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

## Sources (checked in a real browser on 10 Nov 2026)

| Source | How it's read | Venues |
|---|---|---|
| **Tennis Australia Court Finder** (Blacktown, Cumberland, Parramatta council courts and clubs) | `discover.py` searches around each area in `venues.json` → `discover`, then `adapters/clubspark.py` reads each venue's full timetable from play.tennis.com.au | Found automatically: e.g. Caroline Chisholm Park, Gallery Gardens, Timbergetters, Caber Park, Merrylands Park, Mays Hill… |
| **Cricket NSW indoor net hire** (Cricket Central, Sydney Olympic Park) | `adapters/perfectmind.py`: opens each lane's page for a token, then asks for the week's times | 9 lanes, set up by hand in `venues.json` |
| Venues on their own systems (e.g. Blacktown Tennis Centre Stanhope, members' login) | Can't be read; listed with a "Book on venue site" link | Found automatically |

Every time slot links to that venue's booking page on the right date.

## After the first run

- Open the Action's log. Each venue prints `ok … N free slots` or `FAIL … reason`.
- Spot-check a couple of venues against their booking pages.
- `FormatChanged` in the log means a site changed how it sends its data; the
  venue keeps its last good times (marked "may be out of date") until the
  adapter is updated.

## Adding venues

**More tennis areas:** add a suburb + postcode to `discover`, e.g.
`{"name": "Castle Hill", "postcode": "2154", "sport": "tennis", "proximity": 2}`.
To hide a found venue, put its id (e.g. `"mays-hill-tennis-courts"`) in `exclude`.

**More PerfectMind venues** (many councils' leisure centres use it): copy the
Cricket Central entry. The IDs are in the URL when you open a facility's
booking page (`facilityId`, `widgetId`, `calendarId`).

**A single Book a Court / ClubSpark venue by hand:**

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
