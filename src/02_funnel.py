from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "funnelproject-511023"
TABLE = f"{PROJECT_ID}.funnel_project.session_funnel"

DATA_DIR = Path("data")
FIG_DIR = Path("outputs/figures")
TABLE_DIR = Path("outputs/tables")
for folder in [DATA_DIR, FIG_DIR, TABLE_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

BROWSE_STEPS = [
    ("session_start", None),
    ("view_item", "n_view_item"),
    ("add_to_cart", "n_add_to_cart"),
]
CHECKOUT_STEPS = [
    ("checkout_start", "n_checkout_start"),
    ("add_payment_info", "n_add_payment_info"),
    ("purchase", "n_purchase"),
]
UNORDERED_STEPS = [
    ("session_start", None),
    ("view_item", "u_view_item"),
    ("add_to_cart", "u_add_to_cart"),
    ("checkout_start", "u_checkout_start"),
    ("add_payment_info", "u_add_payment_info"),
    ("purchase", "u_purchase"),
]


def load_sessions():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT * FROM `{TABLE}`"
    sessions = client.query(query).to_dataframe()
    sessions["session_date"] = pd.to_datetime(sessions["session_date"].astype(str))
    sessions.to_parquet(DATA_DIR / "session_funnel.parquet", index=False)
    return sessions


def build_funnel(df, steps):
    rows = []
    for label, column in steps:
        count = len(df) if column is None else int(df[column].sum())
        rows.append({"step": label, "sessions": count})

    funnel = pd.DataFrame(rows)
    funnel["pct_of_first_step"] = funnel["sessions"] / funnel["sessions"].iloc[0]
    funnel["pct_of_all_sessions"] = funnel["sessions"] / len(df)
    funnel["step_conversion"] = funnel["sessions"] / funnel["sessions"].shift(1)
    funnel["step_dropoff"] = 1 - funnel["step_conversion"]
    return funnel


def plot_funnel(funnel, title, filename):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(funnel["step"], funnel["sessions"], color="#4C72B0")
    ax.invert_yaxis()
    for i, row in funnel.iterrows():
        label = f"{row['sessions']:,}  ({row['pct_of_first_step']:.1%})"
        ax.text(row["sessions"], i, "  " + label, va="center", fontsize=9)
    ax.set_title(title)
    ax.set_xlabel("Sessions")
    ax.set_xlim(0, funnel["sessions"].max() * 1.4)
    fig.tight_layout()
    fig.savefig(FIG_DIR / filename, dpi=150)
    plt.close(fig)


def checkout_entry_breakdown(df):
    checkout = df[df["n_checkout_start"]]
    table = checkout.groupby("checkout_entry_type").agg(
        checkout_sessions=("session_key", "count"),
        purchases=("n_purchase", "sum"),
    )
    table["share_of_checkouts"] = table["checkout_sessions"] / table["checkout_sessions"].sum()
    table["checkout_to_purchase"] = table["purchases"] / table["checkout_sessions"]
    return table.sort_values("checkout_sessions", ascending=False)


def main():
    sessions = load_sessions()
    print(f"Sessions: {len(sessions):,}")
    print(f"Users: {sessions['user_pseudo_id'].nunique():,}")

    browse = build_funnel(sessions, BROWSE_STEPS)
    checkout = build_funnel(sessions, CHECKOUT_STEPS)
    unordered = build_funnel(sessions, UNORDERED_STEPS)
    entry = checkout_entry_breakdown(sessions)

    print("\nBrowse funnel (nested, primary)")
    print(browse.to_string(index=False))
    print("\nCheckout funnel (nested from checkout entry, primary)")
    print(checkout.to_string(index=False))
    print("\nUnordered funnel (upper bound)")
    print(unordered.to_string(index=False))
    print("\nCheckout sessions by entry type")
    print(entry.to_string())

    browse.to_csv(TABLE_DIR / "funnel_browse.csv", index=False)
    checkout.to_csv(TABLE_DIR / "funnel_checkout.csv", index=False)
    unordered.to_csv(TABLE_DIR / "funnel_unordered.csv", index=False)
    entry.to_csv(TABLE_DIR / "checkout_entry_type.csv")

    plot_funnel(browse, "Browse funnel (nested)", "funnel_browse.png")
    plot_funnel(checkout, "Checkout funnel (nested from checkout entry)", "funnel_checkout.png")
    plot_funnel(unordered, "Unordered funnel (upper bound)", "funnel_unordered.png")

    all_purchases = int(sessions["u_purchase"].sum())
    nested_purchases = int(sessions["n_purchase"].sum())
    revenue = sessions["revenue_usd"].sum()
    print(f"\nPurchase sessions (any): {all_purchases:,}")
    print(f"Purchase sessions kept by nested checkout funnel: {nested_purchases:,} "
          f"({nested_purchases / all_purchases:.1%})")
    print(f"Session conversion rate: {all_purchases / len(sessions):.2%}")
    print(f"Average order value: ${revenue / all_purchases:,.2f}")


if __name__ == "__main__":
    main()