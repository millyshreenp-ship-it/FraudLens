"""
FraudLens AI — Network & Visualization Layer
Step 6: plot_timeline_replay()

Shows a flagged cycle "playing out" step by step: each step reveals one
more transfer in the order it actually happened, so an investigator can
watch the money move (e.g. A -> B, then B -> C, then C -> A) instead of
just seeing the finished graph all at once.

Built with Plotly frames + a slider (and a Play button), which is the
standard way to do simple step/animated playback in Plotly.
"""

import networkx as nx
import plotly.graph_objects as go
from datetime import datetime


def plot_timeline_replay(cycle_transactions):
    """
    Build a step-through timeline replay of a flagged cycle.

    Parameters
    ----------
    cycle_transactions : list of dict
        The transactions that make up ONE flagged cycle (e.g. the 3
        transactions from a detected A -> B -> C -> A ring). Each dict
        needs: "sender", "receiver", "amount", "timestamp".
        This is meant for a single small flagged cycle, not the whole
        network — use plot_transaction_network() for the full graph.

    Returns
    -------
    plotly.graph_objects.Figure
        A figure with a Play button and a slider — press play or drag
        the slider to watch the cycle unfold one transfer at a time.
    """
    if not cycle_transactions:
        fig = go.Figure()
        fig.update_layout(title="No cycle transactions to replay")
        return fig

    # sort so the replay follows the actual order money moved in
    def get_time(txn):
        ts = txn["timestamp"]
        return datetime.fromisoformat(ts) if isinstance(ts, str) else ts

    ordered = sorted(cycle_transactions, key=get_time)

    # build a small graph just to get consistent node positions —
    # circular layout looks natural for a cycle
    accounts = []
    for txn in ordered:
        if txn["sender"] not in accounts:
            accounts.append(txn["sender"])
        if txn["receiver"] not in accounts:
            accounts.append(txn["receiver"])

    circle_graph = nx.Graph()
    circle_graph.add_nodes_from(accounts)
    pos = nx.circular_layout(circle_graph)

    node_x = [pos[acc][0] for acc in accounts]
    node_y = [pos[acc][1] for acc in accounts]

    # node trace is built ONCE and stays at a fixed trace index in every
    # frame — this is what keeps Plotly from losing track of it
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=accounts,
        textposition="top center",
        textfont=dict(size=13, color="#1d3557"),
        marker=dict(size=24, color="#457b9d", line=dict(width=1.5, color="#1d3557")),
        hoverinfo="text",
        hovertext=accounts,
        showlegend=False,
    )

    def make_frame(step_index):
        """Build one frame with a FIXED number of edge traces (one per
        transaction, always present). Edges not reached yet are made
        invisible; edges already passed are dimmed gray; the current
        edge is bright red. The node trace is always appended last, at
        the same fixed position, in every single frame."""
        edge_traces = []

        for i, txn in enumerate(ordered):
            x0, y0 = pos[txn["sender"]]
            x1, y1 = pos[txn["receiver"]]

            if i < step_index:
                color, width, visible = "#c9c9c9", 2, True   # already happened
            elif i == step_index:
                color, width, visible = "#e63946", 5, True   # happening now
            else:
                color, width, visible = "#c9c9c9", 2, False  # hasn't happened yet

            edge_traces.append(
                go.Scatter(
                    x=[x0, x1], y=[y0, y1],
                    mode="lines+markers",
                    line=dict(width=width, color=color),
                    marker=dict(size=6, color=color),
                    hoverinfo="text",
                    hovertext=f"{txn['sender']} -> {txn['receiver']}<br>Amount: {txn['amount']:,.0f}",
                    visible=visible,
                    showlegend=False,
                )
            )

        current_txn = ordered[step_index]
        step_caption = (
            f"Step {step_index + 1} of {len(ordered)}: "
            f"{current_txn['sender']} sent {current_txn['amount']:,.0f} to {current_txn['receiver']} "
            f"at {current_txn['timestamp']}"
        )

        return edge_traces + [node_trace], step_caption

    # build all frames up front
    frames = []
    slider_steps = []
    for step_index in range(len(ordered)):
        frame_data, caption = make_frame(step_index)
        frames.append(go.Frame(data=frame_data, name=str(step_index), layout=go.Layout(title=caption)))
        slider_steps.append({
            "args": [[str(step_index)], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
            "label": f"Step {step_index + 1}",
            "method": "animate",
        })

    # first frame is the figure's initial state
    initial_data, initial_caption = make_frame(0)

    fig = go.Figure(
        data=initial_data,
        frames=frames,
        layout=go.Layout(
            title=initial_caption,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.3, 1.3]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.3, 1.3]),
            plot_bgcolor="white",
            updatemenus=[{
                "type": "buttons",
                "showactive": False,
                "buttons": [
                    {"label": "Play", "method": "animate",
                     "args": [None, {"frame": {"duration": 900, "redraw": True}, "fromcurrent": True}]},
                    {"label": "Pause", "method": "animate",
                     "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]},
                ],
            }],
            sliders=[{
                "steps": slider_steps,
                "currentvalue": {"prefix": "Viewing: "},
            }],
        ),
    )

    return fig


if __name__ == "__main__":
    # the same 3-hop laundering cycle used in earlier tests
    cycle_transactions = [
        {"sender": "ACC101", "receiver": "ACC456", "amount": 250000, "timestamp": "2026-07-01T10:05:00"},
        {"sender": "ACC456", "receiver": "ACC789", "amount": 237500, "timestamp": "2026-07-01T10:12:00"},
        {"sender": "ACC789", "receiver": "ACC101", "amount": 230000, "timestamp": "2026-07-01T10:19:00"},
    ]

    fig = plot_timeline_replay(cycle_transactions)
    fig.update_layout(width=800, height=600)
    fig.write_html("timeline_replay_preview.html")
    print("Saved timeline_replay_preview.html — open it, then click Play or drag the slider")
