from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint, proportions_ztest

DATA_PATH = Path("data/session_funnel.parquet")
FIG_DIR = Path("outputs/figures")
TABLE_DIR = Path("outputs/tables")

TRANSITIONS = [
    {"name": "session_start -> view_item", "from": None, "to": "n_view_item", "stage": "browse"},
    {"name": "view_item -> add_to_cart", "from": "n_view_item", "to": "n_add_to_cart", "stage": "browse"},
    {"name": "add_to_cart -> checkout_start", "from": "u_add_to_cart", "to": "n_checkout_start", "stage": "browse"},
    {"name": "checkout_start -> add_payment_info", "from": "n_checkout_start", "to": "n_add_payment_info", "stage": "checkout"},
    {"name": "add_payment_info -> purchase", "from": "n_add_payment_info", "to": "n_purchase", "stage": "checkout"},
    {"name": "checkout_start -> purchase", "from": "n_checkout_start", "to": "n_purchase", "stage": "checkout"},
]
BASE_SEGMENTS = ["device_category", "traffic_medium", "country", "user_type"]
CHECKOUT_SEGMENTS = BASE_SEGMENTS + ["checkout_entry_type"]
MIN_SAMPLE = 100
TOP_COUNTRIES = 8


def prepare(df):
    df = df.copy()
    top = df["country"].value_counts().head(TOP_COUNTRIES).index
    df["country"] = df["country"].where(df["country"].isin(top), "Other countries")
    for col in CHECKOUT_SEGMENTS:
        df[col] = df[col].fillna("unknown")
    return df


def entered_mask(df, column):
    if column is None:
        return pd.Series(True, index=df.index)
    return df[column].astype(bool)


def segment_step_stats(df):
    rows = []
    for transition in TRANSITIONS:
        entered = entered_mask(df, transition["from"])
        converted = entered & df[transition["to"]].astype(bool)
        segments = CHECKOUT_SEGMENTS if transition["stage"] == "checkout" else BASE_SEGMENTS

        for segment in segments:
            for value in df.loc[entered, segment].unique():
                in_seg = df[segment] == value

                n_seg = int((in_seg & entered).sum())
                x_seg = int((in_seg & converted).sum())
                n_rest = int((~in_seg & entered).sum())
                x_rest = int((~in_seg & converted).sum())

                if n_seg < MIN_SAMPLE or n_rest < MIN_SAMPLE:
                    continue

                rate_seg = x_seg / n_seg
                rate_rest = x_rest / n_rest
                ci_low, ci_high = proportion_confint(x_seg, n_seg, method="wilson")
                _, p_value = proportions_ztest([x_seg, x_rest], [n_seg, n_rest])

                rows.append({
                    "stage": transition["stage"],
                    "transition": transition["name"],
                    "segment": segment,
                    "value": value,
                    "n_entered": n_seg,
                    "n_converted": x_seg,
                    "rate": rate_seg,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "rate_rest": rate_rest,
                    "abs_diff": rate_seg - rate_rest,
                    "rel_diff": (rate_seg - rate_rest) / rate_rest if rate_rest > 0 else None,
                    "lost_sessions": (rate_rest - rate_seg) * n_seg,
                    "p_value": p_value,
                })
    return pd.DataFrame(rows)


def add_corrections(stats):
    stats = stats.dropna(subset=["p_value"]).copy()
    reject, p_adj, _, _ = multipletests(stats["p_value"], alpha=0.05, method="fdr_bh")
    stats["p_adjusted"] = p_adj
    stats["significant"] = reject
    stats["is_leak"] = stats["significant"] & (stats["abs_diff"] < 0)
    return stats


def entry_type_by_segment(df):
    checkout = df[df["n_checkout_start"]]
    tables = {}
    for segment in ["device_category", "traffic_medium", "user_type"]:
        table = pd.crosstab(checkout[segment], checkout["checkout_entry_type"], normalize="index")
        table["checkout_sessions"] = checkout[segment].value_counts()
        tables[segment] = table.sort_values("checkout_sessions", ascending=False)
        table.to_csv(TABLE_DIR / f"entry_type_by_{segment}.csv")
    return tables


def plot_segment(stats, segment, transition, filename):
    subset = stats[(stats["segment"] == segment) & (stats["transition"] == transition)]
    if subset.empty:
        return
    subset = subset.sort_values("rate")
    errors = [subset["rate"] - subset["ci_low"], subset["ci_high"] - subset["rate"]]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(subset["value"], subset["rate"], xerr=errors, color="#55A868", capsize=4)
    ax.set_title(f"{transition} by {segment}")
    ax.set_xlabel("Step conversion rate (95% Wilson CI)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / filename, dpi=150)
    plt.close(fig)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    sessions = prepare(pd.read_parquet(DATA_PATH))
    stats = add_corrections(segment_step_stats(sessions))
    stats.to_csv(TABLE_DIR / "segment_step_stats.csv", index=False)

    leaks = stats[stats["is_leak"]].sort_values("lost_sessions", ascending=False)
    leaks.to_csv(TABLE_DIR / "top_leaks.csv", index=False)

    columns = ["transition", "segment", "value", "n_entered", "rate", "rate_rest", "lost_sessions", "p_adjusted"]
    print(f"Comparisons tested: {len(stats)}")
    print(f"Significant leaks after BH correction: {len(leaks)}")
    print("\nTop 15 leaks ranked by lost sessions")
    print(leaks[columns].head(15).to_string(index=False))

    print("\nCheckout entry type mix by segment (row shares)")
    for segment, table in entry_type_by_segment(sessions).items():
        print(f"\n{segment}")
        print(table.round(3).to_string())

    for segment in BASE_SEGMENTS:
        plot_segment(stats, segment, "view_item -> add_to_cart", f"view_to_cart_{segment}.png")
        plot_segment(stats, segment, "add_to_cart -> checkout_start", f"cart_to_checkout_{segment}.png")
        plot_segment(stats, segment, "checkout_start -> purchase", f"checkout_to_purchase_{segment}.png")
    plot_segment(stats, "checkout_entry_type", "checkout_start -> purchase", "checkout_to_purchase_entry_type.png")


if __name__ == "__main__":
    main()