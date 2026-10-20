import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config import AREAS, CHARTS, GRID, INK, MUTED, PROCESSED, SURFACE, THRESHOLD


def load_table(threshold=THRESHOLD):
    t = pd.read_csv(PROCESSED / "hourly.csv.gz", index_col=0, parse_dates=True)
    t["date"] = pd.to_datetime(t["date"])
    events = pd.DataFrame({f"ev_{a}": t[f"spread_{a}"] > threshold for a in AREAS}, index=t.index)
    return pd.concat([t, events], axis=1)


def style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "axes.titlecolor": INK,
        "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.major.size": 0, "ytick.major.size": 0,
        "legend.frameon": False, "lines.linewidth": 2, "axes.axisbelow": True,
    })


def save(fig, name, source="Source: PJM Data Miner 2 (rt_hrl_lmps, hrl_load_metered, wind_gen, solar_gen, gen_by_fuel)"):
    fig.text(0.01, -0.02, source, fontsize=7.5, color=MUTED, ha="left", va="top")
    CHARTS.mkdir(exist_ok=True)
    fig.savefig(CHARTS / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def pct(ax, axis="y"):
    from matplotlib.ticker import PercentFormatter
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(PercentFormatter(1.0, decimals=0))
