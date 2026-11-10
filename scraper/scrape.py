"""Scrape every venue in venues.json and write site/data/availability.json.

    python scraper/scrape.py            # live scrape
    python scraper/scrape.py --demo     # write made-up sample data (for trying the site)

A venue that fails keeps its last good data (marked stale) so one broken site
never blanks the whole app.
"""
import argparse
import json
import random
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from adapters import ADAPTERS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VENUES = ROOT / "venues.json"
OUT = ROOT / "site" / "data" / "availability.json"
POLITE_DELAY_S = 2  # pause between venues so we never hammer a booking site


def load_previous() -> dict:
    try:
        return {v["id"]: v for v in json.loads(OUT.read_text())["venues"]}
    except Exception:
        return {}


def demo_slots(venue: dict, start: date, days: int) -> list[dict]:
    rnd = random.Random(venue["id"])
    out = []
    for d in range(days):
        day = (start + timedelta(days=d)).isoformat()
        for court in ("Court 1", "Court 2", "Court 3"):
            for h in range(7, 22):
                if rnd.random() < (0.3 if 17 <= h <= 20 else 0.6):
                    out.append({"date": day, "start": f"{h:02d}:00", "end": f"{h + 1:02d}:00",
                                "court": court, "booking_url": venue.get("booking_url", "#")})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()

    cfg = json.loads(VENUES.read_text())
    days = int(cfg.get("days_ahead", 7))
    start = date.today()
    end = start + timedelta(days=days - 1)
    previous = load_previous()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    results, failures = [], 0
    for i, v in enumerate(cfg["venues"]):
        info = {k: v.get(k) for k in ("id", "name", "suburb", "address", "sport", "lat", "lng",
                                      "booking_url", "price_note")}
        try:
            if args.demo:
                slots = demo_slots(v, start, days)
            else:
                if i:
                    time.sleep(POLITE_DELAY_S)
                slots = ADAPTERS[v["platform"]](v, start, end)
            info.update(slots=slots, updated=now, status="ok")
            print(f"ok    {v['id']}: {len(slots)} free slots")
        except Exception as e:  # keep last good data, flag it
            failures += 1
            old = previous.get(v["id"], {})
            info.update(slots=old.get("slots", []), updated=old.get("updated"),
                        status="stale", error=f"{type(e).__name__}: {e}"[:300])
            print(f"FAIL  {v['id']}: {info['error']}", file=sys.stderr)
        results.append(info)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"generated": now, "demo": args.demo, "venues": results}, indent=1))
    print(f"wrote {OUT.relative_to(ROOT)} ({len(results)} venues, {failures} failed)")
    # Only fail the job if every venue failed — partial data is still useful.
    return 1 if results and failures == len(results) else 0


if __name__ == "__main__":
    sys.exit(main())
