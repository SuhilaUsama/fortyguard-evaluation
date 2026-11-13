# FortyGuard evaluation report

**Author:** Suhila Usama Ahmed · **Dates:** 13 Nov 2026 · **Client:** Codex CLI 0.169.0 (`gpt-5.6-luna`) and a small Python MCP client · **Spend:** 51,300 of 1,000,000 trial credits (every call quoted first)

I tested FortyGuard as a new customer would: a fresh free trial account, the Dashboard, and the Temperature MCP from Codex. I built two things on top: a crew-dispatch planner and a Codex recipe pack. Everything below has evidence in [`evidence/`](evidence/) or [`demos/`](demos/). I stayed at customer level: one trial account, no load testing, nothing touching other users or their data.

## Summary

The MCP is well built for agents. Its tool annotations work with Codex out of the box: read-only tools run unattended, and paid tools stay blocked until the user approves them. The weak spot is the data behind routing. **Routes for tomorrow come back with last July's temperatures**, and an agent passes that straight to the customer. Onboarding also has a surprise: the Dashboard account is quietly locked to Alabama.

## What works well

- **The annotations do their job in Codex.** In `codex exec`, `credit_balance` and the `*_read` tools ran without prompting, and `temperature_routing` was refused ("MCP tool call requires approval") until I approved that one tool. That is exactly the right default for a paid API. ([sample run 2](demos/codex-recipes/sample-runs/2-paid-call-blocked-in-exec.md))
- **Codex asked before spending**, quoting 3,500 credits from the tool description, before I had said anything about cost. ([sample run 1](demos/codex-recipes/sample-runs/1-asks-before-spending.md))
- **Billing matched the descriptions:** 13 routes × 3,500 and 2 `env_params` × 2,900 = 51,300 credits. Reads were free.
- **Time zones are handled consistently.** `2025-07-15T13:00:00Z` and local `06:00` returned the same route.
- **It's fast.** Connecting and listing tools takes about 2 s, a route submit 4–9 s, and results arrive within a minute.

## Findings

| # | Sev | Finding | Evidence | Suggested fix |
|---|---|---|---|---|
| F01 | **High** | **Routing ignores the date.** A Phoenix route for tomorrow (14 Nov 2026) at 06:00 and 14:00 returns *exactly* the values for 15 Jul 2025 at the same hours (mean 34.315 / 41.819 °C, identical to three decimals). Against the Open-Meteo forecast, tomorrow's four slots are +20.8 to +23.9 °C too hot, and Houston at 07:00 is 28.9 °C vs 10.4 °C forecast. The calls are accepted and charged with no warning. | `F01-*` | Use forecast data for future departures, or reject dates you can't serve. Return the data date and source with every route. |
| F02 | **High** | **An agent passes F01 straight to the customer.** Asked to plan a 7 am crew trip tomorrow, Codex recommended the "Coolest" route at "35.87 °C (96.6 °F)". The forecast is 13 °C. Nothing in the response let the agent notice. | [sample run 3](demos/codex-recipes/sample-runs/3-no-recipe-trusts-bad-number.md) | Fix F01, and add a `warnings` entry when the data isn't for the requested date. |
| F03 | Medium | **"Coolest" can mean more heat exposure.** In the runs that returned 4 options, "Coolest" was 0.03 °C cooler on average but longer, so its `degree_minutes_above_threshold` was **67.0 vs 64.8** for "Fastest". The 32 °C threshold was exceeded for the whole trip in every run, so the minutes figure carries no information. | `F03-F04-*` | Rank and label by exposure, and hide options whose difference is below the model's error. |
| F04 | Medium | **Same trip, different answers.** I ran the same 21 km Phoenix trip 12 times. 10 runs evaluated 6 candidates and returned a single "Only route" (`no_cooling_available`). Only the two 07:00 runs on 14 Nov returned 4 options. No reason is given. | `F01-*`, `F03-F04-*` | Explain why alternatives were dropped (identical geometry, below threshold, and so on). |
| F05 | Medium | **Route temperatures don't follow the day.** On 15 Jul 2025 the 18:00 route reads 34.6 °C, cooler than 10:00 (40.1 °C). ERA5 has 39.7 °C at 18:00 and 36.4 °C at 10:00. A dispatcher would send the crew out at 18:00 thinking it's the cool slot. The UTC and local requests agree, so this isn't a time-zone parsing bug. | `F05-*` | Validate route temperatures against a reanalysis such as ERA5 and publish the expected error. |
| F06 | Medium | **Route results don't say where the numbers come from.** `field` and `metadata` are empty: no source, no data timestamp, no forecast-or-historical flag, no resolution. That's why F01 is invisible to customers and agents. | any `F0*-route-*` | Fill `metadata` with source, data time and model version. |
| F07 | **High** | **The free Dashboard account is locked to Alabama.** The free-key signup asks only for an email, but the profile shows "Subscribed State: Alabama", read-only even in Edit Profile. Choosing Phoenix shows "Location is outside your subscribed state". The API key on the same account works in Arizona and Texas. | `F07-*.png` | Ask for the state at signup (or don't restrict trial accounts), let users change it, and use the same rule in the Dashboard and the API. |
| F08 | Medium | **"Free plan" is billed at Premium prices.** The welcome email says "Free plan (no billing required)", but the account is `plan_type: Premium`, which has the highest per-call prices (`env_params` 2,900 vs 2,110; heatmap 4,220 vs 3,500). The key and credits also expire after 7 days (19 Nov), which the email doesn't mention. | `F08-*` | Name the trial plan honestly and show its expiry in the email. |
| F09 | Medium | **The welcome email contains the Dashboard password in plain text**, right next to the API key. | (email, not published) | Send a set-password link instead, and show the key once in the Dashboard. |
| F10 | Low | **The Dashboard doesn't see API usage.** Usage → Routes showed 0/30 after 13 MCP routes that day, and the Dashboard shows no credit balance anywhere. The usage endpoint's `activity_breakdown` lists only the 5,800 `env_params` credits out of 51,300 spent. | `F10-*`, dashboard | One usage view covering both, with routing itemised. |
| F11 | Low | **Typing coordinates into "Go to" stacked 8 identical warning toasts**, one per keystroke. | dashboard | Debounce, and show one inline message. |

## Demos

- **[cool-dispatch](demos/cool-dispatch/)**: picks the departure time and route with the least heat exposure for a field crew. It quotes the cost first, ranks by exposure rather than labels, and checks every slot against an independent forecast. On the live run for tomorrow it rejected all four FortyGuard slots (gaps of +21 to +24 °C) and fell back to the forecast instead of sending the crew out on bad numbers. 11 unit tests, built on real responses.
- **[codex-recipes](demos/codex-recipes/)**: `AGENTS.md` rules, three Codex skills (`$fortyguard-cool-route`, `$fortyguard-heat-check`, `$fortyguard-credits`) and a project config with per-tool approvals. The rules also cover two older `env_params` issues: `heat_index_celsius` is computed from the one temperature you supply, and the single-day summary is the midnight value. The heat-check skill ran live: one approved call, 2,900 credits, hourly table and work window.

## Setup notes for Codex users

- Codex older than about 0.150 couldn't load the current model list for a ChatGPT sign-in. Every model was refused until I updated to 0.169.0.
- `bearer_token_env_var` keeps the key out of `config.toml`. Add `shell_environment_policy.exclude` so shell commands Codex runs can't read it.
- In `codex exec`, approve paid tools one by one with `mcp_servers.fortyguard.tools.<tool>.approval_mode = "approve"`. Don't use the sandbox bypass flag to get MCP calls through.
