"""Run with:  python -m unittest discover tests

Fixtures are trimmed copies of real responses captured on 2026-11-10."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scraper"))
from adapters import perfectmind  # noqa: E402
from discover import to_venues  # noqa: E402


def fixture(name):
    return json.loads((HERE / "fixtures" / name).read_text())


class PerfectMindTests(unittest.TestCase):
    def test_parse_real_shape(self):
        slots = perfectmind.parse(fixture("perfectmind_lane1.json"), "Lane 1", lambda d: f"link/{d}")
        got = [(s["date"], s["start"], s["end"]) for s in slots]
        self.assertEqual(got, [("2026-11-10", "16:00", "17:00"), ("2026-11-10", "16:30", "17:30"),
                               ("2026-11-10", "20:30", "21:30"), ("2026-11-11", "09:00", "10:00")])
        self.assertEqual(slots[0]["court"], "Lane 1")
        self.assertEqual(slots[0]["booking_url"], "link/2026-11-10")

    def test_landing_url_has_date(self):
        v = {"host": "h", "org": "1", "widget_id": "w", "calendar_id": "c"}
        self.assertIn("arrivalDate=2026-11-12", perfectmind.landing_url(v, "f", "2026-11-12"))

    def test_bad_response(self):
        with self.assertRaises(perfectmind.FormatChanged):
            perfectmind.parse({"success": False}, "Lane 1", str)


class DiscoverTests(unittest.TestCase):
    def test_to_venues(self):
        vs = {v["id"]: v for v in to_venues(fixture("ta_search.json"))}
        cc = vs["caroline-chisholm-park-tennis-courts"]
        self.assertEqual((cc["platform"], cc["host"], cc["slug"]),
                         ("clubspark", "play.tennis.com.au", "CarolineChisholmParkTennisCourts"))
        self.assertEqual(cc["suburb"], "Winston Hills")
        stan = vs["blacktown-tennis-centre-stanhope"]
        self.assertEqual(stan["platform"], "link_only")
        self.assertIn("perfectgym", stan["booking_url"])


if __name__ == "__main__":
    unittest.main()
