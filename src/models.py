"""How predictable is a congested hour, and where does the skill come from?

Train on everything before SPLIT, score on everything after (data the models never saw).
Two horizons:
  hour ahead - you know the last hour's state
  day ahead  - you only know yesterday; yesterday's weather and load stand in for a forecast
Each model is compared with a baseline that needs no model at all.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import load_table, save, style
from config import AREA_COLOURS, AREAS, GRID, INK, MUTED, RESULTS, SPLIT

FUNDAMENTALS = ["load_rto", "load_dom", "load_bge", "load_peco", "load_comed", "load_aep",
                "wind_west", "wind_midatl", "wind_south", "solar_south", "solar_midatl", "solar_west",
                "gen_nuclear", "gen_gas", "gen_coal"]


def calendar(t):
    hour = pd.get_dummies(t.hour, prefix="h")
    month = pd.get_dummies(t.month, prefix="m")
    weekend = (t.dow >= 5).astype(int).rename("weekend")
    return pd.concat([hour, month, weekend], axis=1).astype(float)


def auc(y, score):
    ok = score.notna() & y.notna()
    return roc_auc_score(y[ok], score[ok])


def fit_score(model, X, y, train, test):
    model.fit(X[train], y[train])
    return pd.Series(model.predict_proba(X[test])[:, 1], index=X.index[test])


def run_area(t, area):
    y = t[f"ev_{area}"].astype(int)
    cal = calendar(t)
    fund = t[FUNDAMENTALS].ffill()
    fund_yday = fund.shift(24)
    ev = t[f"ev_{area}"].astype(float)
    lags_hour = pd.concat({"ev_lag1": ev.shift(1), "ev_lag24": ev.shift(24),
                           "ev_last24": ev.shift(1).rolling(24).mean()}, axis=1)
    lags_day = pd.concat({"ev_lag24": ev.shift(24),
                          "ev_yday_hours": ev.groupby(t.date).transform("sum").shift(24)}, axis=1)

    ok = lags_hour.notna().all(axis=1) & lags_day.notna().all(axis=1) & fund_yday.notna().all(axis=1)
    train = (t.index < SPLIT) & ok
    test = (t.index >= SPLIT) & ok
    yt = y[test]
    lr = lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    gb = lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, random_state=0)

    res = {}
    res[("hour ahead", "baseline: it was congested last hour")] = auc(yt, lags_hour.ev_lag1[test])
    X = pd.concat([cal, fund, lags_hour], axis=1)
    res[("hour ahead", "logistic regression: calendar + fundamentals + recent state")] = auc(
        yt, fit_score(lr(), X, y, train, test))

    res[("day ahead", "baseline: same hour yesterday")] = auc(yt, lags_day.ev_lag24[test])
    res[("day ahead", "calendar only")] = auc(yt, fit_score(lr(), cal, y, train, test))
    X = pd.concat([cal, fund_yday], axis=1)
    res[("day ahead", "boosted trees: calendar + yesterday's fundamentals")] = auc(
        yt, fit_score(gb(), X, y, train, test))
    X = pd.concat([cal, fund_yday, lags_day], axis=1)
    res[("day ahead", "boosted trees: + yesterday's congestion")] = auc(yt, fit_score(gb(), X, y, train, test))
    return res


def chart(df):
    order = list(df.index)
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ypos = np.arange(len(order))[::-1]
    for y, (h, m) in zip(ypos, order):
        vals = df.loc[(h, m)]
        ax.plot([vals.min(), vals.max()], [y, y], color=GRID, lw=3, zorder=1)
    for a in AREAS:
        ax.scatter(df[a].values, ypos, s=60, color=AREA_COLOURS[a], label=a.title(), zorder=3,
                   edgecolor="white", linewidth=1.5)
    ax.set_yticks(ypos, [f"{h}: {m}" for h, m in order], fontsize=8.5)
    ax.axvline(0.5, color=MUTED, lw=0.8, ls=(0, (3, 3)))
    ax.text(0.505, ypos[0] + 0.25, "coin flip", fontsize=8, color=MUTED)
    ax.set_xlim(0.45, 1.0)
    ax.set_ylim(-1.3, len(order) - 0.4)
    ax.set_xlabel(f"AUC on unseen data ({SPLIT[:7]} onward)")
    ax.set_title("Recent congestion predicts the next hour better than weather does")
    ax.legend(loc="lower left", fontsize=8.5, ncol=3, bbox_to_anchor=(0.0, -0.02))
    ax.grid(axis="y", visible=False)
    save(fig, "07_model_auc.png")


def main():
    style()
    t = load_table()
    out = pd.DataFrame({a: run_area(t, a) for a in AREAS})
    out.index.names = ["horizon", "model"]
    out.round(3).to_csv(RESULTS / "model_auc.csv")
    chart(out)
    pd.set_option("display.width", 200)
    print(out.round(3))


if __name__ == "__main__":
    main()
