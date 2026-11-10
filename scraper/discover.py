"""Find tennis venues automatically through Tennis Australia's Court Finder
(the search behind https://www.tennis.com.au/book/court-hire/).

    GET https://api.tennis.com.au/bkjr/v1/api/court-hire/search
        ?locationName=blacktown&locationPostcode=2148&duration=60
        &fromDate=2026-11-10T15:42:48&dateMode=on&wheelchairAccess=false
        &instantBooking=false&proximity=2&facilityType=tennis

Each result has the venue's name, suburb, coordinates, price and its ClubSpark
booking page (websites.hireACourtURL, e.g. https://play.tennis.com.au/GalleryGardensTennisCourts/),
which the clubspark adapter then reads for the full timetable. Venues that book
through another system have bookingOptions.externalBookingUrl set; those are
listed as link-only.
"""
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime

SEARCH = "https://api.tennis.com.au/bkjr/v1/api/court-hire/search"
USER_AGENT = "CourtFinder/0.1 (availability aggregator; links users to the venue's own booking page)"


def search(area: dict) -> dict:
    q = urllib.parse.urlencode({
        "locationName": area["name"].lower(), "locationPostcode": area["postcode"],
        "duration": "60", "fromDate": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "dateMode": "on", "wheelchairAccess": "false", "instantBooking": "false",
        "proximity": str(area.get("proximity", 2)), "facilityType": area.get("sport", "tennis"),
    })
    req = urllib.request.Request(f"{SEARCH}?{q}", headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def to_venues(data: dict, sport: str = "tennis") -> list[dict]:
    out = []
    for item in data.get("items", []):
        v, b = item["venue"], item.get("bookingOptions") or {}
        addr = v.get("address") or {}
        hire = (v.get("websites") or {}).get("hireACourtURL") or ""
        m = re.match(r"https?://([^/]+)/([^/?#]+)", hire)
        ext = b.get("externalBookingUrl")
        base = {
            "id": re.sub(r"[^a-z0-9]+", "-", v["clubName"].lower()).strip("-"),
            "name": v["clubName"], "suburb": (addr.get("suburb") or "").title(), "sport": sport,
            "lat": addr.get("latitude"), "lng": addr.get("longitude"),
            "price_note": f"From ${b['priceFrom']:.2f} / 30 min" if b.get("priceFrom") else None,
        }
        if ext or not m:
            out.append({**base, "platform": "link_only", "booking_url": ext or hire,
                        "price_note": "Book on the venue's own system"})
        else:
            out.append({**base, "platform": "clubspark", "host": m.group(1), "slug": m.group(2),
                        "booking_url": hire})
    return out


def discover(areas: list[dict]) -> list[dict]:
    seen, venues = set(), []
    for a in areas:
        for v in to_venues(search(a), a.get("sport", "tennis")):
            if v["id"] not in seen:
                seen.add(v["id"])
                venues.append(v)
    return venues
