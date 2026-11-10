"""ClubSpark adapter: Tennis Australia "Book a Court" (play.tennis.com.au /
bookacourt.tennis.com.au) and LTA ClubSpark (clubspark.lta.org.uk).

The booking sheet on these sites is filled in by the browser from a JSON feed:

    https://{host}/v0/VenueBooking/{slug}/GetVenueSessions
        ?resourceID=&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD&roleId=

The response lists each court ("Resources") and, for each day, its
"Sessions". Times are minutes after midnight. An open, bookable window is a
session with Category 0 and Capacity > 0; everything else on that court
(bookings, coaching, closures) blocks time. Free slots are the open windows,
cut into Interval-minute steps, minus anything that overlaps a blocking
session.

If the platform changes this format, parse() raises FormatChanged so the run
reports the venue as failed instead of quietly showing wrong times.
"""
import json
import urllib.parse
import urllib.request
from datetime import date

USER_AGENT = "CourtFinder/0.1 (availability aggregator; links users to the venue's own booking page)"


class FormatChanged(Exception):
    pass


def feed_url(host: str, slug: str, start: date, end: date) -> str:
    q = urllib.parse.urlencode({
        "resourceID": "", "startDate": start.isoformat(),
        "endDate": end.isoformat(), "roleId": "",
    })
    return f"https://{host}/v0/VenueBooking/{slug}/GetVenueSessions?{q}"


def default_booking_url(host: str, slug: str, day: str) -> str:
    # Opens the venue's booking sheet on the right date.
    return f"https://{host}/{slug}/Booking/BookByDate#?date={day}&role=guest"


def _hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse(data: dict, booking_url_for) -> list[dict]:
    if not isinstance(data, dict) or "Resources" not in data:
        raise FormatChanged("no 'Resources' key in response")
    default_interval = int(data.get("MinimumInterval") or 60)
    slots = []
    for res in data["Resources"]:
        court = res.get("Name") or f"Court {res.get('Number', '?')}"
        for day in res.get("Days", []):
            day_str = str(day.get("Date", ""))[:10]
            sessions = day.get("Sessions", [])
            open_ = [s for s in sessions
                     if s.get("Category") == 0 and (s.get("Capacity") or 0) > 0]
            blocks = [s for s in sessions if s not in open_]
            for s in open_:
                step = int(s.get("Interval") or default_interval)
                t = int(s["StartTime"])
                while t + step <= int(s["EndTime"]):
                    clash = any(b["StartTime"] < t + step and b["EndTime"] > t for b in blocks)
                    if not clash:
                        slots.append({
                            "date": day_str, "start": _hhmm(t), "end": _hhmm(t + step),
                            "court": court, "booking_url": booking_url_for(day_str),
                        })
                    t += step
    return slots


def fetch(venue: dict, start: date, end: date) -> list[dict]:
    host = venue.get("host", "play.tennis.com.au")
    slug = venue["slug"]
    req = urllib.request.Request(feed_url(host, slug, start, end), headers={
        "User-Agent": USER_AGENT, "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))

    # Deep link straight to the booking sheet for that date; fall back to the
    # venue's own page if one is configured and the date link isn't wanted.
    def link(day: str) -> str:
        return venue.get("booking_url_template", "").format(date=day) or default_booking_url(host, slug, day)

    return parse(data, link)
