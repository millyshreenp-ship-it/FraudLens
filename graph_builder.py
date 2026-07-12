"""
FraudLens AI — Network & Visualization Layer
Step 1: build_transaction_graph()

Turns a list of transactions into a NetworkX directed graph:
- Nodes = accounts
- Edges = transfers (with total amount, transaction count, and the raw
  list of individual transactions so we can inspect/highlight later)
"""

import networkx as nx
from datetime import datetime


def build_transaction_graph(transactions):
    """
    Build a directed transaction graph from a list of transactions.

    Parameters
    ----------
    transactions : list of dict
        Each dict should have at least:
            "sender": str        e.g. "ACC101"
            "receiver": str      e.g. "ACC456"
            "amount": float      e.g. 250000
            "timestamp": str or datetime   e.g. "2026-07-01 10:05:00"
        Optional:
            "txn_type": str      e.g. "TRANSFER", "CASH_OUT"

    Returns
    -------
    networkx.DiGraph
        A directed graph where:
        - each node is an account, with attribute "total_received" and
          "total_sent" (running totals, useful later for mule-account checks)
        - each edge (sender -> receiver) has attributes:
            "weight"       -> total amount transferred sender->receiver
            "count"        -> number of transactions on this edge
            "transactions" -> list of the raw transaction dicts for this edge
    """
    G = nx.DiGraph()

    for txn in transactions:
        sender = txn["sender"]
        receiver = txn["receiver"]
        amount = float(txn["amount"])
        timestamp = txn["timestamp"]

        # normalize timestamp to a datetime object if it's a string
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # make sure both accounts exist as nodes, even before any edge is added
        if sender not in G:
            G.add_node(sender, total_sent=0.0, total_received=0.0)
        if receiver not in G:
            G.add_node(receiver, total_sent=0.0, total_received=0.0)

        # update running totals on the nodes
        G.nodes[sender]["total_sent"] += amount
        G.nodes[receiver]["total_received"] += amount

        if G.has_edge(sender, receiver):
            # already a transfer relationship between these two accounts —
            # aggregate instead of overwriting
            G[sender][receiver]["weight"] += amount
            G[sender][receiver]["count"] += 1
            G[sender][receiver]["transactions"].append(txn)
        else:
            G.add_edge(
                sender,
                receiver,
                weight=amount,
                count=1,
                transactions=[txn],
            )

    return G


if __name__ == "__main__":
    # --- quick manual test with a small sample that includes a 3-hop cycle ---
    sample_transactions = [
        {"sender": "ACC101", "receiver": "ACC456", "amount": 250000, "timestamp": "2026-07-01T10:05:00"},
        {"sender": "ACC456", "receiver": "ACC789", "amount": 237500, "timestamp": "2026-07-01T10:12:00"},
        {"sender": "ACC789", "receiver": "ACC101", "amount": 230000, "timestamp": "2026-07-01T10:19:00"},
        # some normal, unrelated activity mixed in
        {"sender": "ACC202", "receiver": "ACC303", "amount": 5000, "timestamp": "2026-07-01T09:00:00"},
        {"sender": "ACC202", "receiver": "ACC303", "amount": 1200, "timestamp": "2026-07-02T09:00:00"},
    ]

    graph = build_transaction_graph(sample_transactions)

    print(f"Nodes (accounts): {list(graph.nodes())}")
    print(f"Number of accounts: {graph.number_of_nodes()}")
    print(f"Number of edges (transfer relationships): {graph.number_of_edges()}\n")

    print("Edge details:")
    for sender, receiver, data in graph.edges(data=True):
        print(f"  {sender} -> {receiver} | total: {data['weight']:.0f} | count: {data['count']}")

    print("\nNode totals (sanity check):")
    for node, data in graph.nodes(data=True):
        print(f"  {node} | sent: {data['total_sent']:.0f} | received: {data['total_received']:.0f}")