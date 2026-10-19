from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "funnelproject-511023"
DATA_PATH = Path("data/session_funnel.parquet")
FIG_DIR = Path("outputs/figures")
TABLE_DIR = Path("outputs/tables")
CUTOFF_FIRST_SEEN = pd.Timestamp("2021-01-01", tz="UTC")
MIN_CART_ROWS = 200

CATEGORY_SQL = """
WITH item_rows AS (
  SELECT
    event_name,
    item.item_id AS item_id,
    item.item_category AS raw_category,
    IFNULL(item.item_revenue_in_usd, 0) AS item_revenue_usd
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
    UNNEST(items) AS item
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND event_name IN ('view_item', 'add_to_cart', 'begin_checkout', 'purchase')
    AND item.item_id IS NOT NULL
    AND item.item_id NOT IN ('', '(not set)')
),
category_counts AS (
  SELECT item_id, raw_category, COUNT(*) AS n
  FROM item_rows
  WHERE event_name IN ('begin_checkout', 'purchase')
    AND raw_category IS NOT NULL
    AND raw_category NOT IN ('', '(not set)')
  GROUP BY item_id, raw_category
),
item_lookup AS (
  SELECT
    item_id,
    ARRAY_AGG(raw_category ORDER BY n DESC, raw_category LIMIT 1)[OFFSET(0)] AS product_category
  FROM category_counts
  GROUP BY item_id
)
SELECT
  IFNULL(l.product_category, '(unmapped)') AS product_category,
  COUNT(DISTINCT r.item_id) AS items,
  COUNTIF(r.event_name = 'view_item') AS view_item_rows,
  COUNTIF(r.event_name = 'add_to_cart') AS add_to_cart_rows,
  COUNTIF(r.event_name = 'begin_checkout') AS checkout_rows,
  COUNTIF(r.event_name = 'purchase') AS purchase_rows,
  ROUND(SUM(IF(r.event_name = 'purchase', r.item_revenue_usd, 0)), 2) AS item_revenue_usd
FROM item_rows AS r
LEFT JOIN item_lookup AS l
  ON r.item_id = l.item_id
GROUP BY product_category
"""

CHECKOUT_ITEMS_SQL = """
WITH checkout_events AS (
  SELECT
    CONCAT(
      user_pseudo_id, '-',
      CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
    ) AS session_key,
    IFNULL(ARRAY_LENGTH(items), 0) AS n_items,
    (SELECT IFNULL(SUM(i.quantity), 0) FROM UNNEST(items) AS i) AS total_quantity
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND event_name = 'begin_checkout'
)
SELECT
  session_key,
  COUNT(*) AS checkout_events,
  MAX(n_items) AS max_items,
  MAX(total_quantity) AS max_quantity
FROM checkout_events
WHERE session_key IS NOT NULL
GROUP BY session_key
"""


def time_to_convert(sessions):
    users = sessions.groupby("user_pseudo_id").agg(
        first_seen=("session_start_ts", "min"),
        first_purchase=("ts_purchase", "min"),
        total_sessions=("session_key", "count"),
    )
    users = users[users["first_seen"] < CUTOFF_FIRST_SEEN]
    buyers = users.dropna(subset=["first_purchase"]).copy()
    buyers["hours_to_convert"] = (
        buyers["first_purchase"] - buyers["first_seen"]
    ).dt.total_seconds() / 3600

    merged = sessions.merge(
        buyers[["first_purchase"]], left_on="user_pseudo_id", right_index=True
    )
    before = merged[merged["session_start_ts"] <= merged["first_purchase"]]
    sessions_to_buy = before.groupby("user_pseudo_id").size()
    buyers["sessions_to_purchase"] = sessions_to_buy

    print(f"Users first seen before cutoff: {len(users):,}")
    print(f"Of those who purchased: {len(buyers):,} ({len(buyers) / len(users):.2%})")
    print("\nHours to convert (percentiles)")
    print(buyers["hours_to_convert"].quantile([0.25, 0.5, 0.75, 0.9]).round(1).to_string())
    print("\nSessions up to and including first purchase")
    print(buyers["sessions_to_purchase"].value_counts().sort_index().head(10).to_string())
    buyers.to_csv(TABLE_DIR / "buyers_time_to_convert.csv")
    return buyers


def plot_sessions_to_purchase(buyers):
    counts = buyers["sessions_to_purchase"].clip(upper=6).value_counts().sort_index()
    labels = [str(int(i)) if i < 6 else "6+" for i in counts.index]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(labels, counts.values / counts.sum(), color="#8172B2")
    ax.set_title("Sessions needed before first purchase")
    ax.set_xlabel("Sessions")
    ax.set_ylabel("Share of buyers")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "sessions_to_purchase.png", dpi=150)
    plt.close(fig)


def cart_abandonment(sessions):
    carted = sessions[sessions["u_add_to_cart"]]
    table = carted.groupby("device_category").agg(
        cart_sessions=("session_key", "count"),
        purchased=("u_purchase", "sum"),
    )
    table["abandonment_rate"] = 1 - table["purchased"] / table["cart_sessions"]
    overall = 1 - carted["u_purchase"].sum() / len(carted)
    print(f"\nOverall cart abandonment: {overall:.2%}")
    print(table.sort_values("abandonment_rate", ascending=False).to_string())
    table.to_csv(TABLE_DIR / "cart_abandonment_by_device.csv")


def category_analysis(client):
    cats = client.query(CATEGORY_SQL).to_dataframe()

    total_cart_rows = cats["add_to_cart_rows"].sum()
    unmapped = cats[cats["product_category"] == "(unmapped)"]
    unmapped_cart_rows = int(unmapped["add_to_cart_rows"].sum())
    print("\nCategory mapping coverage")
    print(f"Total revenue across categories: ${cats['item_revenue_usd'].sum():,.0f}")
    print(f"Cart item rows unmapped: {unmapped_cart_rows:,} "
          f"({unmapped_cart_rows / total_cart_rows:.1%} of all cart item rows)")

    mapped = cats[(cats["product_category"] != "(unmapped)")
                  & (cats["add_to_cart_rows"] >= MIN_CART_ROWS)].copy()
    mapped["view_to_cart"] = mapped["add_to_cart_rows"] / mapped["view_item_rows"]
    mapped["cart_to_checkout"] = mapped["checkout_rows"] / mapped["add_to_cart_rows"]
    mapped["cart_to_purchase"] = mapped["purchase_rows"] / mapped["add_to_cart_rows"]
    mapped["revenue_share"] = mapped["item_revenue_usd"] / cats["item_revenue_usd"].sum()
    mapped = mapped.sort_values("cart_to_purchase")

    cats.to_csv(TABLE_DIR / "category_funnel_raw.csv", index=False)
    mapped.to_csv(TABLE_DIR / "category_funnel.csv", index=False)

    columns = ["product_category", "items", "add_to_cart_rows", "purchase_rows",
               "view_to_cart", "cart_to_checkout", "cart_to_purchase", "revenue_share"]
    print(f"\nProduct categories with at least {MIN_CART_ROWS} cart rows, weakest cart to purchase first")
    print(mapped[columns].round(3).to_string(index=False))


def empty_cart_check(sessions, client):
    items = client.query(CHECKOUT_ITEMS_SQL).to_dataframe()
    checkout = sessions[sessions["u_begin_checkout"]].merge(items, on="session_key", how="left")
    checkout["checkout_entry_type"] = checkout["checkout_entry_type"].fillna("unknown")
    checkout["max_items"] = checkout["max_items"].fillna(0).astype(int)
    checkout["has_items"] = checkout["max_items"] > 0

    detail = checkout.groupby(["checkout_entry_type", "has_items"]).agg(
        checkout_sessions=("session_key", "count"),
        payment_rate=("n_add_payment_info", "mean"),
        purchase_rate=("n_purchase", "mean"),
    )
    entry_totals = checkout.groupby("checkout_entry_type")["session_key"].count()
    detail["share_of_entry_type"] = (
        detail["checkout_sessions"].values
        / entry_totals.reindex(detail.index.get_level_values(0)).values
    )

    summary = checkout.groupby("checkout_entry_type").agg(
        checkout_sessions=("session_key", "count"),
        share_with_items=("has_items", "mean"),
        median_items=("max_items", "median"),
    )

    print("\nEmpty cart check: begin_checkout sessions by entry type")
    print(summary.round(3).to_string())
    print("\nOutcomes by entry type and whether checkout carried items")
    print(detail.round(3).to_string())

    summary.to_csv(TABLE_DIR / "empty_cart_summary.csv")
    detail.to_csv(TABLE_DIR / "empty_cart_detail.csv")


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    client = bigquery.Client(project=PROJECT_ID)
    sessions = pd.read_parquet(DATA_PATH)

    buyers = time_to_convert(sessions)
    plot_sessions_to_purchase(buyers)
    cart_abandonment(sessions)
    category_analysis(client)
    empty_cart_check(sessions, client)


if __name__ == "__main__":
    main()