"""
FraudLens AI — Network & Visualization Layer
Step 2: find_central_accounts()

Identifies the accounts most "central" to the transaction network using
two centrality measures:

- Degree centrality: how many direct connections (in + out) an account has.
  A high score means the account is a hub — lots of accounts send to or
  receive from it directly.

- Betweenness centrality: how often an account sits on the shortest path
  between other pairs of accounts. A high score means money tends to flow
  THROUGH this account to get from one part of the network to another —
  a classic signature of a "pass-through" or layering account in money
  laundering.

We combine both because they catch different things: a mule account might
have high degree (many small deposits) without high betweenness, while a
layering account in a laundering chain might have high betweenness without
necessarily having many direct connections.
"""

import networkx as nx
from graph_builder import build_transaction_graph


def find_central_accounts(graph, top_n=5):
    """
    Rank accounts by combined degree + betweenness centrality.

    Parameters
    ----------
    graph : networkx.DiGraph
        A transaction graph, as produced by build_transaction_graph().
    top_n : int
        How many top accounts to return.

    Returns
    -------
    list of dict
        Each dict has:
            "account"      -> account id
            "degree_score"       -> normalized degree centrality (0-1)
            "betweenness_score"  -> normalized betweenness centrality (0-1)
            "combined_score"     -> average of the two, used for ranking
        Sorted by combined_score, highest first.
    """
    if graph.number_of_nodes() == 0:
        return []

    # networkx centrality functions work on the graph as-is; for degree
    # centrality on a DiGraph this accounts for both in- and out-edges
    degree_scores = nx.degree_centrality(graph)

    # betweenness centrality on a directed graph considers directed shortest
    # paths, which is exactly what we want (money flows one direction)
    betweenness_scores = nx.betweenness_centrality(graph, weight="weight")

    results = []
    for account in graph.nodes():
        d_score = degree_scores.get(account, 0.0)
        b_score = betweenness_scores.get(account, 0.0)
        combined = (d_score + b_score) / 2

        results.append({
            "account": account,
            "degree_score": round(d_score, 4),
            "betweenness_score": round(b_score, 4),
            "combined_score": round(combined, 4),
        })

    results.sort(key=lambda x: x["combined_score"], reverse=True)

    return results[:top_n]


if __name__ == "__main__":
    # Same sample as before, but with an extra hub account added so we can
    # see degree and betweenness pull apart a bit:
    # - ACC101/456/789 form the laundering cycle (should score high on both)
    # - ACC999 is a hub that many small accounts pay into (high degree,
    #   low betweenness, since money doesn't flow further THROUGH it)
    sample_transactions = [
        {"sender": "ACC101", "receiver": "ACC456", "amount": 250000, "timestamp": "2026-07-01T10:05:00"},
        {"sender": "ACC456", "receiver": "ACC789", "amount": 237500, "timestamp": "2026-07-01T10:12:00"},
        {"sender": "ACC789", "receiver": "ACC101", "amount": 230000, "timestamp": "2026-07-01T10:19:00"},

        {"sender": "ACC202", "receiver": "ACC303", "amount": 5000, "timestamp": "2026-07-01T09:00:00"},
        {"sender": "ACC202", "receiver": "ACC303", "amount": 1200, "timestamp": "2026-07-02T09:00:00"},

        # a hub account that many separate accounts pay into directly
        {"sender": "ACC001", "receiver": "ACC999", "amount": 3000, "timestamp": "2026-07-01T08:00:00"},
        {"sender": "ACC002", "receiver": "ACC999", "amount": 4000, "timestamp": "2026-07-01T08:05:00"},
        {"sender": "ACC003", "receiver": "ACC999", "amount": 2500, "timestamp": "2026-07-01T08:10:00"},
        {"sender": "ACC004", "receiver": "ACC999", "amount": 5000, "timestamp": "2026-07-01T08:15:00"},
    ]

    graph = build_transaction_graph(sample_transactions)
    top_accounts = find_central_accounts(graph, top_n=5)

    print("Top central accounts (most worth investigating first):\n")
    for rank, acc in enumerate(top_accounts, start=1):
        print(f"{rank}. {acc['account']} | combined: {acc['combined_score']} "
              f"| degree: {acc['degree_score']} | betweenness: {acc['betweenness_score']}")