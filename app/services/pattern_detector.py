"""
Pattern Detector Service
────────────────────────
Core algorithm layer – detects three classes of financial crime patterns:

1. Cycle Detection        – circular fund routing (rings of length 3–5)
2. Smurfing Detection     – fan-in / fan-out within a 72-hour window
3. Layered Shell Network  – ≥3-hop chains through low-degree intermediary nodes

Each detector returns a list of RawRing dicts that the scoring engine
and JSON formatter consume.

RawRing schema
──────────────
{
    "ring_id"         : str               e.g. "RING_001"
    "member_accounts" : list[str]
    "pattern_type"    : str               "cycle" | "smurfing" | "layered_shell" | "hybrid"
    "patterns_by_account": dict[str, list[str]]   per-account pattern labels
}
"""

from __future__ import annotations

import itertools
from collections import defaultdict
from datetime import timedelta
from typing import Any

import networkx as nx
import pandas as pd

from app.core.config import (
    MAX_CYCLE_LENGTH,
    MIN_CYCLE_LENGTH,
    RING_ID_PREFIX,
    SHELL_MAX_DEGREE,
    SHELL_MAX_HOPS,
    SHELL_MIN_HOPS,
    SMURFING_MIN_ENDPOINTS,
    SMURFING_WINDOW_HOURS,
)


# ══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ══════════════════════════════════════════════════════════════════════════════

def _next_ring_id(counter: list[int]) -> str:
    counter[0] += 1
    return f"{RING_ID_PREFIX}_{counter[0]:03d}"


# ══════════════════════════════════════════════════════════════════════════════
# 1. CYCLE DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def detect_cycles(
    G: nx.DiGraph,
    ring_counter: list[int],
) -> list[dict[str, Any]]:
    """
    Find simple directed cycles of length MIN_CYCLE_LENGTH..MAX_CYCLE_LENGTH.

    Strategy
    --------
    networkx.simple_cycles() uses Johnson's algorithm (O(V + E) · (V + E + C)
    where C = number of circuits).  We filter by length immediately to avoid
    storing large intermediate structures.

    Returns
    -------
    List of RawRing dicts.
    """
    rings: list[dict[str, Any]] = []
    seen_cycle_sets: set[frozenset] = set()

    for cycle in nx.simple_cycles(G):
        length = len(cycle)
        if not (MIN_CYCLE_LENGTH <= length <= MAX_CYCLE_LENGTH):
            continue

        key = frozenset(cycle)
        if key in seen_cycle_sets:
            continue
        seen_cycle_sets.add(key)

        pattern_label = f"cycle_length_{length}"
        ring_id = _next_ring_id(ring_counter)

        patterns_by_account: dict[str, list[str]] = {
            acc: [pattern_label] for acc in cycle
        }

        rings.append(
            {
                "ring_id": ring_id,
                "member_accounts": list(cycle),
                "pattern_type": "cycle",
                "patterns_by_account": patterns_by_account,
            }
        )

    return rings


# ══════════════════════════════════════════════════════════════════════════════
# 2. SMURFING DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def detect_smurfing(
    df: pd.DataFrame,
    ring_counter: list[int],
) -> list[dict[str, Any]]:
    """
    Detect fan-in (many → one) and fan-out (one → many) within a 72-hour window.

    Algorithm (O(n log n))
    ─────────────────────
    Sort transactions by (receiver_id, timestamp) for fan-in, then sweep a
    sliding window.  Repeat for (sender_id, timestamp) for fan-out.
    """
    rings: list[dict[str, Any]] = []
    window = timedelta(hours=SMURFING_WINDOW_HOURS)

    # ── Fan-in: many senders → one receiver ──────────────────────────────────
    fan_in_rings = _sliding_window_smurfing(
        df,
        focus_col="receiver_id",
        partner_col="sender_id",
        pattern_label="fan_in_smurfing",
        pattern_type="smurfing",
        ring_counter=ring_counter,
        window=window,
    )
    rings.extend(fan_in_rings)

    # ── Fan-out: one sender → many receivers ─────────────────────────────────
    fan_out_rings = _sliding_window_smurfing(
        df,
        focus_col="sender_id",
        partner_col="receiver_id",
        pattern_label="fan_out_smurfing",
        pattern_type="smurfing",
        ring_counter=ring_counter,
        window=window,
    )
    rings.extend(fan_out_rings)

    return rings


def _sliding_window_smurfing(
    df: pd.DataFrame,
    focus_col: str,
    partner_col: str,
    pattern_label: str,
    pattern_type: str,
    ring_counter: list[int],
    window: timedelta,
) -> list[dict[str, Any]]:
    """
    Sliding-window scan per focus account.
    For each focus account, we walk its sorted timestamps and expand a window
    of size `window`.  If ≥ SMURFING_MIN_ENDPOINTS unique partners are found in
    that window, it's flagged.
    """
    rings: list[dict[str, Any]] = []
    already_flagged: set[frozenset] = set()

    # Group by focus account and sort by time — vectorised via Pandas groupby
    for focus_id, group in df.groupby(focus_col):
        group = group.sort_values("timestamp")
        timestamps = group["timestamp"].to_numpy()
        partners = group[partner_col].to_numpy()
        n = len(timestamps)

        left = 0
        # Two-pointer sliding window
        for right in range(n):
            # Shrink window from left
            while (timestamps[right] - timestamps[left]) > window:
                left += 1

            # Partners in current window
            window_partners = set(partners[left : right + 1])
            if len(window_partners) >= SMURFING_MIN_ENDPOINTS:
                key = frozenset(window_partners | {focus_id})
                if key in already_flagged:
                    continue
                already_flagged.add(key)

                members = [focus_id] + list(window_partners)
                patterns_by_account: dict[str, list[str]] = {
                    acc: [pattern_label] for acc in members
                }
                ring_id = _next_ring_id(ring_counter)
                rings.append(
                    {
                        "ring_id": ring_id,
                        "member_accounts": members,
                        "pattern_type": pattern_type,
                        "patterns_by_account": patterns_by_account,
                    }
                )

    return rings


# ══════════════════════════════════════════════════════════════════════════════
# 3. LAYERED SHELL NETWORK DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def detect_layered_shells(
    G: nx.DiGraph,
    degree_map: dict[str, int],
    ring_counter: list[int],
) -> list[dict[str, Any]]:
    """
    Detect transaction chains ≥ SHELL_MIN_HOPS hops where intermediate nodes
    are low-degree (degree ≤ SHELL_MAX_DEGREE).

    Algorithm
    ---------
    For each node with out-degree > 0, run a DFS up to SHELL_MAX_HOPS deep.
    Collect paths where:
        – length ≥ SHELL_MIN_HOPS
        – all intermediate nodes have degree ≤ SHELL_MAX_DEGREE

    We deduplicate by member set (frozenset) to avoid re-flagging same group.
    """
    rings: list[dict[str, Any]] = []
    seen_member_sets: set[frozenset] = set()

    # Only start DFS from nodes that could be chain heads (have successors)
    candidate_sources = [
        n for n in G.nodes() if G.out_degree(n) > 0
    ]

    for source in candidate_sources:
        # DFS stack: (current_path, visited_in_path)
        stack: list[tuple[list[str], set[str]]] = [([source], {source})]

        while stack:
            path, visited = stack.pop()
            current = path[-1]

            if len(path) > SHELL_MAX_HOPS + 1:
                continue

            # Evaluate path as a chain if it meets minimum length
            if len(path) >= SHELL_MIN_HOPS + 1:
                # Check intermediate nodes are low-degree
                intermediates = path[1:-1]
                if all(degree_map.get(n, 0) <= SHELL_MAX_DEGREE for n in intermediates):
                    member_set = frozenset(path)
                    if member_set not in seen_member_sets:
                        seen_member_sets.add(member_set)

                        patterns_by_account: dict[str, list[str]] = {
                            acc: ["layered_shell_chain"] for acc in path
                        }
                        ring_id = _next_ring_id(ring_counter)
                        rings.append(
                            {
                                "ring_id": ring_id,
                                "member_accounts": list(path),
                                "pattern_type": "layered_shell",
                                "patterns_by_account": patterns_by_account,
                            }
                        )

            # Expand DFS into successors (not already in path)
            if len(path) <= SHELL_MAX_HOPS:
                for successor in G.successors(current):
                    if successor not in visited:
                        stack.append((path + [successor], visited | {successor}))

    return rings


# ══════════════════════════════════════════════════════════════════════════════
# Public entry point
# ══════════════════════════════════════════════════════════════════════════════

def run_all_detectors(
    G: nx.DiGraph,
    df: pd.DataFrame,
    degree_map: dict[str, int],
) -> list[dict[str, Any]]:
    """
    Execute all three detectors in sequence, sharing a single ring counter
    so ring IDs are globally unique across all detection passes.
    """
    ring_counter: list[int] = [0]   # mutable counter passed by reference

    all_rings: list[dict[str, Any]] = []

    cycle_rings  = detect_cycles(G, ring_counter)
    all_rings.extend(cycle_rings)

    smurf_rings  = detect_smurfing(df, ring_counter)
    all_rings.extend(smurf_rings)

    shell_rings  = detect_layered_shells(G, degree_map, ring_counter)
    all_rings.extend(shell_rings)

    return all_rings
