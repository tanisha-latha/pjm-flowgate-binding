# Clock checks

## 1. Missing hour on spring-forward days

- rt_hrl_lmps: missing {'2024-03-10': [3], '2025-03-09': [3], '2026-03-08': [3]} -> hour-ending
- hrl_load: missing {'2024-03-10': [3], '2025-03-09': [3], '2026-03-08': [3]} -> hour-ending
- wind_gen: missing {'2024-03-10': [2], '2025-03-09': [2], '2026-03-08': [2]} -> hour-beginning
- solar_gen: missing {'2024-03-10': [2], '2025-03-09': [2], '2026-03-08': [2]} -> hour-beginning
- gen_by_fuel: missing {'2024-03-10': [2], '2025-03-09': [2], '2026-03-08': [2]} -> hour-beginning

## 2. Lag check after alignment (correlation)

- RTO load vs system energy price: -2h: 0.414, -1h: 0.435, +0h: 0.447, +1h: 0.439, +2h: 0.411 (best at +0h)
- solar feed vs fuel-mix solar: -2h: 0.833, -1h: 0.959, +0h: 0.998, +1h: 0.929, +2h: 0.785 (best at +0h)
