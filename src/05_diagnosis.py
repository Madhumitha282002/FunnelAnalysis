from pathlib import Path
 
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter
 
DATA_PATH = Path("data/session_funnel.parquet")
FIG_DIR = Path("outputs/figures")
TABLE_DIR = Path("outputs/tables")
SEGMENTS = ["device_category", "traffic_medium", "user_type"]
 
 
def add_week(sessions):
    df = sessions.copy()
    df["session_date"] = pd.to_datetime(df["session_date"])
    df["week"] = df["session_date"].dt.to_period("W-SUN").dt.start_time
    days_per_week = df.groupby("week")["session_date"].nunique()
    full_weeks = days_per_week[days_per_week == 7].index
    df = df[df["week"].isin(full_weeks)]
    for col in SEGMENTS:
        df[col] = df[col].fillna("unknown")
    return df
 
 
def weekly_trend(df):
    weekly = df.groupby("week").agg(
        sessions=("session_key", "count"),
        purchases=("u_purchase", "sum"),
        revenue=("revenue_usd", "sum"),
    )
    weekly["conversion_rate"] = weekly["purchases"] / weekly["sessions"]
    weekly["cr_change"] = weekly["conversion_rate"].diff()
    weekly.to_csv(TABLE_DIR / "weekly_trend.csv")
 
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(weekly.index, weekly["conversion_rate"], marker="o", color="#C44E52")
    ax.set_title("Weekly session conversion rate")
    ax.set_ylabel("Conversion rate")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1%}"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "weekly_conversion.png", dpi=150)
    plt.close(fig)
    return weekly
 
 
def decompose(df, week0, week1, segment):
    before = df[df["week"] == week0].groupby(segment).agg(
        n0=("u_purchase", "size"), x0=("u_purchase", "sum")
    )
    after = df[df["week"] == week1].groupby(segment).agg(
        n1=("u_purchase", "size"), x1=("u_purchase", "sum")
    )
    table = before.join(after, how="outer").fillna(0)
    table["w0"] = table["n0"] / table["n0"].sum()
    table["w1"] = table["n1"] / table["n1"].sum()
    table["r0"] = (table["x0"] / table["n0"]).fillna(0)
    table["r1"] = (table["x1"] / table["n1"]).fillna(0)
    table["rate_effect"] = table["w0"] * (table["r1"] - table["r0"])
    table["mix_effect"] = (table["w1"] - table["w0"]) * table["r0"]
    table["interaction"] = (table["w1"] - table["w0"]) * (table["r1"] - table["r0"])
    table["total_effect"] = table["rate_effect"] + table["mix_effect"] + table["interaction"]
    return table
 
 
def main():
    df = add_week(pd.read_parquet(DATA_PATH))
    weekly = weekly_trend(df)
    print(weekly.round(4).to_string())
 
    biggest = weekly["cr_change"].abs().idxmax()
    position = weekly.index.get_loc(biggest)
    week0 = weekly.index[position - 1]
    week1 = biggest
    total_change = weekly.loc[week1, "conversion_rate"] - weekly.loc[week0, "conversion_rate"]
    print(f"\nBiggest change: {week0.date()} to {week1.date()}, {total_change:+.4f}")
 
    for segment in SEGMENTS:
        table = decompose(df, week0, week1, segment)
        table.to_csv(TABLE_DIR / f"decomposition_{segment}.csv")
        print(f"\nDecomposition by {segment}")
        print(table[["w0", "w1", "r0", "r1", "rate_effect", "mix_effect", "interaction"]].round(4).to_string())
        print(f"Rate effect total: {table['rate_effect'].sum():+.4f}")
        print(f"Mix effect total: {table['mix_effect'].sum():+.4f}")
        print(f"Interaction total: {table['interaction'].sum():+.4f}")
        print(f"Check sum: {table['total_effect'].sum():+.4f} vs actual {total_change:+.4f}")
 
 
if __name__ == "__main__":
    main()
