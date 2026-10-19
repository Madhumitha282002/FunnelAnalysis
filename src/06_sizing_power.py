import math
from pathlib import Path

import pandas as pd
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

DATA_PATH = Path("data/session_funnel.parquet")
TABLE_DIR = Path("outputs/tables")

SEGMENT_COLUMN = "user_type"
SEGMENT_VALUE = "new"
STEP_FROM = "n_checkout_start"
STEP_TO = "n_add_payment_info"

STEP_LIFTS = [0.05, 0.10, 0.20]
USER_MDES = [0.05, 0.10, 0.15]
ALPHA = 0.05
POWER = 0.80
MIN_DAYS = 14
WINDOW_DAYS = 7

DATA_END = pd.Timestamp("2021-02-01", tz="UTC")
HOLIDAY_START = pd.Timestamp("2020-12-14", tz="UTC")
HOLIDAY_END = pd.Timestamp("2021-01-18", tz="UTC")
REVENUE_SUSPECT_FROM = pd.Timestamp("2021-01-25")


def load_sessions():
    df = pd.read_parquet(DATA_PATH)
    df["session_date"] = pd.to_datetime(df["session_date"])
    df[SEGMENT_COLUMN] = df[SEGMENT_COLUMN].fillna("unknown")
    return df


def is_non_holiday(timestamps):
    return (timestamps < HOLIDAY_START) | (timestamps >= HOLIDAY_END)


def average_order_value(df, segment_only):
    buyers = df[df["u_purchase"] & (df["session_date"] < REVENUE_SUSPECT_FROM)]
    if segment_only:
        buyers = buyers[buyers[SEGMENT_COLUMN] == SEGMENT_VALUE]
    return buyers["revenue_usd"].sum() / len(buyers)


def later_purchase_rate(df, entered):
    abandoned = entered[~entered["u_purchase"]][["user_pseudo_id", "session_start_ts"]]
    purchases = df[df["u_purchase"]][["user_pseudo_id", "ts_purchase"]]
    merged = abandoned.merge(purchases, on="user_pseudo_id", how="left")
    merged["bought_later"] = merged["ts_purchase"] > merged["session_start_ts"]
    per_session = merged.groupby(["user_pseudo_id", "session_start_ts"])["bought_later"].any()
    return per_session.mean(), len(per_session)


def daily_rate(timestamps):
    kept = timestamps[is_non_holiday(timestamps)]
    return len(kept) / kept.dt.date.nunique()


def step_sizing(df):
    segment = df[df[SEGMENT_COLUMN] == SEGMENT_VALUE]
    entered = segment[segment[STEP_FROM]]
    reached = entered[entered[STEP_TO]]

    baseline = len(reached) / len(entered)
    downstream = reached["n_purchase"].mean()
    recapture, abandoned_sessions = later_purchase_rate(df, entered)
    aov_all = average_order_value(df, segment_only=False)
    aov_segment = average_order_value(df, segment_only=True)
    n_days = df["session_date"].nunique()
    daily_entering = daily_rate(entered["session_start_ts"])

    print(f"Target: {SEGMENT_COLUMN} = {SEGMENT_VALUE}, {STEP_FROM} -> {STEP_TO}")
    print(f"Sessions entering step over {n_days} days: {len(entered):,}")
    print(f"Daily sessions entering step (non-holiday): {daily_entering:,.0f}")
    print(f"Baseline step conversion: {baseline:.2%}")
    print(f"Purchase rate after reaching {STEP_TO}: {downstream:.2%}")
    print(f"Abandoned checkout sessions: {abandoned_sessions:,}")
    print(f"Share of those users who purchased in a later session: {recapture:.2%}")
    print(f"AOV, all buyers (excluding suspect final week): ${aov_all:,.2f}")
    print(f"AOV, {SEGMENT_VALUE} buyers (guardrail baseline): ${aov_segment:,.2f}")

    rows = []
    for lift in STEP_LIFTS:
        extra_step_sessions = len(entered) * baseline * lift
        gross_purchases = extra_step_sessions * downstream
        net_purchases = gross_purchases * (1 - recapture)
        net_revenue = net_purchases * aov_segment
        rows.append({
            "step_relative_lift": lift,
            "new_step_rate": baseline * (1 + lift),
            "extra_step_sessions": round(extra_step_sessions, 0),
            "gross_extra_purchases": round(gross_purchases, 0),
            "net_extra_purchases": round(net_purchases, 0),
            "net_extra_revenue_period_usd": round(net_revenue, 0),
            "net_extra_revenue_per_30_days_usd": round(net_revenue * 30 / n_days, 0),
        })
    sizing = pd.DataFrame(rows)
    print("\nOpportunity sizing (net of later-session recapture)")
    print(sizing.to_string(index=False))
    return sizing, baseline, daily_entering


def user_level_baseline(df):
    first_purchase = df.groupby("user_pseudo_id")["ts_purchase"].min()
    exposures = (
        df[(df[SEGMENT_COLUMN] == SEGMENT_VALUE) & df[STEP_FROM]]
        .sort_values("session_start_ts")
        .drop_duplicates("user_pseudo_id")[["user_pseudo_id", "session_start_ts"]]
        .copy()
    )
    exposures = exposures[exposures["session_start_ts"] < DATA_END - pd.Timedelta(days=WINDOW_DAYS)]
    exposures["first_purchase"] = exposures["user_pseudo_id"].map(first_purchase)
    deadline = exposures["session_start_ts"] + pd.Timedelta(days=WINDOW_DAYS)
    exposures["converted"] = (
        (exposures["first_purchase"] >= exposures["session_start_ts"])
        & (exposures["first_purchase"] <= deadline)
    )

    rate = exposures["converted"].mean()
    daily_users = daily_rate(exposures["session_start_ts"])

    print(f"\nPrimary metric: purchase within {WINDOW_DAYS} days of first reaching checkout")
    print(f"Eligible {SEGMENT_VALUE} users: {len(exposures):,}")
    print(f"Baseline {WINDOW_DAYS}-day purchase rate: {rate:.2%}")
    print(f"Daily eligible users (non-holiday): {daily_users:,.1f}")
    return rate, daily_users


def power_table(baseline, daily_units, lifts, unit_label):
    rows = []
    for lift in lifts:
        target = min(baseline * (1 + lift), 0.9999)
        effect = proportion_effectsize(target, baseline)
        n_per_arm = math.ceil(NormalIndPower().solve_power(
            effect_size=effect, alpha=ALPHA, power=POWER, ratio=1.0, alternative="two-sided"
        ))
        raw_days = math.ceil(2 * n_per_arm / daily_units)
        recommended_days = max(MIN_DAYS, math.ceil(raw_days / 7) * 7)
        rows.append({
            "relative_mde": lift,
            "baseline": round(baseline, 4),
            "target": round(target, 4),
            f"{unit_label}_per_arm": n_per_arm,
            "days_needed_raw": raw_days,
            "recommended_days": recommended_days,
            "recommended_weeks": recommended_days // 7,
        })
    return pd.DataFrame(rows)


def main():
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df = load_sessions()

    sizing, step_baseline, daily_step_sessions = step_sizing(df)
    user_rate, daily_users = user_level_baseline(df)

    primary = power_table(user_rate, daily_users, USER_MDES, "users")
    secondary = power_table(step_baseline, daily_step_sessions, STEP_LIFTS, "sessions")

    print("\nPower: primary metric (user-level 7-day purchase)")
    print(primary.to_string(index=False))
    print("\nPower: secondary metric (session-level checkout to payment)")
    print(secondary.to_string(index=False))

    sizing.to_csv(TABLE_DIR / "sizing.csv", index=False)
    primary.to_csv(TABLE_DIR / "power_primary_user_level.csv", index=False)
    secondary.to_csv(TABLE_DIR / "power_secondary_step.csv", index=False)


if __name__ == "__main__":
    main()