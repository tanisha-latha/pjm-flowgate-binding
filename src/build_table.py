"""Join the raw PJM files into one hourly table on one clock.

Every series ends up indexed by hour-beginning, local (prevailing Eastern) time.
LMPs and load are published hour-ending (1-24), so they shift back one hour.
Wind, solar and fuel mix are already hour-beginning (0-23).
See checks.py for how the conventions were confirmed.
"""
import pandas as pd

from config import AREAS, PROCESSED, RAW, ZONES


def hour_beginning(date, hour):
    return pd.to_datetime(date) + pd.to_timedelta(hour, unit="h")


def load_lmps():
    df = pd.read_csv(RAW / "rt_hrl_lmps.csv")
    df["ts"] = hour_beginning(df.opr_date, df.hour_ending - 1)
    cong = df.pivot_table(index="ts", columns="pnode_name", values="congestion_price_rt", aggfunc="mean")
    lmp = df.pivot_table(index="ts", columns="pnode_name", values="total_lmp_rt", aggfunc="mean")
    energy = df.groupby("ts").system_energy_price_rt.mean().rename("energy_price")
    cong.columns = ["cong_" + c for c in cong.columns]
    lmp.columns = ["lmp_" + c for c in lmp.columns]
    return pd.concat([cong, lmp, energy], axis=1)


def load_load():
    df = pd.read_csv(RAW / "hrl_load.csv")
    df = df[df.region_zone.isin(ZONES)]
    df["ts"] = hour_beginning(df.opr_date, df.opr_hour - 1)
    out = df.pivot_table(index="ts", columns="region_zone", values="load_value", aggfunc="mean")
    out.columns = ["load_" + ZONES[c] for c in out.columns]
    return out


def load_area_series(name, col):
    df = pd.read_csv(RAW / f"{name}.csv")
    df["ts"] = hour_beginning(df.opr_date, df.opr_hour)
    out = df.pivot_table(index="ts", columns="area", values=col, aggfunc="mean")
    out.columns = [f"{col.split('_')[0]}_{c.lower()}" for c in out.columns]
    return out


def load_fuel():
    df = pd.read_csv(RAW / "gen_by_fuel.csv")
    df["ts"] = hour_beginning(df.opr_date, df.opr_hour)
    out = df.pivot_table(index="ts", columns="fuel_type", values="mw", aggfunc="mean")
    out.columns = ["gen_" + c.lower().replace(" ", "_") for c in out.columns]
    return out


def build():
    t = pd.concat(
        [load_lmps(), load_load(), load_area_series("wind_gen", "wind_value"),
         load_area_series("solar_gen", "solar_value"), load_fuel()],
        axis=1,
    )
    t = t[t.index.notna()].sort_index()
    t = t[t.filter(like="cong_").notna().any(axis=1)]  # keep hours with prices

    for area, a in AREAS.items():
        t[f"spread_{area}"] = t[f"cong_{a['rich']}"] - t[f"cong_{a['cheap']}"]

    t["hour"] = t.index.hour
    t["month"] = t.index.month
    t["year"] = t.index.year
    t["dow"] = t.index.dayofweek
    t["date"] = t.index.normalize()
    return t


if __name__ == "__main__":
    PROCESSED.mkdir(parents=True, exist_ok=True)
    table = build()
    table.to_csv(PROCESSED / "hourly.csv.gz")
    print(f"{len(table):,} hours, {table.shape[1]} columns, {table.index.min()} to {table.index.max()}")
