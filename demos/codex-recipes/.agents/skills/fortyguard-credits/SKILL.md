---
name: fortyguard-credits
description: Use when a user asks about FortyGuard credits, prices, or what a planned set of FortyGuard calls will cost. Free; never calls a paid tool.
---

# FortyGuard credits and quotes

1. Call `credit_balance` (free) and report `available_credits`.
2. For a planned task, list each paid call with the price from that tool's description (they differ by plan; the trace's `plan_type` tells you which plan applies), the count, and the total.
3. Note that `*_read` tools, `credit_balance`, and monitoring `list_monitors` / `list_alerts` are free.
4. Never call a paid tool from this skill.
