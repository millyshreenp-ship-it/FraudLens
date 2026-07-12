"""
FraudLens AI — Network & Visualization Layer
Step 3: plot_transaction_network()

Renders the transaction graph with Plotly:
- Nodes = accounts, sized by how "central" they are (degree + betweenness)
- Edges = transfers, drawn as lines
- If a suspicious cycle is passed in (e.g. the accounts in a detected
  money-laundering ring), those specific edges are drawn thicker and in a
  different color so they visually pop out of the rest of the network.
"""

import networkx as nx
import plotly.graph_objects as go
from graph_builder import build_transaction_graph


def plot_transaction_network(graph, highlight_cycle=None):
    """
    Draw the transaction network with Plotly.

    Parameters
    ----------
    graph : networkx.DiGraph
        A transaction graph, as produced by build_transaction_graph().
    highlight_cycle : list of str, optional
        A list of account IDs forming a suspicious cycle, e.g.
        ["ACC101", "ACC456", "ACC789"]. The edges connecting these
        accounts in order (including wrapping the last one back to the
        first) will be drawn thicker and in a highlight color.

    Returns
    -------
    plotly.graph_objects.Figure
        Ready to call .show() on, or embed in Streamlit with st.plotly_chart().
    """
    if graph.number_of_nodes() == 0:
        # return an empty, clearly-labeled figure rather than crashing
        fig = go.Figure()
        fig.update_layout(title="No transactions to display")
        return fig

    # --- 1. compute a layout (x, y position for every node) ---
    pos = nx.spring_layout(graph, seed=42, weight="weight")

    # --- 2. compute centrality scores to size nodes by ---
    degree_scores = nx.degree_centrality(graph)
    betweenness_scores = nx.betweenness_centrality(graph, weight="weight")

    # --- 3. figure out which edges are part of the highlighted cycle ---
    highlighted_edges = set()
    if highlight_cycle:
        for i in range(len(highlight_cycle)):
            a = highlight_cycle[i]
            b = highlight_cycle[(i + 1) % len(highlight_cycle)]  # wraps last -> first
            highlighted_edges.add((a, b))

    # --- 4. build edge traces (normal edges vs highlighted edges) ---
    normal_edge_x, normal_edge_y = [], []
    highlight_edge_x, highlight_edge_y = [], []

    for sender, receiver in graph.edges():
        x0, y0 = pos[sender]
        x1, y1 = pos[receiver]

        if (sender, receiver) in highlighted_edges:
            highlight_edge_x += [x0, x1, None]
            highlight_edge_y += [y0, y1, None]
        else:
            normal_edge_x += [x0, x1, None]
            normal_edge_y += [y0, y1, None]

    normal_edge_trace = go.Scatter(
        x=normal_edge_x, y=normal_edge_y,
        line=dict(width=1, color="#b0b0b0"),
        hoverinfo="none",
        mode="lines",
        name="Transfers",
    )

    highlight_edge_trace = go.Scatter(
        x=highlight_edge_x, y=highlight_edge_y,
        line=dict(width=4, color="#e63946"),
        hoverinfo="none",
        mode="lines",
        name="Flagged cycle",
    )

    # --- 5. build the node trace, sized and colored by combined centrality ---
    node_x, node_y, node_text, node_size, node_color = [], [], [], [], []

    for account in graph.nodes():
        x, y = pos[account]
        node_x.append(x)
        node_y.append(y)

        d_score = degree_scores.get(account, 0.0)
        b_score = betweenness_scores.get(account, 0.0)
        combined = (d_score + b_score) / 2

        # scale so nodes are visibly different but nothing disappears/explodes
        node_size.append(15 + combined * 150)

        is_flagged = highlight_cycle and account in highlight_cycle
        node_color.append("#e63946" if is_flagged else "#457b9d")

        sent = graph.nodes[account]["total_sent"]
        received = graph.nodes[account]["total_received"]
        node_text.append(
            f"{account}<br>"
            f"Sent: {sent:,.0f}<br>"
            f"Received: {received:,.0f}<br>"
            f"Degree centrality: {d_score:.3f}<br>"
            f"Betweenness centrality: {b_score:.3f}"
        )

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=[acc for acc in graph.nodes()],
        textposition="top center",
        hovertext=node_text,
        hoverinfo="text",
        marker=dict(size=node_size, color=node_color, line=dict(width=1, color="#1d3557")),
        name="Accounts",
    )

    # --- 6. assemble the figure ---
    fig = go.Figure(
        data=[normal_edge_trace, highlight_edge_trace, node_trace],
        layout=go.Layout(
            title="FraudLens AI — Transaction Network",
            showlegend=True,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="white",
        ),
    )

    return fig


if __name__ == "__main__":
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

    graph = build_transaction_graph(sample_transactions)

    # highlight the known laundering cycle
    fig = plot_transaction_network(graph, highlight_cycle=["ACC101", "ACC456", "ACC789"])

    fig.write_html("network_preview.html")
    print("Saved network_preview.html — open it in a browser to check the plot")
