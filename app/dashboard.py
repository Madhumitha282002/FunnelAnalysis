from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent / "dashboard_data.parquet"

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
FILTER_COLUMNS = {
    "Device": "device_category",
    "Traffic medium": "traffic_medium",
    "User type": "user_type",
}


@st.cache_data
def load_data():
    df = pd.read_parquet(DATA_PATH)
    df["week"] = df["session_date"].dt.to_period("W-SUN").dt.start_time
    return df


def funnel_table(df, steps):
    rows = []
    for label, column in steps:
        count = len(df) if column is None else int(df[column].sum())
        rows.append({"step": label, "sessions": count})
    table = pd.DataFrame(rows)
    table["step_conversion"] = (table["sessions"] / table["sessions"].shift(1)).round(3)
    table["pct_of_first_step"] = (table["sessions"] / table["sessions"].iloc[0]).round(3)
    return table


def funnel_chart(table):
    return (
        alt.Chart(table)
        .mark_bar(color="#4C72B0")
        .encode(
            x=alt.X("sessions:Q", title="Sessions"),
            y=alt.Y("step:N", sort=None, title=None),
            tooltip=["step", "sessions", "step_conversion", "pct_of_first_step"],
        )
        .properties(height=50 * len(table))
    )


def rate_by(df, group_col, entered_col, converted_col):
    entered = df[df[entered_col]]
    table = (
        entered.groupby(group_col, observed=True)
        .agg(sessions=(converted_col, "size"), rate=(converted_col, "mean"))
        .reset_index()
    )
    table["rate"] = table["rate"].round(3)
    return table.sort_values("sessions", ascending=False)


def main():
    st.set_page_config(page_title="Funnel Leak Diagnosis", layout="wide")
    st.title("Ecommerce Funnel Leak Diagnosis")
    st.caption("Google Merchandise Store GA4 sample, Nov 2020 to Jan 2021. Session-level data.")

    df = load_data()

    st.sidebar.header("Filters")
    view = df
    for label, column in FILTER_COLUMNS.items():
        options = sorted(df[column].astype(str).unique())
        picked = st.sidebar.multiselect(label, options, default=options)
        view = view[view[column].astype(str).isin(picked)]

    if view.empty:
        st.warning("No sessions match the selected filters.")
        return

    sessions = len(view)
    purchases = int(view["u_purchase"].sum())
    revenue = float(view["revenue_usd"].sum())
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sessions", f"{sessions:,}")
    col2.metric("Purchases", f"{purchases:,}")
    col3.metric("Session conversion", f"{purchases / sessions:.2%}")
    col4.metric("Revenue", f"${revenue:,.0f}")
    st.caption("Revenue for the week of Jan 25 appears incomplete in the source data.")

    left, right = st.columns(2)
    with left:
        st.subheader("Browse funnel")
        browse = funnel_table(view, BROWSE_STEPS)
        st.altair_chart(funnel_chart(browse), use_container_width=True)
        st.dataframe(browse, hide_index=True)
    with right:
        st.subheader("Checkout funnel")
        checkout = funnel_table(view, CHECKOUT_STEPS)
        st.altair_chart(funnel_chart(checkout), use_container_width=True)
        st.dataframe(checkout, hide_index=True)

    st.subheader("Key leak: checkout to payment by user type")
    payment = rate_by(view, "user_type", "n_checkout_start", "n_add_payment_info")
    payment_chart = (
        alt.Chart(payment)
        .mark_bar(color="#C44E52")
        .encode(
            x=alt.X("rate:Q", title="Checkout to payment rate", axis=alt.Axis(format="%")),
            y=alt.Y("user_type:N", title=None),
            tooltip=["user_type", "sessions", "rate"],
        )
    )
    st.altair_chart(payment_chart, use_container_width=True)

    st.subheader("Weekly session conversion")
    weekly = (
        view.groupby("week")
        .agg(sessions=("u_purchase", "size"), purchases=("u_purchase", "sum"))
        .reset_index()
    )
    weekly["conversion_rate"] = weekly["purchases"] / weekly["sessions"]
    weekly_chart = (
        alt.Chart(weekly)
        .mark_line(point=True, color="#4C72B0")
        .encode(
            x=alt.X("week:T", title="Week starting"),
            y=alt.Y("conversion_rate:Q", title="Conversion rate", axis=alt.Axis(format="%")),
            tooltip=["week", "sessions", "purchases", alt.Tooltip("conversion_rate:Q", format=".2%")],
        )
    )
    st.altair_chart(weekly_chart, use_container_width=True)

    st.subheader("Checkout to purchase by checkout entry type")
    st.dataframe(
        rate_by(view, "checkout_entry_type", "n_checkout_start", "n_purchase"),
        hide_index=True,
    )


if __name__ == "__main__":
    main()