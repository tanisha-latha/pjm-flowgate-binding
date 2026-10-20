# Why PJM Flowgates Bind

When a transmission line in PJM hits its limit, it binds. Cheap power gets stuck on one side, prices split by location, and the gap between them is the spread a trading desk tries to predict.

This project looks at three congested areas of PJM, around Baltimore, Richmond and Chicago, using only public PJM data, and asks two things:

1. **When** is each area congested?
2. **Why?** Which fundamentals actually explain it, and which only look like they do?

**Short answer:** weather and load explain *which hours* an area is congested. They don't fully explain *how often*. Comparing January to August of each year, all three areas were far more congested in 2026 than in 2024 while western wind barely changed, and some of the biggest jumps happened with flat or falling load. For a desk, recent congestion is a better predictor than the weather, and a simple "it was congested today, so take tomorrow's spread" rule holds up on data the analysis never trained on.

## How congestion is measured

Each area is a pair of pricing nodes on either side of the congestion. The spread is the difference in their real-time congestion prices, and an hour counts as congested when the spread is above $10/MWh.

| Area | Expensive side | Cheap side | Power is trying to flow |
|---|---|---|---|
| Baltimore | BGE | PECO | south into BGE |
| Richmond | Dominion | SOUTH interface | north out of the Southeast |
| Chicago | Western Hub | ComEd | east out of northern Illinois |

A spread between two nodes picks up every constraint between them, not one named flowgate. That makes it a public, reproducible stand-in for flowgate binding, and the same pattern holds at $5 and $20 thresholds (`results/congested_share_by_year.csv`).

## Method

1. **One clock.** PJM publishes LMPs and load hour-ending and wind, solar and fuel mix hour-beginning. I confirmed each file's convention two ways before joining anything: which hour disappears on spring-forward days, and whether series that should move together line up at zero lag. ([results/clock_checks.md](results/clock_checks.md))
2. **One hourly table.** 23,373 hours from January 2024 to August 2026: congestion at 46 pricing nodes, zonal load, wind and solar by region, and generation by fuel.
3. **Hold every pattern within a year.** Congestion rose a lot over the period, so pooling years makes anything that also trended up look like a cause.
4. **Look for step changes.** Find the largest jumps in daily congestion, then check whether load, wind, solar, nuclear output or a nearby generator retirement moved on the same dates.
5. **Test on unseen data.** Models are trained before September 2025 and scored on the twelve months after, against baselines that need no model.

## Findings

### Congestion jumped in 2026 in all three areas

![Share of congested hours by year](charts/01_congested_share_by_year.png)

Comparing January to August of each year, Baltimore was flat from 2024 to 2025 (26%, then 25%) and jumped to 40% in 2026. Richmond and Chicago rose each year. Over the same months, Dominion load rose 16%, southern solar 36% and western wind 6%. ([results/fundamentals_by_year.csv](results/fundamentals_by_year.csv))

### Each area has its own hours

![Congestion by hour and month](charts/02_hour_month_heatmaps.png)

Baltimore is congested on summer and September evenings and winter mornings. Richmond peaks in the afternoon. Chicago is congested at night, mostly in winter, spring and October.

### Baltimore: load explains the hour, not the whole level

![Baltimore congestion by load](charts/03_baltimore_by_load.png)

More Dominion and BGE load means more congestion in every year. In 2024 the lowest-load hours were congested 8% of the time and the highest-load hours 65%. But the low-load floor rose to 19% in 2025 and 21% in 2026, so something besides load made the line tighter.

### Richmond: solar sets the hour, the year sets the level

![Richmond congestion by solar](charts/04_richmond_by_solar.png)

Within a year, more southern solar barely changes midday congestion. In 2025 it sits between 23% and 30% across every solar bin. The jump between years is much bigger than anything solar explains.

### Chicago: windy nights, and more of them congested each year

![Chicago congestion by wind](charts/05_chicago_by_wind.png)

At night, the windiest hours are congested 36% to 51% of the time, against 9% to 14% for the calmest. Load barely matters at night ([results/chicago_wind_load_grid.csv](results/chicago_wind_load_grid.csv)). At the same wind level, around 3 GW, congestion went from 14% in 2024 to 31% in 2025 and 38% in 2026, while average western wind rose only 6%.

### Congestion moves in steps, and not every step is weather

![Step changes](charts/06_step_changes.png)

Of the nine biggest jumps, six line up with an obvious fundamental: winter cold snaps that pushed load up 13% to 22%, and an October 2025 wind ramp in the west. Three don't:

| Area | Date | Congested before | After | Load change |
|---|---|---|---|---|
| Baltimore | 14 Sep 2025 | 18% | 69% | Dominion load -0.4% |
| Richmond | 17 Sep 2025 | 4% | 34% | Dominion load +0.6% |
| Baltimore | 8 Mar 2026 | 19% | 62% | Dominion load -8%, wind +25% |

No generator retirement of any size happened within 60 miles of those dates (EIA-860M). The two September jumps coincide with a 6 to 7% dip in PJM nuclear output, which is fall refueling season, so that is one candidate. A transmission outage or switching change is the other, and PJM's outage history is what would tell them apart. ([results/step_changes.csv](results/step_changes.csv))

### Recent congestion predicts better than the weather

![Model AUC](charts/07_model_auc.png)

Scored on September 2025 onward:

- **Hour ahead:** "it was congested last hour" alone scores an AUC of 0.83 to 0.84. A logistic regression adding calendar, fundamentals and recent state reaches 0.90 to 0.91.
- **Day ahead:** the calendar alone scores 0.64 to 0.66. Adding yesterday's weather and load as a stand-in forecast reaches 0.66 to 0.73. Adding yesterday's congestion lifts it to 0.70 to 0.77.

([results/model_auc.csv](results/model_auc.csv))

### Bet on the regime, not the hour

![Regime rule](charts/08_regime_rule.png)

**Rule:** if an area was congested for six or more hours today, take tomorrow's spread.

| Area | Congested again tomorrow | Tomorrow's avg spread after a 6+ hour day | After a quiet day | Test period only (Sep 2025 on) |
|---|---|---|---|---|
| Baltimore | 95% | $26 | $5 | $34 vs $11 |
| Richmond | 89% | $34 | $3 | $46 vs $6 |
| Chicago | 92% | $20 | $2 | $27 vs $5 |

The six-hour cutoff isn't tuned. The gap grows steadily at 1, 3, 6 and 12 hours. ([results/regime_rule.csv](results/regime_rule.csv))

## Limits

- No outage, import or forecast data, so the unexplained jumps are flagged, not explained.
- Spreads between nodes capture every constraint between them, not a single named flowgate.
- The trading test uses real-time prices with no costs. I haven't tested it against day-ahead prices, which is where the market would already price some of this.
- Hourly averages hide five-minute congestion.

## Next

1. Pull PJM's transmission outage history for the three unexplained jump dates.
2. Add day-ahead LMPs and test the rule against the day-ahead spread.
3. Repeat with PJM's published binding-constraint data for named flowgates.

## Run it

```
pip install -r requirements.txt
python run_all.py
```

Put the raw files in `data/raw/` first (not committed). All of it is public:

| File | Source | Feed |
|---|---|---|
| `rt_hrl_lmps.csv` | PJM Data Miner 2 | real-time hourly LMPs |
| `hrl_load.csv` | PJM Data Miner 2 | hourly metered load |
| `wind_gen.csv` | PJM Data Miner 2 | wind generation |
| `solar_gen.csv` | PJM Data Miner 2 | solar generation |
| `gen_by_fuel.csv` | PJM Data Miner 2 | generation by fuel type |
| `eia860m_aug2026.xlsx` | [EIA-860M](https://www.eia.gov/electricity/data/eia860m/) | generator inventory, August 2026 |

The expected columns are listed at the top of each loader in `src/build_table.py`.

```
src/config.py         areas, nodes, thresholds, train/test split
src/build_table.py    raw files -> one hourly table on one clock
src/checks.py         hour-label checks
src/explore.py        congestion by year, hour, month, load, solar, wind
src/step_changes.py   biggest jumps and what moved with them
src/models.py         hour-ahead and day-ahead models vs baselines
src/regime.py         the 6-hour rule
results/              tables behind every number above
charts/               the charts above
docs/glossary.md      plain-language definitions
```

Python, pandas, scikit-learn, Matplotlib.

## Author

Tanisha Mattapalli
