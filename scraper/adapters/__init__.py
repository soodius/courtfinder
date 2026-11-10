"""Adapters turn one booking platform's data into a common shape.

Every adapter exposes:

    fetch(venue: dict, start: date, end: date) -> list[dict]

returning one dict per free slot:

    {"date": "2026-11-12", "start": "18:00", "end": "19:00",
     "court": "Court 2", "booking_url": "https://..."}

To support a new platform, add a module here with a fetch() function and
register it in ADAPTERS.
"""
from . import clubspark

ADAPTERS = {
    "clubspark": clubspark.fetch,
}
