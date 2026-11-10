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

    def test_unexpected_format_raises(self):
        with self.assertRaises(FormatChanged):
            parse({"something": "else"}, str)


if __name__ == "__main__":
    unittest.main()
