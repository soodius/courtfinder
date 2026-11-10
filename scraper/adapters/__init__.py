"""Adapters turn one booking platform's data into a common shape.

Every adapter exposes:

    fetch(venue: dict, start: date, end: date) -> list[dict]

returning one dict per free slot:

    {"date": "2026-11-12", "start": "18:00", "end": "19:00",
     "court": "Court 2", "booking_url": "https://..."}

To support a new platform, add a module here with a fetch() function and
register it in ADAPTERS.
"""
from . import clubspark, perfectmind


def link_only(venue, start, end):
    """Venue books through a system we can't read (e.g. a members' portal): no times, just the link."""
    return []


ADAPTERS = {
    "clubspark": clubspark.fetch,      # Tennis Australia Book a Court / play.tennis.com.au
    "perfectmind": perfectmind.fetch,  # Cricket NSW Cricket Central nets, many councils
    "link_only": link_only,
}
