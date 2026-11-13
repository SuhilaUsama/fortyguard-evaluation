"""Unit tests for the planning logic, using trimmed real FortyGuard responses (stdlib unittest, no network)."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
import planner  # noqa: E402
import reference  # noqa: E402

FOUR = json.loads((HERE / "fixtures" / "phoenix-2026-11-14-0700-four-routes.json").read_text(encoding="utf-8"))
ONLY = json.loads((HERE / "fixtures" / "phoenix-2025-07-15-1400-only-route.json").read_text(encoding="utf-8"))


class ParseAndPick(unittest.TestCase):
    def test_parse_four_routes(self):
        opts = planner.parse_route_read(FOUR)
        self.assertEqual([o.label for o in opts], ["Fastest", "Balanced", "Option 4", "Coolest"])
        self.assertAlmostEqual(opts[0].exposure_deg_min, 64.82)

    def test_best_is_lowest_exposure_not_the_coolest_label(self):
        best = planner.pick_best(planner.parse_route_read(FOUR))
        self.assertEqual(best.label, "Fastest")  # "Coolest" has 67.04 degree-minutes vs 64.82

    def test_coolest_label_contradiction_is_noted(self):
        s = planner.evaluate(planner.Slot("2026-11-14T07:00", planner.parse_route_read(FOUR), 13.0))
        self.assertTrue(any('"Coolest" has more exposure' in n for n in s.notes))


class TrustCheck(unittest.TestCase):
    def test_far_from_reference_is_untrusted(self):
        # Real case: FortyGuard 35.9 C vs Open-Meteo 13.0 C for a November 7 am departure.
        s = planner.evaluate(planner.Slot("2026-11-14T07:00", planner.parse_route_read(FOUR), 13.0))
        self.assertFalse(s.trusted)
        self.assertEqual(s.gap_c, 22.9)

    def test_close_to_reference_is_trusted(self):
        s = planner.evaluate(planner.Slot("2025-07-15T14:00", planner.parse_route_read(ONLY), 40.1))
        self.assertTrue(s.trusted)
        self.assertIn("only one route returned", s.notes)

    def test_missing_reference_is_not_trusted(self):
        s = planner.evaluate(planner.Slot("2025-07-15T14:00", planner.parse_route_read(ONLY), None))
        self.assertFalse(s.trusted)

    def test_empty_route_list(self):
        s = planner.evaluate(planner.Slot("2025-07-15T14:00", [], 30.0))
        self.assertIsNone(s.best)
        self.assertIn("no route returned", s.notes)


class Planning(unittest.TestCase):
    def test_recommends_trusted_slot_with_least_exposure(self):
        hot = planner.Slot("2025-07-15T14:00", planner.parse_route_read(ONLY), 40.1)  # trusted, 161.8
        cool = planner.Slot("2025-07-15T14:00", planner.parse_route_read(FOUR), 34.0)  # trusted, 64.82
        cool.departure = "2025-07-15T06:00"
        p = planner.plan([hot, cool])
        self.assertEqual(p.basis, "fortyguard")
        self.assertEqual(p.recommended.departure, "2025-07-15T06:00")

    def test_never_recommends_untrusted_slot(self):
        bad = planner.Slot("2026-11-14T07:00", planner.parse_route_read(FOUR), 13.0)
        p = planner.plan([bad])
        self.assertEqual(p.basis, "reference-only")
        md = planner.to_markdown(p, "t")
        self.assertIn("failed the sanity check", md)

    def test_no_data(self):
        p = planner.plan([planner.Slot("2026-11-14T07:00", [], None)])
        self.assertEqual(p.basis, "none")
        self.assertIn("No recommendation", planner.to_markdown(p, "t"))


class Reference(unittest.TestCase):
    def test_at_rounds_to_hour(self):
        series = {"2026-11-14T07:00": 13.0}
        self.assertEqual(reference.at(series, "2026-11-14T07:00:00"), 13.0)
        self.assertEqual(reference.at(series, "2026-11-14T07:40"), 13.0)
        self.assertIsNone(reference.at(series, "2026-11-14T08:00"))


if __name__ == "__main__":
    unittest.main()
