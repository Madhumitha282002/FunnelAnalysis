from pathlib import Path

import pandas as pd

DATA_PATH = Path("data/session_funnel.parquet")
TABLE_DIR = Path("outputs/tables")
WEEK0 = pd.Timestamp("2020-12-14")
WEEK1 = pd.Timestamp("2020-12-21")


def step_rates(df):
    carted = df[df["u_add_to_cart"]]
    checkout = df[df["n_checkout_start"]]
    payment = df[df["n_add_payment_info"]]
    purchases = df["u_purchase"].sum()
    return pd.Series({
        "sessions": len(df),
        "session_to_view": df["n_view_item"].mean(),
        "view_to_cart": df["n_add_to_cart"].sum() / df["n_view_item"].sum(),
        "cart_to_checkout": carted["n_checkout_start"].mean(),
        "checkout_to_payment": checkout["n_add_payment_info"].mean(),
        "payment_to_purchase": payment["n_purchase"].mean(),
        "checkout_to_purchase": checkout["n_purchase"].mean(),
        "session_conversion": purchases / len(df),
        "aov_usd": df["revenue_usd"].sum() / purchases,
    })


def main():
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(DATA_PATH)
    df["session_date"] = pd.to_datetime(df["session_date"])
    df["week"] = df["session_date"].dt.to_period("W-SUN").dt.start_time

    before = step_rates(df[df["week"] == WEEK0])
    after = step_rates(df[df["week"] == WEEK1])
    table = pd.DataFrame({"week_of_dec_14": before, "week_of_dec_21": after})
    table["abs_change"] = table["week_of_dec_21"] - table["week_of_dec_14"]
    table["rel_change"] = table["abs_change"] / table["week_of_dec_14"]

    print(table.round(4).to_string())
    table.to_csv(TABLE_DIR / "day5_step_rates.csv")


if __name__ == "__main__":
    main()