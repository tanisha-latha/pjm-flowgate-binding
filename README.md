# Why PJM Flowgates Bind

When a transmission line in PJM hits its limit, it "binds". Cheap power gets stuck on one side, and prices split by location. Traders make money predicting those price gaps.

This project asks two questions about three PJM flowgates, one near Baltimore, one near Richmond and one near Chicago:

1. **When does each one bind?** Time of day, season, and what load, wind, solar and the generation mix are doing.
2. **Why?** Which fundamentals actually explain it, and which only look like they do.

## Hypothesis

Weather and load explain **which hours** a flowgate binds. They do not explain **how often** it binds. Large step changes in binding frequency look like grid events, such as transmission outages or switching changes, and the practical forecasting question for a desk is whether that event is still on.

## Approach

1. **One clock.** Load and prices are reported hour-ending and other series hour-beginning, so I check the convention of every file before joining anything.
2. **One hourly table.** Binding hours and shadow prices, nodal prices, zonal load, wind, solar and fuel mix, all on the same timestamps.
3. **Hold every pattern to three tests.** It has to hold within each year and not only across them. It needs a named alternative explanation that I try to rule out. Models are fit on an early period and scored on a later one they have not seen.
4. **Scan for step changes.** Find the biggest jumps in daily binding, then check whether load, wind, solar, nuclear output or a generator retirement moved on the same dates.
5. **Trading angle.** Test a simple regime rule against a model: if a flowgate bound for several hours today, does tomorrow's spread pay?

## Data

Public sources only. No proprietary or interview data is in this repository.

- [PJM Data Miner 2](https://dataminer2.pjm.com/): binding constraints, day-ahead and real-time LMPs, hourly load, wind and solar, generation by fuel
- [EIA-860M](https://www.eia.gov/electricity/data/eia860m/): generator inventory and retirements

Raw data is not committed. It is downloaded by the scripts in `src/` into `data/`, which is git-ignored.

## Layout

```
README.md
docs/glossary.md     plain-language definitions (flowgate, shadow price, spread)
src/                 data pull, cleaning, analysis (in progress)
notebooks/           exploration and charts (in progress)
data/                downloaded data, not committed
```

## Status

- [x] Repository and project plan
- [ ] Data pull from PJM Data Miner 2 and EIA
- [ ] Hourly table and timestamp checks
- [ ] Step-change scan
- [ ] Models and trading test
- [ ] Charts and write-up

## Tools

Python, pandas, scikit-learn, Matplotlib.

## Author

Tanisha Mattapalli
