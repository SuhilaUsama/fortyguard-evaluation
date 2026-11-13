"""Pure planning logic for cool-dispatch (no network, fully unit-tested).

Input: FortyGuard temperature_routing_read results for several departure slots, plus an
independent reference air temperature per slot (Open-Meteo). Output: a ranked plan with a
trust check per slot, so a dispatcher never acts on numbers that fail a basic sanity test.
"""
from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_MAX_GAP_C = 5.0  # FortyGuard route mean vs reference air temperature


@dataclass
class RouteOption:
    label: str
    distance_km: float
    duration_min: float
    mean_c: float
    peak_c: float
    exposure_deg_min: float  # degree-minutes above threshold, FortyGuard's own exposure metric
    threshold_c: float


@dataclass
class Slot:
    departure: str  # ISO local wall time, e.g. 2026-11-14T07:00
    options: list[RouteOption]
    reference_c: float | None  # Open-Meteo air temperature at departure, None if unavailable
    best: RouteOption | None = None
    gap_c: float | None = None
    trusted: bool = False
    notes: list[str] = field(default_factory=list)


def parse_route_read(value: dict) -> list[RouteOption]:
    """Turn the `value` object of a completed temperature_routing_read into RouteOptions."""
    out = []
    for feat in value.get("routes", []):
        p = feat["properties"]
        t = p["thermal"]
        out.append(RouteOption(
            label=p.get("label", "?"),
            distance_km=p["distance_km"],
            duration_min=p["duration_min"],
            mean_c=t["mean_c"],
            peak_c=t["peak_c"],
            exposure_deg_min=t["degree_minutes_above_threshold"],
            threshold_c=t["threshold_c"],
        ))
    return out


def pick_best(options: list[RouteOption]) -> RouteOption:
    """Lowest heat exposure wins; ties go to the shorter trip.

    Deliberately ignores FortyGuard's labels: a route labelled "Coolest" can carry more
    exposure than "Fastest" because it is longer.
    """
    return min(options, key=lambda o: (round(o.exposure_deg_min, 2), o.duration_min))


def evaluate(slot: Slot, max_gap_c: float = DEFAULT_MAX_GAP_C) -> Slot:
    if not slot.options:
        slot.notes.append("no route returned")
        return slot
    slot.best = pick_best(slot.options)
    labelled = [o for o in slot.options if o.label.lower() == "coolest"]
    if labelled and labelled[0] is not slot.best:
        slot.notes.append(
            f'"Coolest" has more exposure ({labelled[0].exposure_deg_min:.1f}) than '
            f'{slot.best.label} ({slot.best.exposure_deg_min:.1f}); using {slot.best.label}')
    if len(slot.options) == 1:
        slot.notes.append("only one route returned")
    if slot.reference_c is None:
        slot.notes.append("no reference temperature; cannot check")
        return slot
    slot.gap_c = round(slot.best.mean_c - slot.reference_c, 1)
    slot.trusted = abs(slot.gap_c) <= max_gap_c
    if not slot.trusted:
        slot.notes.append(
            f"FortyGuard {slot.best.mean_c:.1f} C vs reference {slot.reference_c:.1f} C "
            f"(gap {slot.gap_c:+.1f} C > {max_gap_c:.0f} C): not trusted")
    return slot


@dataclass
class Plan:
    slots: list[Slot]
    recommended: Slot | None
    basis: str  # "fortyguard" | "reference-only" | "none"


def plan(slots: list[Slot], max_gap_c: float = DEFAULT_MAX_GAP_C) -> Plan:
    for s in slots:
        evaluate(s, max_gap_c)
    trusted = [(s, s.best) for s in slots if s.trusted and s.best is not None]
    if trusted:
        rec = min(trusted, key=lambda sb: (round(sb[1].exposure_deg_min, 2), sb[1].mean_c))[0]
        return Plan(slots, rec, "fortyguard")
    with_ref = [(s, s.reference_c) for s in slots if s.reference_c is not None and s.best is not None]
    if with_ref:
        return Plan(slots, min(with_ref, key=lambda sr: sr[1])[0], "reference-only")
    return Plan(slots, None, "none")


def to_markdown(p: Plan, title: str) -> str:
    lines = [f"# {title}", ""]
    r = p.recommended
    if p.basis == "fortyguard" and r is not None and r.best is not None and r.reference_c is not None:
        lines.append(f"**Leave at {r.departure[11:16]}** via {r.best.label}: "
                     f"{r.best.distance_km:.1f} km, {r.best.duration_min:.0f} min, "
                     f"route mean {r.best.mean_c:.1f} C (checked against reference {r.reference_c:.1f} C).")
    elif p.basis == "reference-only" and r is not None and r.reference_c is not None:
        lines.append(f"**FortyGuard numbers failed the sanity check for every slot.** Ranking falls back to "
                     f"the reference forecast: coolest departure {r.departure[11:16]} ({r.reference_c:.1f} C). "
                     "Treat route temperatures below as unreliable.")
    else:
        lines.append("**No recommendation:** no slot had both a route and a reference temperature.")
    lines += ["", "| Departure | Route used | km | min | FortyGuard mean C | Reference C | Gap C | Trusted | Notes |",
              "|---|---|---|---|---|---|---|---|---|"]
    for s in p.slots:
        b = s.best
        lines.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            s.departure[11:16], b.label if b else "-", f"{b.distance_km:.1f}" if b else "-",
            f"{b.duration_min:.0f}" if b else "-", f"{b.mean_c:.1f}" if b else "-",
            "-" if s.reference_c is None else f"{s.reference_c:.1f}",
            "-" if s.gap_c is None else f"{s.gap_c:+.1f}", "yes" if s.trusted else "no",
            "; ".join(s.notes) or ""))
    return "\n".join(lines) + "\n"
