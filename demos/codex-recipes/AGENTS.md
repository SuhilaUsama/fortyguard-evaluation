# FortyGuard rules for Codex (project instructions)

These apply to every task in this folder that uses the `fortyguard` MCP server.

## Spending
- Every paid FortyGuard call costs credits. Before any paid call, show the tool, the exact arguments and the price stated in the tool description, then wait for the user's "yes". The user saying "find X" is not approval.
- Call `credit_balance` (free) before and after paid work and report the difference.
- Never resubmit a job that is still processing. Poll the `*_read` tool instead (reads are free).
- Stop after the number of paid calls the user approved.

## Inputs
- Coverage is the contiguous United States only. Refuse other locations without calling a tool.
- Units differ by tool: `env_params.temperature` is Celsius, `report.temperature` is Fahrenheit. Convert and say so.
- `env_params` and `report` need a temperature from the user or a reliable source. Never invent one.
- Pass `departure_time` with an explicit UTC offset (for Phoenix, `-07:00`).

## Checking the answer (required)
FortyGuard can return numbers that look fine but are wrong. Before you present a temperature:
1. Compare it with an independent source for the same place and hour (Open-Meteo forecast or archive, or a value the user gives you).
2. If they differ by more than 5 °C, say so first, show both numbers, and do not recommend an action from the FortyGuard number alone.
3. For routes, rank options by `thermal.degree_minutes_above_threshold` (heat exposure), not by the "Coolest" label. A longer "Coolest" route can carry more exposure.
4. For `env_params`, don't time outdoor work from `heat_index_celsius`: it is derived from the single temperature you supplied for every hour. Use the hourly `apparent_temperature` instead.

## Output
- Lead with the recommendation, then a short table, then the credits spent.
- Never print or store the API key.
