---
name: fortyguard-cool-route
description: Use when a user wants the coolest or safest driving route or departure time between two US points with FortyGuard. Quotes the cost, checks the numbers against an independent forecast, and ranks by heat exposure.
---

# FortyGuard cool route

## Inputs
- Origin and destination as `lat,lon` (contiguous US only).
- Local date and one or more departure times. Ask if missing.

## Steps
1. Call `credit_balance` (free).
2. Quote: N departure times x 3,500 credits (`temperature_routing`). Show the exact arguments. Wait for "yes".
3. For each departure, call `temperature_routing` once, with `departure_time` including the UTC offset. Save each `activity_id`.
4. Poll `temperature_routing_read` (free) about every 10 s until `status` is `completed` or `failed`. Never resubmit.
5. For every route option, read `distance_km`, `duration_min`, `thermal.mean_c`, `thermal.peak_c` and `thermal.degree_minutes_above_threshold`.
6. Pick the option with the lowest `degree_minutes_above_threshold` (ties: shorter trip). Say so if that isn't the one labelled "Coolest".
7. Check the numbers: get the air temperature for the route midpoint and departure hour from Open-Meteo (`https://api.open-meteo.com/v1/forecast?latitude=..&longitude=..&hourly=temperature_2m&timezone=auto&start_date=D&end_date=D`, or `archive-api.open-meteo.com/v1/archive` for dates older than about 2 months). If you can't reach it, ask the user for a reference temperature.
8. If FortyGuard's `mean_c` differs from the reference by more than 5 °C, mark the result **untrusted**. Don't recommend it; recommend the departure time that is coolest by the reference instead, and say why.
9. Call `credit_balance` again.

## Output
One line with the recommendation, then a table: departure | route | km | min | FortyGuard mean °C | reference °C | gap | trusted. End with credits spent.
