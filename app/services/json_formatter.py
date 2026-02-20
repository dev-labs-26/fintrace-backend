"""
JSON Formatter Service
──────────────────────
Converts raw engine outputs into Pydantic-validated AnalysisResponse objects
that match the exact Fintrace JSON schema.
"""

from __future__ import annotations

from typing import Any

import networkx as nx
import pandas as pd

from app.models.schemas import AnalysisResponse, FraudRing, Summary, SuspiciousAccount, Transaction


def build_response(
    all_rings: list[dict[str, Any]],
    score_map: dict[str, float],
    pattern_map: dict[str, list[str]],
    account_ring_map: dict[str, str],
    G: nx.DiGraph,
    processing_time: float,
    df: pd.DataFrame | None = None,
) -> AnalysisResponse:
    """
    Assemble the final AnalysisResponse.

    Parameters
    ----------
    all_rings         : Enriched rings (with risk_score populated by scoring_engine).
    score_map         : account_id → suspicion_score
    pattern_map       : account_id → [pattern_label, ...]
    account_ring_map  : account_id → first ring_id the account belongs to
    G                 : The full transaction DiGraph (to count total accounts)
    processing_time   : Wall-clock seconds for the full analysis pipeline
    df                : Original transaction DataFrame (optional, for timeline data)
    """

    # ── Suspicious accounts (sorted descending by score) ─────────────────────
    suspicious_accounts: list[SuspiciousAccount] = []
    for acct, score in sorted(score_map.items(), key=lambda x: -x[1]):
        suspicious_accounts.append(
            SuspiciousAccount(
                account_id=acct,
                suspicion_score=score,
                detected_patterns=pattern_map.get(acct, []),
                ring_id=account_ring_map.get(acct),
            )
        )

    # ── Fraud rings ───────────────────────────────────────────────────────────
    fraud_rings: list[FraudRing] = []

    # Deduplicate rings by member set across all detection passes
    seen_ring_members: set[frozenset] = set()
    for ring in all_rings:
        member_set = frozenset(ring["member_accounts"])
        if member_set in seen_ring_members:
            continue
        seen_ring_members.add(member_set)

        fraud_rings.append(
            FraudRing(
                ring_id=ring["ring_id"],
                member_accounts=ring["member_accounts"],
                pattern_type=ring["pattern_type"],
                risk_score=ring.get("risk_score", 0.0),
                member_count=len(ring["member_accounts"]),
            )
        )

    # ── Summary ───────────────────────────────────────────────────────────────
    summary = Summary(
        total_accounts_analyzed=G.number_of_nodes(),
        suspicious_accounts_flagged=len(suspicious_accounts),
        fraud_rings_detected=len(fraud_rings),
        processing_time_seconds=processing_time,
    )

    # ── Transactions (for timeline visualization) ────────────────────────────
    transactions: list[Transaction] = []
    if df is not None:
        # Include all transactions for timeline playback
        for _, row in df.iterrows():
            transactions.append(
                Transaction(
                    transaction_id=str(row.get("transaction_id", "")),
                    sender_id=str(row.get("sender_id", "")),
                    receiver_id=str(row.get("receiver_id", "")),
                    amount=float(row.get("amount", 0.0)),
                    timestamp=str(row.get("timestamp", "")),
                )
            )

    return AnalysisResponse(
        suspicious_accounts=suspicious_accounts,
        fraud_rings=fraud_rings,
        summary=summary,
        transactions=transactions,
    )
