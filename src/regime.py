"""Bet on the regime, not the hour.

Rule: if an area was congested for N or more hours today, take tomorrow's spread
(1 MW, receive the real-time congestion spread every hour, no costs).
Compared with tomorrow after a day with no congestion at all.
Hourly spreads are clipped at the 1st/99th percentile so a cold snap can't decide the answer.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import load_table, pct, save, style
from config import AREA_COLOURS, AREAS, INK, MUTED, RESULTS, SPLIT, THRESHOLD

CUTOFFS = [1, 3, 6, 12]
RULE = 6


def daily(t, area):
    s = t[f"spread_{area}"]
    s = s.clip(s.quantile(0.01), s.quantile(0.99))
    d = pd.DataFrame({
        "hours": t[f"ev_{area}"].groupby(t.date).sum(),
        "spread": s.groupby(t.date).mean(),
        "spread_median": s.groupby(t.date).median(),
    })
    nxt = d.shift(-1)
    d["next_hours"], d["next_spread"], d["next_spread_median"] = nxt.hours, nxt.spread, nxt.spread_median
    # only pair consecutive calendar days
    d = d[(d.index.to_series().shift(-1) - d.index.to_series()) == pd.Timedelta(days=1)]
    return d.dropna()


def summarise(d, cond):
    g = d[cond]
    return {"days": len(g), "p_congested_tomorrow": (g.next_hours > 0).mean(),
            "p_6plus_tomorrow": (g.next_hours >= RULE).mean(),
            "next_spread_mean": g.next_spread.mean(), "next_spread_median": g.next_spread_median.median()}


def main():
    style()
    t = load_table()
    rows = []
    for area in AREAS:
        d = daily(t, area)
        for period, dd in [("all", d), ("test", d[d.index >= SPLIT])]:
            rows.append({"area": area, "period": period, "condition": "0 hours today", **summarise(dd, dd.hours == 0)})
            for c in CUTOFFS:
                rows.append({"area": area, "period": period, "condition": f"{c}+ hours today",
                             **summarise(dd, dd.hours >= c)})
    out = pd.DataFrame(rows)
    out.round(3).to_csv(RESULTS / "regime_rule.csv", index=False)

    a = out[(out.period == "all") & out.condition.isin(["0 hours today", f"{RULE}+ hours today"])]
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    w = 0.36
    for i, area in enumerate(AREAS):
        g = a[a.area == area].set_index("condition")
        quiet, busy = g.loc["0 hours today", "next_spread_mean"], g.loc[f"{RULE}+ hours today", "next_spread_mean"]
        ax.bar(i - w / 2, quiet, w - 0.03, color=AREA_COLOURS[area], alpha=0.35)
        ax.bar(i + w / 2, busy, w - 0.03, color=AREA_COLOURS[area])
        ax.text(i - w / 2, quiet + 0.5, f"${quiet:.0f}", ha="center", fontsize=8.5, color=INK)
        ax.text(i + w / 2, busy + 0.5, f"${busy:.0f}", ha="center", fontsize=8.5, color=INK)
        p = g.loc[f"{RULE}+ hours today", "p_congested_tomorrow"]
        ax.text(i + w / 2, busy / 2, f"{p:.0%}\ncongested\nagain", ha="center", va="center", fontsize=7.5, color="white")
    ax.set_xticks(range(len(AREAS)), [f"{a.title()}\nquiet day | {RULE}+ hour day" for a in AREAS], fontsize=8.5)
    ax.set_ylabel("tomorrow's average spread ($/MWh)")
    ax.set_title(f"After a {RULE}+ hour day, tomorrow's spread is wider")
    ax.grid(axis="x", visible=False)
    save(fig, "08_regime_rule.png",
         source="Source: PJM Data Miner 2 real-time LMPs, Jan 2024 to Aug 2026. Hourly spreads clipped at 1st/99th "
                "percentile. No transaction costs.")
    pd.set_option("display.width", 220)
    print(out.round(3).to_string())


if __name__ == "__main__":
    main()
