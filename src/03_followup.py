from pathlib import Path

import pandas as pd

DATA_PATH = Path("data/session_funnel.parquet")
TABLE_DIR = Path("outputs/tables")


def stratified_rates(checkout, group_cols):
    table = checkout.groupby(group_cols).agg(
        checkout_sessions=("session_key", "count"),
        payment_rate=("n_add_payment_info", "mean"),
        purchase_rate=("n_purchase", "mean"),
    )
    return table[table["checkout_sessions"] >= 100].round(3)


def main():
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    sessions = pd.read_parquet(DATA_PATH)
    checkout = sessions[sessions["n_checkout_start"]].copy()
    for col in ["user_type", "checkout_entry_type", "device_category"]:
        checkout[col] = checkout[col].fillna("unknown")

    by_entry = stratified_rates(checkout, ["user_type", "checkout_entry_type"])
    by_device = stratified_rates(checkout, ["user_type", "device_category"])

    print("Checkout outcomes by user type and entry type")
    print(by_entry.to_string())
    print("\nCheckout outcomes by user type and device")
    print(by_device.to_string())

    by_entry.to_csv(TABLE_DIR / "checkout_by_user_type_entry_type.csv")
    by_device.to_csv(TABLE_DIR / "checkout_by_user_type_device.csv")


if __name__ == "__main__":
    main()