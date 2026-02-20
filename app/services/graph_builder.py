"""
Graph Builder Service
─────────────────────
Converts the validated transaction DataFrame into a NetworkX DiGraph.

Node  = account_id (sender_id ∪ receiver_id)
Edge  = sender → receiver
Edge attributes:
    amount          – float
    timestamp       – datetime
    transaction_id  – str
"""

from __future__ import annotations

import networkx as nx
import pandas as pd


def build_graph(df: pd.DataFrame) -> nx.DiGraph:
    """
    Build a directed, multi-edge-capable graph from a transaction DataFrame.

    We use a plain DiGraph (not MultiDiGraph) but store all transactions on an
    edge as a list under the "transactions" attribute so the graph stays sparse
    and traversal is O(V + E).

    Parameters
    ----------
    df : pd.DataFrame
        Output of ``csv_parser.parse_csv``.

    Returns
    -------
    nx.DiGraph
    """
    G = nx.DiGraph()

    # ── Add all account nodes ─────────────────────────────────────────────────
    all_accounts = pd.concat(
        [df["sender_id"], df["receiver_id"]], ignore_index=True
    ).unique()
    G.add_nodes_from(all_accounts)

    # ── Build edge list from vectorised operations ────────────────────────────
    for row in df.itertuples(index=False):
        src, dst = row.sender_id, row.receiver_id
        tx = {
            "transaction_id": row.transaction_id,
            "amount": row.amount,
            "timestamp": row.timestamp,
        }
        if G.has_edge(src, dst):
            G[src][dst]["transactions"].append(tx)
            G[src][dst]["total_amount"] += row.amount
        else:
            G.add_edge(
                src,
                dst,
                transactions=[tx],
                total_amount=row.amount,
            )

    return G


def get_degree_map(G: nx.DiGraph) -> dict[str, int]:
    """
    Return total degree (in + out) for every node.
    Used by multiple detectors so computed once and shared.
    """
    return {node: G.in_degree(node) + G.out_degree(node) for node in G.nodes()}
