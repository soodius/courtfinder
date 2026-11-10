"""Run with:  python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))
from adapters.clubspark import FormatChanged, parse  # noqa: E402

SAMPLE = {
    "MinimumInterval": 60,
    "Resources": [
        {"Name": "Court 1", "Number": 1, "Days": [{
            "Date": "2026-11-12T00:00:00",
            "Sessions": [
                {"Category": 0, "Capacity": 1, "StartTime": 420, "EndTime": 660, "Interval": 60},  # open 7-11
                {"Category": 1000, "Capacity": 0, "StartTime": 480, "EndTime": 540},              # booked 8-9
            ]}]},
        {"Name": "Court 2", "Number": 2, "Days": [{
            "Date": "2026-11-12T00:00:00",
            "Sessions": [
                {"Category": 0, "Capacity": 1, "StartTime": 1080, "EndTime": 1200, "Interval": 60},  # open 18-20
                {"Category": 3, "Capacity": 0, "StartTime": 1110, "EndTime": 1140},                # coaching 18:30-19
            ]}]},
    ],
}


class ParseTests(unittest.TestCase):
    def test_free_slots_skip_bookings(self):
        slots = parse(SAMPLE, lambda d: f"https://x/{d}")
        got = [(s["court"], s["start"]) for s in slots]
        self.assertEqual(got, [("Court 1", "07:00"), ("Court 1", "09:00"),
                               ("Court 1", "10:00"), ("Court 2", "19:00")])
        self.assertEqual(slots[0]["date"], "2026-11-12")
        self.assertEqual(slots[0]["booking_url"], "https://x/2026-11-12")

    def test_real_caroline_chisholm_court1(self):
        # Court 1, Caroline Chisholm Park, 10 Nov 2026 as returned by GetVenueSessions.
        # The live booking sheet and Tennis Australia's Court Finder both showed
        # 16:00 / 16:30 / 17:00 free that afternoon.
        real = {"MinimumInterval": 30, "Resources": [{"Name": "Court 1", "Days": [{
            "Date": "2026-11-10T00:00:00", "Sessions": [
                {"Category": 0, "Capacity": 4, "StartTime": 480, "EndTime": 1020, "Interval": 30},
                {"Category": 0, "Capacity": 4, "StartTime": 1020, "EndTime": 1110, "Interval": 30},
                {"Category": 1000, "Capacity": 0, "StartTime": 1110, "EndTime": 1200, "Interval": 90},
                {"Category": 1000, "Capacity": 0, "StartTime": 1200, "EndTime": 1260, "Interval": 60},
                {"Category": 0, "Capacity": 4, "StartTime": 1260, "EndTime": 1320, "Interval": 30}]}]}]}
        afternoon = [s["start"] for s in parse(real, str) if s["start"] >= "15:45"]
        self.assertEqual(afternoon, ["16:00", "16:30", "17:00", "17:30", "18:00", "21:00", "21:30"])

    def test_unexpected_format_raises(self):
        with self.assertRaises(FormatChanged):
            parse({"something": "else"}, str)


if __name__ == "__main__":
    unittest.main()
