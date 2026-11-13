# cool-dispatch

Picks the departure time and route with the least heat exposure for a field crew, using FortyGuard `temperature_routing`. Before it recommends anything, it checks every slot against an independent forecast (Open-Meteo).

**Who it's for:** an operations manager sending a crew from a yard to a job site, who wants to know when to leave and which way to drive.

## What it does

1. Quotes the cost (`slots × 3,500` credits) and spends nothing without `--yes`.
2. Submits one route per departure slot, then polls the free read tool until each completes.
3. In each slot, picks the option with the lowest `degree_minutes_above_threshold`. It ignores the "Coolest" label, because that option can carry more exposure ([REPORT F03](../../REPORT.md)).
4. Gets the air temperature for the route midpoint and hour from Open-Meteo: the forecast for recent and future dates, the ERA5 archive for older ones.
5. Marks a slot **untrusted** if FortyGuard's route mean is more than 5 °C from the reference. Untrusted slots are never recommended. If every slot fails, it says so and ranks by the reference forecast.
6. Writes a Markdown plan and the raw JSON to `sample-output/`.

## Live run (13 Nov 2026, for 14 Nov)

```text
python src/cool_dispatch.py --from 33.4255,-112.1300 --to 33.4152,-111.9310 --date 2026-11-14 --slots 06:00,09:00,12:00,15:00 --yes
Quote: 4 temperature_routing calls x 3,500 = 14,000 credits (reads are free).
Credits: 965,600 -> 951,600 (spent 14,000)
```

FortyGuard returned 34–42 °C for a November day in Phoenix. The forecast was 13–18 °C, so all four slots were rejected and the plan fell back to the forecast: [sample-output/dispatch-2026-11-14.md](sample-output/dispatch-2026-11-14.md). Without the check, the crew would have been planned around summer heat that doesn't exist ([REPORT F01](../../REPORT.md)).

## Run it

```bash
pip install -r requirements.txt          # Python 3.11+
export FORTYGUARD_API_KEY=...            # see ../../.env.example; never commit it
python src/cool_dispatch.py --from LAT,LON --to LAT,LON --date YYYY-MM-DD --slots 06:00,09:00   # quote only
python src/cool_dispatch.py ... --yes                                                          # spend
python -m unittest discover -s tests -v  # 11 tests, no network, no key
```

The tests use trimmed real FortyGuard responses (`tests/fixtures/`). They cover parsing, picking by exposure over the "Coolest" label, the trust check, falling back when every slot fails, and empty or missing data.

## Files

- `src/planner.py`: pure planning logic (tested).
- `src/fg_client.py`: thin MCP client (Streamable HTTP, Bearer key from the environment).
- `src/reference.py`: Open-Meteo reference temperatures.
- `src/cool_dispatch.py`: the CLI.
