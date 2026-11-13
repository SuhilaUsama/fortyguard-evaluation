"""cool-dispatch: pick the departure slot and route with the least heat exposure for a field crew.

    python src/cool_dispatch.py --from 33.4255,-112.1300 --to 33.4152,-111.9310 \
        --date 2026-11-14 --slots 06:00,09:00,12:00,15:00            # quote only, no spend
    python src/cool_dispatch.py ... --yes                              # run (spends credits)
    python src/cool_dispatch.py ... --replay sample-output/<run>.json  # re-plan saved results, no network to FortyGuard

Every slot is checked against an independent forecast (Open-Meteo). A slot whose FortyGuard
route temperature is far from the reference is marked untrusted and never recommended.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planner  # noqa: E402
import reference  # noqa: E402


def latlon(s: str) -> tuple[float, float]:
    a, b = s.split(",")
    return float(a), float(b)


async def fetch(args, departures: list[str]) -> dict:
    import fg_client
    async with fg_client.connect() as fg:
        before = await fg.balance()
        ids = {d: await fg.submit_route(args.origin, args.dest, d) for d in departures}
        routes = {d: await fg.read_route(i) for d, i in ids.items()}
        after = await fg.balance()
    return {"activity_ids": ids, "routes": routes, "credits_before": before, "credits_after": after}


def build_plan(raw: dict, args, departures: list[str]) -> planner.Plan:
    mid = ((args.origin[0] + args.dest[0]) / 2, (args.origin[1] + args.dest[1]) / 2)
    ref = raw.get("reference") or reference.hourly_air_temp(mid[0], mid[1], args.date)
    raw["reference"] = ref
    slots = [planner.Slot(d, planner.parse_route_read(raw["routes"][d]), reference.at(ref, d)) for d in departures]
    return planner.plan(slots, args.max_gap)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="origin", type=latlon, required=True)
    ap.add_argument("--to", dest="dest", type=latlon, required=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD, local date at the route")
    ap.add_argument("--slots", default="06:00,09:00,12:00,15:00", help="local departure times")
    ap.add_argument("--max-gap", type=float, default=planner.DEFAULT_MAX_GAP_C)
    ap.add_argument("--yes", action="store_true", help="confirm the quoted spend")
    ap.add_argument("--replay", type=Path, help="saved run JSON to re-plan without calling FortyGuard")
    ap.add_argument("--out", type=Path, default=Path("sample-output"))
    args = ap.parse_args(argv)
    departures = [f"{args.date}T{s.strip()}:00" for s in args.slots.split(",")]

    if args.replay:
        raw = json.loads(args.replay.read_text(encoding="utf-8"))
    else:
        import fg_client
        cost = len(departures) * fg_client.ROUTE_PRICE
        print(f"Quote: {len(departures)} temperature_routing calls x {fg_client.ROUTE_PRICE:,} = {cost:,} credits "
              f"(reads are free). Departures: {', '.join(d[11:16] for d in departures)} local on {args.date}.")
        if not args.yes:
            print("Nothing spent. Re-run with --yes to confirm.")
            return 0
        raw = asyncio.run(fetch(args, departures))
        print(f"Credits: {raw['credits_before']:,} -> {raw['credits_after']:,} "
              f"(spent {raw['credits_before'] - raw['credits_after']:,})")

    p = build_plan(raw, args, departures)
    md = planner.to_markdown(p, f"Crew dispatch {args.date}: {args.origin} -> {args.dest}")
    print(md)
    if not args.replay:
        args.out.mkdir(parents=True, exist_ok=True)
        stem = f"dispatch-{args.date}"
        raw["inputs"] = {"from": args.origin, "to": args.dest, "date": args.date, "slots": args.slots}
        (args.out / f"{stem}.json").write_text(json.dumps(raw, indent=1), encoding="utf-8")
        (args.out / f"{stem}.md").write_text(md, encoding="utf-8")
        print(f"Saved {args.out / stem}.json and .md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
