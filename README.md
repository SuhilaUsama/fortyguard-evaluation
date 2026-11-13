# FortyGuard: a new customer's evaluation, with Codex

Ziad Osama El-Boshy · Automation Intern application · 13 Nov 2026

Starting from a fresh free trial account, I used the Dashboard and the Temperature MCP the way a customer would, with **Codex CLI** as the agent. Then I built two small things a FortyGuard customer could reuse.

**Read the [report](REPORT.md)** (one page, 11 findings, each with evidence and a fix).

## Top findings

1. **Routing ignores the date.** Tomorrow's routes come back with last July's temperatures, 18–24 °C too hot, with no warning. Codex passed the number straight to the user. ([F01, F02](REPORT.md))
2. **"Coolest" isn't always the least heat.** The route labelled Coolest carried more exposure than Fastest by FortyGuard's own metric. ([F03](REPORT.md))
3. **The free Dashboard account is silently locked to Alabama**, while the same account's API works in Arizona and Texas. ([F07](REPORT.md))

**Works well:** the tool annotations make Codex safe by default (paid calls blocked until approved), Codex quotes the price before spending, and billing matched the docs exactly.

## Demos

| Demo | What it shows |
|---|---|
| [cool-dispatch](demos/cool-dispatch/) | Crew dispatch planner: best departure and route by heat exposure, every slot checked against a forecast. Rejected all four bad slots on the live run. 11 tests. |
| [codex-recipes](demos/codex-recipes/) | `AGENTS.md` + 3 Codex skills + config for using FortyGuard from Codex safely, with 4 real sample runs. |

## Repo layout

```
REPORT.md            findings, strengths, fixes
evidence/            raw responses (key and account details removed), named by finding
demos/cool-dispatch/ Python planner, tests, live sample output
demos/codex-recipes/ AGENTS.md, .agents/skills, .codex/config.toml, sample runs
```

Scope: customer-level use of one trial account only, with nothing touching other users or their data. Total spend: 51,300 of 1,000,000 trial credits, every paid call quoted first.
