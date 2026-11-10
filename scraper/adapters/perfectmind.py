"""PerfectMind "BookMe4" facility booking (used by Cricket NSW for Cricket Central
indoor nets, and by many councils / leisure centres).

How the site works (checked in a browser on 2026-11-10):

1. GET  https://{host}/{org}/Clients/BookMe4LandingPages/Facility?facilityId=...&widgetId=...&calendarId=...
   sets an anti-forgery cookie and puts a matching hidden
   <input name="__RequestVerificationToken"> in the page. No login needed.
2. POST https://{host}/{org}/Clients/BookMe4LandingPages/FacilityAvailability
   form: facilityId, date (midnight, ISO), daysCount, duration (minutes),
         serviceId, durationIds[], __RequestVerificationToken
   returns {"availabilities": [{"Date": "/Date(<ms>)/", "BookingGroups":
           [{"AvailableSpots": [{"Time": {"Hours":16,"Minutes":0}, "IsDisabled": false}, ...]}]}]}

Each "lane" (net) is a separate facilityId; a venue config lists them as courts.
"""
import http.cookiejar
import json
import re
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    SYD = ZoneInfo("Australia/Sydney")
except Exception:  # pragma: no cover
    SYD = timezone(timedelta(hours=10))

USER_AGENT = "CourtFinder/0.1 (availability aggregator; links users to the venue's own booking page)"
TOKEN_RE = re.compile(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"')


class FormatChanged(Exception):
    pass


def landing_url(v: dict, facility_id: str, day: str | None = None) -> str:
    q = {"facilityId": facility_id, "widgetId": v["widget_id"], "calendarId": v["calendar_id"]}
    if day:
        q["arrivalDate"] = f"{day}T00:00:00.000Z"
    return f"https://{v['host']}/{v['org']}/Clients/BookMe4LandingPages/Facility?" + urllib.parse.urlencode(q)


def parse(data: dict, court: str, link_for) -> list[dict]:
    if not isinstance(data, dict) or "availabilities" not in data:
        raise FormatChanged(f"unexpected response: {str(data)[:200]}")
    slots = []
    for d in data["availabilities"]:
        m = re.search(r"-?\d+", str(d.get("Date", "")))
        if not m:
            raise FormatChanged("day without a /Date(ms)/ value")
        day = datetime.fromtimestamp(int(m.group()) / 1000, tz=SYD).date().isoformat()
        for g in d.get("BookingGroups") or []:
            for s in g.get("AvailableSpots") or []:
                if s.get("IsDisabled"):
                    continue
                t, dur = s["Time"], s.get("Duration") or {}
                start = t["Hours"] * 60 + t["Minutes"]
                end = start + int(dur.get("TotalMinutes") or 60)
                slots.append({"date": day, "start": f"{start // 60:02d}:{start % 60:02d}",
                              "end": f"{end // 60:02d}:{end % 60:02d}", "court": court,
                              "booking_url": link_for(day)})
    return slots


def fetch(v: dict, start: date, end: date) -> list[dict]:
    days = (end - start).days + 1
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [("User-Agent", USER_AGENT)]
    slots = []
    for lane in v["lanes"]:
        # Step 1: open the lane's page to get the cookie + token
        html = opener.open(landing_url(v, lane["facility_id"]), timeout=30).read().decode("utf-8", "replace")
        m = TOKEN_RE.search(html)
        if not m:
            raise FormatChanged("no __RequestVerificationToken on the facility page")
        token = m.group(1)
        # Step 2: ask for the week's availability
        body = urllib.parse.urlencode({
            "facilityId": lane["facility_id"], "date": f"{start.isoformat()}T00:00:00.000Z",
            "daysCount": str(days), "duration": str(v.get("duration", 60)),
            "serviceId": v["service_id"], "durationIds[]": v["duration_id"],
            "__RequestVerificationToken": token,
        }).encode()
        req = urllib.request.Request(
            f"https://{v['host']}/{v['org']}/Clients/BookMe4LandingPages/FacilityAvailability",
            data=body, method="POST", headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
            })
        data = json.loads(opener.open(req, timeout=30).read().decode("utf-8"))
        slots += parse(data, lane["name"], lambda day, fid=lane["facility_id"]: landing_url(v, fid, day))
    return slots
