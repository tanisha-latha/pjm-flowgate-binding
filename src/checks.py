"""Clock checks: confirm which hour label each file uses before trusting any join.

1. Spring-forward days have no 02:00 local. A file labelled hour-beginning is
   missing hour 2; a file labelled hour-ending is missing hour 3.
2. After shifting to hour-beginning, series that should move together
   (RTO load and the system energy price, solar output in two different feeds)
   should line up best at zero lag, not one hour off.
"""
import pandas as pd

from config import PROCESSED, RAW, RESULTS

SPRING = ["2024-03-10", "2025-03-09", "2026-03-08"]


def missing_hours(df, date_col, hour_col, hours):
    out = {}
    for d in SPRING:
        present = set(df.loc[df[date_col] == d, hour_col])
        out[d] = sorted(set(hours) - present)
    return out


def main():
    lines = ["# Clock checks", "", "## 1. Missing hour on spring-forward days", ""]
    files = [
        ("rt_hrl_lmps", "hour_ending", range(1, 25), "hour-ending"),
        ("hrl_load", "opr_hour", range(1, 25), "hour-ending"),
        ("wind_gen", "opr_hour", range(0, 24), "hour-beginning"),
        ("solar_gen", "opr_hour", range(0, 24), "hour-beginning"),
        ("gen_by_fuel", "opr_hour", range(0, 24), "hour-beginning"),
    ]
    for name, col, hours, label in files:
        df = pd.read_csv(RAW / f"{name}.csv", usecols=["opr_date", col])
        miss = missing_hours(df, "opr_date", col, hours)
        lines.append(f"- {name}: missing {miss} -> {label}")

    t = pd.read_csv(PROCESSED / "hourly.csv.gz", index_col=0, parse_dates=True)
    lines += ["", "## 2. Lag check after alignment (correlation)", ""]
    pairs = [
        ("load_rto", "energy_price", "RTO load vs system energy price"),
        ("solar_rto", "gen_solar", "solar feed vs fuel-mix solar"),
    ]
    for a, b, label in pairs:
        cors = {lag: t[a].corr(t[b].shift(lag)) for lag in (-2, -1, 0, 1, 2)}
        best = max(cors, key=cors.get)
        row = ", ".join(f"{lag:+d}h: {r:.3f}" for lag, r in cors.items())
        lines.append(f"- {label}: {row} (best at {best:+d}h)")

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "clock_checks.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
