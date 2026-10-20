"""Find the dates where congestion jumped, then check whether any fundamental moved with it.

For each area: daily share of congested hours, compare the 21 days after each
date with the 21 days before, and keep the largest jumps at least 45 days apart.
On each jump date, compare load, wind, solar and nuclear before vs after, and
list EIA-860M retirements within 60 miles in the 45 days around it.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import load_table, pct, save, style
from config import AREA_COLOURS, AREAS, CITIES, INK, MUTED, RADIUS_MILES, RAW, RESULTS, SURFACE

WINDOW = 21
GAP = 45
TOP = 3
DRIVERS = {
    "baltimore": ["load_dom", "load_bge", "wind_west", "solar_south", "gen_nuclear"],
    "richmond": ["load_dom", "solar_south", "wind_west", "gen_nuclear"],
    "chicago": ["load_comed", "wind_west", "solar_west", "gen_nuclear"],
}


def daily_share(t):
    return t.groupby("date")[[f"ev_{a}" for a in AREAS]].mean().rename(columns=lambda c: c[3:])


def find_jumps(s):
    before = s.rolling(WINDOW).mean()
    after = s[::-1].rolling(WINDOW).mean()[::-1].shift(-1)
    jump = (after - before.shift(1)).dropna()
    picked = []
    for d, v in jump.sort_values(ascending=False).items():
        if all(abs((d - p).days) >= GAP for p, _ in picked):
            picked.append((d, v))
        if len(picked) == TOP:
            break
    return picked


def miles(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 3958.8 * 2 * np.arcsin(np.sqrt(a))


def retirements():
    r = pd.read_excel(RAW / "eia860m_aug2026.xlsx", sheet_name="Retired", header=2)
    r = r[pd.to_numeric(r["Retirement Year"], errors="coerce") >= 2023].copy()
    r["date"] = pd.to_datetime(dict(year=r["Retirement Year"].astype(int), month=r["Retirement Month"].astype(int), day=1))
    r["lat"] = pd.to_numeric(r["Latitude"], errors="coerce")
    r["lon"] = pd.to_numeric(r["Longitude"], errors="coerce")
    r["mw"] = pd.to_numeric(r["Net Summer Capacity (MW)"], errors="coerce")
    return r.dropna(subset=["lat", "lon"])


def explain(row):
    """Crude label: did an obvious fundamental move enough to explain the jump?"""
    load = row.get("load_comed_change_pct") if row["area"] == "chicago" else row.get("load_dom_change_pct")
    if row["area"] == "chicago" and row.get("wind_west_change_pct", 0) >= 30:
        return "wind up"
    if load is not None and load >= 10:
        return "load up"
    return "not load or wind"


def main():
    style()
    t = load_table()
    daily = daily_share(t)
    dvals = t.groupby("date")[sorted({c for v in DRIVERS.values() for c in v})].mean()
    ret = retirements()

    rows, near = [], []
    for area in AREAS:
        lat, lon = CITIES[area]
        r_area = ret[miles(lat, lon, ret.lat, ret.lon) <= RADIUS_MILES]
        for d, v in find_jumps(daily[area]):
            pre = slice(d - pd.Timedelta(days=WINDOW), d - pd.Timedelta(days=1))
            post = slice(d, d + pd.Timedelta(days=WINDOW - 1))
            row = {"area": area, "date": d.date(), "share_before": daily[area][pre].mean(),
                   "share_after": daily[area][post].mean()}
            for c in DRIVERS[area]:
                b, a = dvals[c][pre].mean(), dvals[c][post].mean()
                row[f"{c}_before"], row[f"{c}_after"] = round(b), round(a)
                row[f"{c}_change_pct"] = round(100 * (a / b - 1), 1) if b else np.nan
            close = r_area[(r_area.date - d).abs() <= pd.Timedelta(days=GAP)]
            row["retired_mw_within_45d"] = round(close.mw.sum())
            rows.append(row)
            near += [{"area": area, "jump_date": d.date(), "plant": p, "mw": m, "retired": rd.strftime("%Y-%m")}
                     for p, m, rd in zip(close["Plant Name"], close.mw, close.date)]

    out = pd.DataFrame(rows)
    out["explained_by"] = out.apply(explain, axis=1)
    out.to_csv(RESULTS / "step_changes.csv", index=False)
    pd.DataFrame(near, columns=["area", "jump_date", "plant", "mw", "retired"]).to_csv(
        RESULTS / "step_change_retirements.csv", index=False)

    fig, axes = plt.subplots(3, 1, figsize=(10, 7.5), sharex=True)
    for ax, area in zip(axes, AREAS):
        s = daily[area].rolling(7, min_periods=4).mean()
        ax.plot(s.index, s.values, color=AREA_COLOURS[area], lw=1.6)
        ax.set_title(AREAS[area]["label"], fontsize=10)
        pct(ax)
        ax.set_ylim(0, 1)
        jumps = out[out.area == area].sort_values("date")
        for i, (d, why) in enumerate(zip(jumps.date, jumps.explained_by)):
            d = pd.Timestamp(d)
            odd = why == "not load or wind"
            ax.axvline(d, color=INK if odd else MUTED, lw=1.1 if odd else 0.9, ls="-" if odd else (0, (3, 3)))
            ax.text(d, 0.97 - 0.14 * i, f" {d:%d %b %Y}: {why}", fontsize=8, color=INK, va="top",
                    fontweight="bold" if odd else "normal",
                    bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1, alpha=0.85))
    axes[1].set_ylabel("share of hours congested (7-day average)")
    fig.suptitle("Congestion moves in steps: the three biggest jumps in each area", x=0.01, ha="left",
                 fontweight="bold", color=INK)
    fig.tight_layout()
    save(fig, "06_step_changes.png",
         source="Source: PJM Data Miner 2. Lines mark the largest 21-day before/after jumps, at least 45 days apart. "
                "Solid = load and wind did not move enough to explain it.")

    pd.set_option("display.width", 250)
    print(out.to_string())
    print(pd.DataFrame(near).to_string())


if __name__ == "__main__":
    main()
