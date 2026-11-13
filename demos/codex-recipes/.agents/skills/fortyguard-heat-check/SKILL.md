---
name: fortyguard-heat-check
description: Use when a user asks how hot it is or was at one US location on a date, or when to schedule outdoor work there, using FortyGuard env_params. Quotes the cost and reports hourly conditions without relying on the derived heat index.
---

# FortyGuard heat check

## Inputs
- A point as `lat,lon` (US only) and a date (2021-01-01 or later, not in the future).
- The day's temperature in °C. `env_params` requires it. Ask the user or take it from a reliable source (Open-Meteo archive daily max). Never invent it.

## Steps
1. Call `credit_balance` (free).
2. Quote `env_params` (2,900 credits on premium, 2,110 on basic/startup; use the price in the tool description). Show the exact arguments: `latitude`, `longitude`, `temperature`, `date_time: {start_date, filter_type: 3}`. Wait for "yes".
3. Call `env_params` once.
4. From the hourly data (`raw`), report for each hour: `apparent_temperature`, `relative_humidity`, `wet_bulb_temperature`.
5. Do **not** use `value.parameters` as the day's summary: for a single day it's the first-hour (midnight) snapshot (`parameters_metadata.basis`). Compute the daily min, mean and max yourself.
6. Do **not** time work from `heat_index_celsius`: it's computed from the one temperature you supplied, applied to all 24 hours. Use `apparent_temperature` for the hottest and coolest hours.
7. Suggest the coolest 4-hour outdoor window between 05:00 and 20:00 by mean apparent temperature.
8. Call `credit_balance` again.

## Output
The recommended window first, then a compact hourly table (05:00-20:00), the daily min/mean/max, and credits spent.
