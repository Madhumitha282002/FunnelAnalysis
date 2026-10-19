from pathlib import Path

import pandas as pd

SOURCE = Path("data/session_funnel.parquet")
TARGET = Path("app/dashboard_data.parquet")

COLUMNS = [
    "session_date",
    "device_category",
    "traffic_medium",
    "user_type",
    "checkout_entry_type",
    "n_view_item",
    "n_add_to_cart",
    "u_add_to_cart",
    "n_checkout_start",
    "n_add_payment_info",
    "n_purchase",
    "u_purchase",
    "revenue_usd",
]
CATEGORY_COLUMNS = ["device_category", "traffic_medium", "user_type", "checkout_entry_type"]
BOOL_COLUMNS = [
    "n_view_item",
    "n_add_to_cart",
    "u_add_to_cart",
    "n_checkout_start",
    "n_add_payment_info",
    "n_purchase",
    "u_purchase",
]


def main():
    df = pd.read_parquet(SOURCE, columns=COLUMNS)
    df["session_date"] = pd.to_datetime(df["session_date"])
    for col in CATEGORY_COLUMNS:
        df[col] = df[col].fillna("unknown").astype("category")
    for col in BOOL_COLUMNS:
        df[col] = df[col].fillna(False).astype(bool)
    df["revenue_usd"] = df["revenue_usd"].fillna(0).astype("float32")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(TARGET, index=False, compression="zstd")
    size_mb = TARGET.stat().st_size / 1_000_000
    print(f"Wrote {len(df):,} rows to {TARGET} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()