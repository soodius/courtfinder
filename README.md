# CourtFinder

Shows free court times at local sports venues. A scraper checks each venue's
booking site every 15 minutes, and every time slot links straight to that
venue's own booking page, so people book there.

Runs entirely free on GitHub: GitHub Actions does the scraping and GitHub
Pages hosts the site.

```
venues.json                  ← the list of venues to scrape (edit this)
scraper/scrape.py            ← runs every adapter, writes site/data/availability.json
scraper/adapters/clubspark.py← Tennis Australia "Book a Court" / ClubSpark sites
site/index.html              ← the app (reads data/availability.json)
.github/workflows/scrape.yml ← every 15 min: test → scrape → publish
tests/                       ← parser tests
```

## Put it online (about 10 minutes)

1. Create a free account at github.com, then a new **public** repository (e.g. `courtfinder`).
2. Upload everything in this folder to it (drag-and-drop on the repo page works; make sure the hidden `.github` folder goes too).
3. In the repo: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. **Actions** tab → "Scrape availability and publish site" → **Run workflow**.
5. When it goes green, your app is live at `https://<your-username>.github.io/courtfinder/`.
   From then on it refreshes itself every 15 minutes.

## Before going live: check the first real scrape

The scraper reads the same data feed that Book a Court's booking sheet uses
(`/v0/VenueBooking/<venue>/GetVenueSessions`). It couldn't be tested live while
building this, so after the first run:

- Open the Action's log. Each venue prints `ok … N free slots` or `FAIL … reason`.
- Open one venue's booking page in your browser and compare a few times with the app.
- If you see `FormatChanged`, the site's data layout differs from what the
  adapter expects. Open the booking page, press F12 → Network, reload, find the
  request that returns the court times, and send its response to whoever
  maintains this (or to Claude) to adjust `parse()` in `clubspark.py`.

Note: Jonas Bradley Park (the starter venue) showed a "courts currently closed"
notice when this was built, so it may return no free times. Add a few more
venues to test properly.

## Adding venues

Add an entry to `venues.json`. For any Book a Court / ClubSpark venue:

```json
{
  "id": "merrylands-park",
  "name": "Merrylands Park Tennis Courts",
  "suburb": "Merrylands",
  "sport": "tennis",
  "lat": -33.83, "lng": 150.99,
  "platform": "clubspark",
  "host": "play.tennis.com.au",
  "slug": "<from the venue's booking URL>",
  "booking_url": "<the venue's booking page>"
}
```

- **slug**: the part after the domain in the venue's booking URL, e.g.
  `play.tennis.com.au/SomeVenue/Booking` → `SomeVenue`.
- **lat / lng**: right-click the venue in Google Maps to copy them (used for distance sorting).
- Optional **booking_url_template**: e.g. `"https://site/book?date={date}"` if the
  venue's own page accepts a date; slot links will then open on that date.

Other sports (basketball, futsal, swimming…) use other booking systems
(Skedda, Playtomic, council portals, etc.). Each needs its own small adapter in
`scraper/adapters/` with a `fetch(venue, start, end)` function returning free
slots in the same shape. See `adapters/__init__.py`.

## Run it on your own computer

```
python3 scraper/scrape.py --demo   # sample data
python3 scraper/scrape.py          # real scrape
cd site && python3 -m http.server  # then open http://localhost:8000
python3 -m unittest discover tests
```

## Being a good scraping neighbour

- It waits 2 seconds between venues and identifies itself in the User-Agent.
- 15 minutes is a sensible interval. Going much faster risks being blocked.
- Booking sites' terms often restrict automated access. Read the terms for each
  platform you add. For anything beyond a personal or local project, ask the
  operator (e.g. Tennis Australia, or the council) for permission or an official
  data feed. Many are happy to help, since you're sending them bookings.
- If a venue asks you to stop, remove it from `venues.json`.
