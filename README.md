# Kohi Swim Windows

A Google Calendar feed of good swim windows at Kohimarama Beach, Auckland — built around high tide, daylight, and traffic-friendly start times.

**Subscribe link:** `https://sw33tpi.github.io/KohiTides/kohimarama_swim_tides.ics`

## Source data

- **Tide predictions:** [LINZ (Land Information New Zealand) tide predictions](https://www.linz.govt.nz/products-services/tides-and-tidal-streams/tide-predictions) — Auckland standard port. Raw data pulled from LINZ's published CSV (e.g. `https://static.charts.linz.govt.nz/tide-tables/maj-ports/csv/Auckland 2026.csv`). These are official predictions, not a live/observed feed, and are not an official tide table under Maritime Rules Part 25.
- **Sunset times:** calculated astronomically for Kohimarama's exact coordinates (36.8591°S, 174.8458°E) using the [`astral`](https://pypi.org/project/astral/) Python library — not pulled from an external API, computed directly from the date and location.

## Start window logic

A high tide only qualifies for a swim window if it falls **on or after** a day-of-week-specific start time, chosen to avoid peak traffic to the beach:

| Day | Earliest qualifying high tide |
|---|---|
| Mon – Thu | 10:00am |
| Fri | 9:30am |
| Sat / Sun | 9:00am |

## End window logic

A high tide only qualifies if it falls **on or before sunset + 30 minutes** for that specific date (sunset shifts throughout the year — from ~5:15pm in winter to ~8:45pm in midsummer).

Once a high tide qualifies under both the start and end rules, its swim window is the full **90 minutes either side of the high tide peak** — this window is not trimmed even if the tail end runs past sunset+30, since swimming into the evening is fine.

## Regenerating for a new year

Once LINZ publish the next year's tide table, re-run `generate_tide_calendar.py` against the new CSV and re-upload `kohimarama_swim_tides.ics` to this repo (same filename — no need to update the subscribe link).
