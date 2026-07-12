"""
FraudLens AI — Network & Visualization Layer
Step 4: detect_communities()

Groups accounts into "communities" — clusters that transact with each other
much more than with the rest of the network. This is different from the
cycle detector (Kavya's job) and from centrality (previous step):

- Cycle detection finds a specific closed loop (A -> B -> C -> A)
- Centrality finds individually important accounts
- Community detection finds GROUPS that are unusually tightly-knit as a
  whole, even if no single account looks suspicious on its own. This is
  useful for spotting things like a laundering ring where money moves
  around within a group of accounts more than it moves in or out.

We use the Louvain method (networkx.algorithms.community.louvain_communities),
which is a standard, well-tested algorithm for this. Community detection
algorithms work on undirected graphs, so we convert first (fraud direction
still matters elsewhere in the pipeline — this step is purely about
"who clusters with whom").
"""

import networkx as nx
from graph_builder import build_transaction_graph


def detect_communities(graph, min_size=2):
    """
    Cluster the transaction graph into communities using the Louvain method.

    Parameters
    ----------
    graph : networkx.DiGraph
        A transaction graph, as produced by build_transaction_graph().
    min_size : int
        Ignore communities smaller than this (a "community" of 1-2 barely
        connected accounts usually isn't interesting to report on).

    Returns
    -------
    list of dict
        Each dict has:
            "community_id" -> int, arbitrary label for the group
            "accounts"      -> list of account IDs in this community
            "size"          -> number of accounts in the community
            "density"       -> float 0-1, how tightly connected the
                                community is internally (1.0 = every
                                possible pair transacts directly with
                                each other; low = loosely connected)
        Sorted by density (most tightly-knit first), so the most
        "unusually tightly connected" clusters surface at the top.
    """
    if graph.number_of_nodes() == 0:
        return []

    # community detection works on undirected graphs; keep edge weights
    # so stronger (higher-amount / more frequent) links count more
    undirected = graph.to_undirected()

    raw_communities = nx.algorithms.community.louvain_communities(
        undirected, weight="weight", seed=42
    )

    results = []
    for i, community in enumerate(raw_communities):
        accounts = sorted(community)
        size = len(accounts)

        if size < min_size:
            continue

        subgraph = undirected.subgraph(accounts)
        density = nx.density(subgraph)

        results.append({
            "community_id": i,
            "accounts": accounts,
            "size": size,
            "density": round(density, 3),
        })

    # most tightly-knit communities first — these are the ones worth a
    # sentence like "this cluster of 8 accounts is unusually tightly connected"
    results.sort(key=lambda c: c["density"], reverse=True)

    return results


if __name__ == "__main__":
    # Reuse the earlier cycle + hub accounts, and add a tightly-knit group
    # of 8 accounts that all transact with each other frequently — this is
    # the "unusually tightly connected cluster" we want the function to surface.
    sample_transactions = [
        {"sender": "ACC101", "receiver": "ACC456", "amount": 250000, "timestamp": "2026-07-01T10:05:00"},
        {"sender": "ACC456", "receiver": "ACC789", "amount": 237500, "timestamp": "2026-07-01T10:12:00"},
        {"sender": "ACC789", "receiver": "ACC101", "amount": 230000, "timestamp": "2026-07-01T10:19:00"},

        {"sender": "ACC202", "receiver": "ACC303", "amount": 5000, "timestamp": "2026-07-01T09:00:00"},
        {"sender": "ACC202", "receiver": "ACC303", "amount": 1200, "timestamp": "2026-07-02T09:00:00"},

        {"sender": "ACC001", "receiver": "ACC999", "amount": 3000, "timestamp": "2026-07-01T08:00:00"},
        {"sender": "ACC002", "receiver": "ACC999", "amount": 4000, "timestamp": "2026-07-01T08:05:00"},
        {"sender": "ACC003", "receiver": "ACC999", "amount": 2500, "timestamp": "2026-07-01T08:10:00"},
        {"sender": "ACC004", "receiver": "ACC999", "amount": 5000, "timestamp": "2026-07-01T08:15:00"},
    ]

    # add a densely-connected ring of 8 accounts (CLU1..CLU8), each sending
    # to several others in the group, to simulate a suspicious tight cluster
    cluster_accounts = [f"CLU{i}" for i in range(1, 9)]
    for i, sender in enumerate(cluster_accounts):
        # each account sends to the next 3 accounts in the group (wrapping around)
        for offset in (1, 2, 3):
            receiver = cluster_accounts[(i + offset) % len(cluster_accounts)]
            sample_transactions.append({
                "sender": sender,
                "receiver": receiver,
                "amount": 15000,
                "timestamp": "2026-07-03T12:00:00",
            })

    graph = build_transaction_graph(sample_transactions)
    communities = detect_communities(graph, min_size=2)

    print("Detected communities (most tightly-knit first):\n")
    for c in communities:
        print(f"Community {c['community_id']} | size: {c['size']} | density: {c['density']}")
        print(f"  accounts: {c['accounts']}")
        if c["size"] >= 5 and c["density"] > 0.5:
            print(f"  --> flag: this cluster of {c['size']} accounts is unusually tightly connected")
        print()
