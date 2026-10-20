"""When is each area congested, and which fundamentals move with it?

Every comparison is made within a year, because congestion rose every year.
Pooling 2024-2026 would make anything that also trended up look like a driver.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from common import load_table, pct, save, style
from config import AREA_COLOURS, AREAS, INK, MUTED, RESULTS, THRESHOLD, THRESHOLDS, YEAR_COLOURS

BLUES = LinearSegmentedColormap.from_list(
    "blues", ["#f3f7fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
)
NIGHT = [22, 23, 0, 1, 2, 3, 4, 5, 6]


def share_by_year(t):
    # Jan to Aug only, so 2026 (which ends in August) is compared like for like
    t = t[t.month <= 8]
    rows = []
    for th in THRESHOLDS:
        for a in AREAS:
            s = (t[f"spread_{a}"] > th).groupby(t.year).mean()
            rows += [{"area": a, "threshold": th, "year": y, "share": v} for y, v in s.items()]
    return pd.DataFrame(rows)


def chart_by_year(shares):
    s = shares[shares.threshold == THRESHOLD].pivot(index="year", columns="area", values="share")
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    w = 0.26
    for i, a in enumerate(AREAS):
        x = np.arange(len(s)) + (i - 1) * w
        bars = ax.bar(x, s[a], width=w - 0.02, color=AREA_COLOURS[a], label=AREAS[a]["label"])
        for b, v in zip(bars, s[a]):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.008, f"{v:.0%}", ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(np.arange(len(s)), [str(y) for y in s.index])
    pct(ax)
    ax.set_ylim(0, s.values.max() * 1.18)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel(f"share of Jan-Aug hours with spread > ${THRESHOLD:.0f}")
    ax.set_title("Congestion jumped in 2026 in all three areas (January to August)")
    ax.legend(loc="upper left", fontsize=8.5)
    save(fig, "01_congested_share_by_year.png")


def chart_heatmaps(t):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), sharey=True)
    for ax, a in zip(axes, AREAS):
        m = t.groupby(["hour", "month"])[f"ev_{a}"].mean().unstack()
        im = ax.imshow(m.values, aspect="auto", origin="lower", cmap=BLUES, vmin=0, vmax=0.7)
        ax.set_xticks(range(12), list("JFMAMJJASOND"))
        ax.set_yticks(range(0, 24, 3))
        ax.grid(False)
        ax.set_title(AREAS[a]["label"], fontsize=10)
        ax.set_xlabel("month")
    axes[0].set_ylabel("hour beginning (local)")
    cb = fig.colorbar(im, ax=axes, shrink=0.85, pad=0.015)
    cb.outline.set_visible(False)
    cb.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    cb.set_label("share of hours congested", color=MUTED)
    fig.suptitle("When each area is congested, 2024 to Aug 2026", x=0.01, ha="left", fontweight="bold", color=INK)
    save(fig, "02_hour_month_heatmaps.png")


def binned(t, col, area, bins, mask=None):
    d = t if mask is None else t[mask]
    edges = np.quantile(d[col].dropna(), np.linspace(0, 1, bins + 1))
    b = pd.cut(d[col], edges, include_lowest=True)
    out = d.groupby(["year", b], observed=True)[f"ev_{area}"].agg(["mean", "size"]).reset_index()
    out["mid"] = out[col].apply(lambda iv: iv.mid)
    return out[out["size"] >= 50]  # drop thin bins


def chart_lines(df, area, xlab, title, name, xfmt=lambda v: f"{v / 1000:.0f}"):
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    for y, g in df.groupby("year"):
        ax.plot(g["mid"], g["mean"], marker="o", ms=5, color=YEAR_COLOURS[y], label=str(y))
    pct(ax)
    ax.set_ylim(0, None)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: xfmt(v)))
    ax.set_xlabel(xlab)
    ax.set_ylabel("share of hours congested")
    ax.set_title(title)
    ax.legend(title="year", fontsize=8.5, loc="upper left")
    save(fig, name)


def chicago_grid(t):
    n = t[t.hour.isin(NIGHT)]
    rows = []
    for y, g in n.groupby("year"):
        wind_hi = g.wind_west > n.wind_west.median()
        load_hi = g.load_comed > n.load_comed.median()
        for w in (False, True):
            for l in (False, True):
                m = (wind_hi == w) & (load_hi == l)
                rows.append({"year": y, "high_wind": w, "high_load": l,
                             "share": g.loc[m, "ev_chicago"].mean(), "hours": int(m.sum())})
    return pd.DataFrame(rows)


def main():
    style()
    t = load_table()
    RESULTS.mkdir(exist_ok=True)

    shares = share_by_year(t)
    shares.to_csv(RESULTS / "congested_share_by_year.csv", index=False)
    chart_by_year(shares)
    chart_heatmaps(t)

    t = t.assign(load_dom_bge=t.load_dom + t.load_bge)
    balt = binned(t, "load_dom_bge", "baltimore", 8)
    balt.to_csv(RESULTS / "baltimore_by_load.csv", index=False)
    chart_lines(balt, "baltimore", "Dominion + BGE load (GW)",
                "Baltimore: congestion rises with load, and low-load hours got more congested",
                "03_baltimore_by_load.png")

    midday = t.hour.between(10, 15)
    rich = binned(t, "solar_south", "richmond", 5, midday)
    rich.to_csv(RESULTS / "richmond_by_solar_midday.csv", index=False)
    chart_lines(rich, "richmond", "southern solar output, 10:00 to 16:00 (GW)",
                "Richmond: the year matters more than the solar",
                "04_richmond_by_solar.png", xfmt=lambda v: f"{v / 1000:.1f}")

    night = t.hour.isin(NIGHT)
    chi = binned(t, "wind_west", "chicago", 5, night)
    chi.to_csv(RESULTS / "chicago_by_wind_night.csv", index=False)
    chart_lines(chi, "chicago", "western wind output, 22:00 to 07:00 (GW)",
                "Chicago: windy nights are congested nights",
                "05_chicago_by_wind.png")
    chicago_grid(t).to_csv(RESULTS / "chicago_wind_load_grid.csv", index=False)

    profiles = pd.concat({a: t.groupby(["year", "hour"])[f"ev_{a}"].mean().unstack() for a in AREAS})
    profiles.round(3).to_csv(RESULTS / "hourly_profile_by_year.csv")
    means = t[t.month <= 8].groupby("year")[["load_dom", "load_bge", "load_comed", "solar_south", "wind_west", "gen_nuclear"]].mean()
    means.round(0).to_csv(RESULTS / "fundamentals_by_year.csv")

    print(shares[shares.threshold == THRESHOLD].pivot(index="year", columns="area", values="share").round(3))
    print(balt.pivot(index="year", columns="mid", values="mean").round(2))
    print(rich.pivot(index="year", columns="mid", values="mean").round(2))
    print(chi.pivot(index="year", columns="mid", values="mean").round(2))
    print(chicago_grid(t).round(2))
    print(means.round(0))


if __name__ == "__main__":
    main()
