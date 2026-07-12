"""
FraudLens AI — Network & Visualization Layer
Step 5: plot_fraud_heatmap()

Aggregates FLAGGED transactions by location and renders a color-scaled bar
chart (a "heatmap-by-region" — darker/taller bars = more fraud activity
in that region).

IMPORTANT: PaySim does not include location data. This function expects
each transaction dict to already have a "location" field (e.g. city or
state) attached. If your dataset doesn't have real locations, this needs
synthetic location data added first (e.g. randomly assigning a state to
each account) — note this as a known limitation in your report, since a
synthetic location has no real fraud-geography meaning.
"""

import pandas as pd
import plotly.express as px
from graph_builder import build_transaction_graph  # not used directly here, kept for consistency with the rest of the module


def plot_fraud_heatmap(transactions_with_location, location_field="location", flagged_field="is_flagged"):
    """
    Aggregate flagged transactions by region and plot a color-scaled bar chart.

    Parameters
    ----------
    transactions_with_location : list of dict
        Each dict must have at least:
            "amount"                -> float
            location_field (default "location")  -> e.g. "Maharashtra"
            flagged_field (default "is_flagged")  -> bool, whether this
                transaction was flagged by the fraud detector
    location_field : str
        Which key in each transaction dict holds the region/location.
    flagged_field : str
        Which key in each transaction dict holds the flagged boolean.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    if not transactions_with_location:
        fig = px.bar(title="No transaction data to display")
        return fig

    df = pd.DataFrame(transactions_with_location)

    if location_field not in df.columns or flagged_field not in df.columns:
        raise ValueError(
            f"Each transaction needs '{location_field}' and '{flagged_field}' fields. "
            f"Got columns: {list(df.columns)}"
        )

    flagged_df = df[df[flagged_field] == True]

    if flagged_df.empty:
        fig = px.bar(title="No flagged transactions to display")
        return fig

    # aggregate: count of flagged transactions + total flagged amount, per region
    region_summary = (
        flagged_df.groupby(location_field)
        .agg(flagged_count=("amount", "count"), flagged_amount=("amount", "sum"))
        .reset_index()
        .sort_values("flagged_count", ascending=False)
    )

    fig = px.bar(
        region_summary,
        x=location_field,
        y="flagged_count",
        color="flagged_count",
        color_continuous_scale="Reds",
        hover_data={"flagged_amount": ":,.0f"},
        labels={
            location_field: "Region",
            "flagged_count": "Flagged transactions",
            "flagged_amount": "Total flagged amount",
        },
        title="Flagged Transactions by Region",
    )
    fig.update_layout(coloraxis_colorbar=dict(title="Flagged count"))

    return fig


if __name__ == "__main__":
    # synthetic sample: locations attached manually since PaySim has none
    sample_transactions = [
        {"sender": "ACC101", "receiver": "ACC456", "amount": 250000, "location": "Maharashtra", "is_flagged": True},
        {"sender": "ACC456", "receiver": "ACC789", "amount": 237500, "location": "Maharashtra", "is_flagged": True},
        {"sender": "ACC789", "receiver": "ACC101", "amount": 230000, "location": "Maharashtra", "is_flagged": True},

        {"sender": "ACC202", "receiver": "ACC303", "amount": 5000, "location": "Delhi", "is_flagged": False},
        {"sender": "ACC202", "receiver": "ACC303", "amount": 1200, "location": "Delhi", "is_flagged": False},

        {"sender": "ACC001", "receiver": "ACC999", "amount": 3000, "location": "Karnataka", "is_flagged": True},
        {"sender": "ACC002", "receiver": "ACC999", "amount": 4000, "location": "Karnataka", "is_flagged": True},
        {"sender": "ACC003", "receiver": "ACC999", "amount": 2500, "location": "Uttar Pradesh", "is_flagged": True},
        {"sender": "ACC004", "receiver": "ACC999", "amount": 5000, "location": "Uttar Pradesh", "is_flagged": False},
    ]

    fig = plot_fraud_heatmap(sample_transactions)
    fig.write_html("fraud_heatmap_preview.html")
    print("Saved fraud_heatmap_preview.html — open it in a browser to check the chart")

    # quick printed sanity check of what got aggregated
    df = pd.DataFrame(sample_transactions)
    flagged = df[df["is_flagged"] == True]
    print("\nFlagged transactions by region:")
    print(flagged.groupby("location")["amount"].agg(["count", "sum"]))
