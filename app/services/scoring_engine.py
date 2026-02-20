"""
Scoring Engine Service
──────────────────────
Assigns a suspicion score (0–100 float) to every account that was touched
by at least one fraud pattern, then populates each RawRing's risk_score field.

Weighted scoring model
──────────────────────
  +40   cycle participation
  +30   fan-in or fan-out smurfing
  +20   high-velocity burst (≥10 TX within 24 h)
  +25   layered shell chain involvement
  +10   degree-centrality anomaly (top-5 % by in-degree)
  -25   likely legitimate merchant pattern (false-positive reduction)

Score is clamped to [0, 100] and rounded to 1 decimal place.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import networkx as nx
from collections import defaultdict
from typing import Any

from app.core.config import (
    MERCHANT_AMOUNT_CV_THRESHOLD,
    MERCHANT_MIN_LIFETIME_DAYS,
    MERCHANT_SPACING_CV_THRESHOLD,
    SCORE_CENTRALITY,
    SCORE_CYCLE,
    SCORE_FP_MERCHANT,
    SCORE_MAX,
    SCORE_MIN,
    SCORE_SHELL,
    SCORE_SMURFING,
    SCORE_VELOCITY,
    VELOCITY_MIN_TX,
    VELOCITY_WINDOW_HOURS,
)


# ══════════════════════════════════════════════════════════════════════════════
# Velocity burst detection (per account)
# ══════════════════════════════════════════════════════════════════════════════

def _burst_accounts(df: pd.DataFrame) -> set[str]:
    """
    Return set of accounts (sender OR receiver) with ≥ VELOCITY_MIN_TX
    transactions within any VELOCITY_WINDOW_HOURS window.

    Uses a sorted sliding-window – O(n log n).
    """
    from datetime import timedelta
    window = timedelta(hours=VELOCITY_WINDOW_HOURS)
    burst_set: set[str] = set()

    for col in ("sender_id", "receiver_id"):
        for acct, grp in df.groupby(col):
            ts = grp["timestamp"].sort_values().reset_index(drop=True)
            n = len(ts)
            left = 0
            for right in range(n):
                while (ts[right] - ts[left]) > window:
                    left += 1
                if (right - left + 1) >= VELOCITY_MIN_TX:
                    burst_set.add(acct)
                    break   # already flagged, skip rest of this account

    return burst_set


# ══════════════════════════════════════════════════════════════════════════════
# Degree-centrality anomaly
# ══════════════════════════════════════════════════════════════════════════════

def _centrality_anomaly_accounts(G: nx.DiGraph) -> set[str]:
    """
    Flag accounts in the top 5 % by in-degree centrality (excluding isolated nodes).
    """
    in_degrees = dict(G.in_degree())
    if not in_degrees:
        return set()

    values = sorted(in_degrees.values(), reverse=True)
    threshold_idx = max(1, int(len(values) * 0.05))
    threshold = values[threshold_idx - 1]

    return {n for n, d in in_degrees.items() if d >= threshold and d > 0}


# ══════════════════════════════════════════════════════════════════════════════
# False-positive merchant heuristic
# ══════════════════════════════════════════════════════════════════════════════

def _merchant_like_accounts(df: pd.DataFrame) -> set[str]:
    """
    Accounts that look like legitimate high-volume businesses:
      1. Active for ≥ MERCHANT_MIN_LIFETIME_DAYS days
      2. Transaction amounts have low coefficient of variation
         (CV ≤ MERCHANT_AMOUNT_CV_THRESHOLD → consistent amounts)
      3. Inter-arrival times have low CV
         (CV ≤ MERCHANT_SPACING_CV_THRESHOLD → evenly spaced)
    """
    merchants: set[str] = set()
    min_days = pd.Timedelta(days=MERCHANT_MIN_LIFETIME_DAYS)

    # Combine sender AND receiver activity
    for col in ("sender_id", "receiver_id"):
        for acct, grp in df.groupby(col):
            ts   = grp["timestamp"].sort_values().reset_index(drop=True)
            amts = grp["amount"].values

            # Lifetime check
            if (ts.iloc[-1] - ts.iloc[0]) < min_days:
                continue

            # Amount CV check
            if amts.std() == 0 or amts.mean() == 0:
                amt_cv = 0.0
            else:
                amt_cv = amts.std() / amts.mean()

            if amt_cv > MERCHANT_AMOUNT_CV_THRESHOLD:
                continue

            # Inter-arrival time CV check (need ≥2 transactions)
            if len(ts) < 2:
                continue
            diffs = ts.diff().dropna().dt.total_seconds().values
            if diffs.mean() == 0:
                iat_cv = 0.0
            else:
                iat_cv = diffs.std() / diffs.mean()

            if iat_cv <= MERCHANT_SPACING_CV_THRESHOLD:
                merchants.add(acct)

    return merchants


# ══════════════════════════════════════════════════════════════════════════════
# Public scoring entry point
# ══════════════════════════════════════════════════════════════════════════════

def score_accounts(
    all_rings: list[dict[str, Any]],
    G: nx.DiGraph,
    df: pd.DataFrame,
) -> tuple[dict[str, float], dict[str, list[str]], dict[str, str]]:
    """
    Compute suspicion scores and collate detected patterns per account.

    Returns
    -------
    scores         : dict[account_id → suspicion_score (float)]
    patterns       : dict[account_id → list[pattern_label]]
    account_ring   : dict[account_id → ring_id]   (first ring the account belongs to)
    """
    raw_scores:   dict[str, float]       = defaultdict(float)
    raw_patterns: dict[str, set[str]]    = defaultdict(set)
    account_ring: dict[str, str]         = {}

    # ── Pre-compute auxiliary sets ────────────────────────────────────────────
    burst_accts      = _burst_accounts(df)
    centrality_accts = _centrality_anomaly_accounts(G)
    merchant_accts   = _merchant_like_accounts(df)

    # ── Score contributions from detected rings ────────────────────────────────
    for ring in all_rings:
        ptype = ring["pattern_type"]
        pba   = ring["patterns_by_account"]  # {account_id: [label, ...]}
        rid   = ring["ring_id"]

        # Determine base score delta for this ring's pattern type
        if ptype == "cycle":
            delta = SCORE_CYCLE
        elif ptype == "smurfing":
            delta = SCORE_SMURFING
        elif ptype == "layered_shell":
            delta = SCORE_SHELL
        else:
            delta = max(SCORE_CYCLE, SCORE_SMURFING, SCORE_SHELL)  # hybrid

        for acct, labels in pba.items():
            raw_scores[acct] += delta
            raw_patterns[acct].update(labels)
            if acct not in account_ring:
                account_ring[acct] = rid

    # ── Add auxiliary signal contributions ────────────────────────────────────
    for acct in burst_accts:
        if acct in raw_scores:   # only add to already-suspicious accounts
            raw_scores[acct] += SCORE_VELOCITY
            raw_patterns[acct].add("high_velocity")

    for acct in centrality_accts:
        if acct in raw_scores:
            raw_scores[acct] += SCORE_CENTRALITY
            raw_patterns[acct].add("degree_centrality_anomaly")

    # ── False-positive reduction ──────────────────────────────────────────────
    for acct in merchant_accts:
        if acct in raw_scores:
            raw_scores[acct] += SCORE_FP_MERCHANT   # negative weight
            raw_patterns[acct].add("merchant_pattern_fp_reduction")

    # ── Clamp, round, convert ─────────────────────────────────────────────────
    final_scores: dict[str, float] = {}
    for acct, score in raw_scores.items():
        clamped = min(SCORE_MAX, max(SCORE_MIN, score))
        final_scores[acct] = round(clamped, 1)

    final_patterns: dict[str, list[str]] = {
        acct: sorted(labels) for acct, labels in raw_patterns.items()
    }

    return final_scores, final_patterns, account_ring


def compute_ring_risk_scores(
    all_rings: list[dict[str, Any]],
    score_map: dict[str, float],
) -> list[dict[str, Any]]:
    """
    Attach a risk_score (avg member suspicion score) to every ring dict.
    Returns the enriched rings list.
    """
    for ring in all_rings:
        members = ring["member_accounts"]
        member_scores = [score_map.get(m, 0.0) for m in members]
        avg = sum(member_scores) / len(member_scores) if member_scores else 0.0
        ring["risk_score"] = round(min(100.0, max(0.0, avg)), 1)

    return all_rings
