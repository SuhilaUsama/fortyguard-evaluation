# Codex recipes for the FortyGuard MCP

A drop-in folder that makes Codex a careful FortyGuard user. It quotes before spending, checks the numbers against an independent source, and avoids the fields that are known to mislead.

## What's inside

| File | Purpose |
|---|---|
| `AGENTS.md` | Project rules Codex reads automatically: quote and confirm before paid calls, US-only coverage, units, mandatory sanity check, rank routes by exposure, don't time work from `heat_index_celsius`. |
| `.agents/skills/fortyguard-cool-route/` | `$fortyguard-cool-route`: coolest departure and route, with a forecast cross-check. |
| `.agents/skills/fortyguard-heat-check/` | `$fortyguard-heat-check`: hourly conditions and the coolest 4-hour work window from `env_params`. |
| `.agents/skills/fortyguard-credits/` | `$fortyguard-credits`: balance and cost quotes. Free. |
| `.codex/config.toml` | MCP server with `bearer_token_env_var`, `required = true`, the key hidden from shell commands, and commented per-tool approvals for headless runs. |
| `sample-runs/` | Four real Codex runs (tool calls and final answers). |

## Use it

```bash
export FORTYGUARD_API_KEY=...       # never put the key in a file
cd demos/codex-recipes
codex                                # trust the project so .codex/config.toml loads
> $fortyguard-credits what would 4 route checks cost?
```

If you don't want to trust the folder, copy the `[mcp_servers.fortyguard]` table into `~/.codex/config.toml`.

**Headless (`codex exec`):** nobody can approve there, so Codex refuses paid tools by default. That's good. Approve only the tool you need for that run:

```bash
codex exec -c 'mcp_servers.fortyguard.tools.env_params.approval_mode="approve"' \
  '$fortyguard-heat-check Tempe 33.4152,-111.9310 on 2025-07-15, day max 42 C. I approve one env_params call.'
```

The forecast cross-check needs network access from Codex's shell. The default read-only sandbox blocks it, and the skill then says it couldn't verify instead of pretending. To allow it, enable network in the sandbox or give a reference temperature in the prompt.

## What the sample runs show

1. [Asks before spending](sample-runs/1-asks-before-spending.md): no cost mentioned in the prompt; Codex quoted 3,500 credits and waited.
2. [Paid call blocked in exec](sample-runs/2-paid-call-blocked-in-exec.md): FortyGuard's `readOnlyHint` annotations drive Codex's approval rules; `temperature_routing` was refused, reads were allowed.
3. [No recipe, bad number passed on](sample-runs/3-no-recipe-trusts-bad-number.md): without these rules, Codex recommended the "Coolest" route at 35.9 °C for a November 7 am in Phoenix (forecast: 13 °C). This is why the cross-check exists.
4. [Heat-check skill](sample-runs/4-heat-check-skill.md): one approved `env_params` call (2,900 credits), hourly table, coolest window 05:00–09:00, the derived heat index deliberately not used, and a clear note that the cross-check couldn't run in the sandbox.

Tested with Codex CLI 0.169.0 and `gpt-5.6-luna` at low reasoning effort.
