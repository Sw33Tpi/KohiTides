"""
Kohimarama swim window tide calendar generator.

Tide data source: LINZ (Land Information New Zealand) official tide predictions
for the Auckland standard port -- the closest standard port to Kohimarama Beach.
https://www.linz.govt.nz/products-services/tides-and-tidal-streams/tide-predictions

"""
import csv
import uuid
from datetime import datetime, timedelta, time
import zoneinfo
from astral import LocationInfo
from astral.sun import sun

# ---- Config ----
INPUT_CSV = "raw_tides.csv"
OUTPUT_ICS = "kohimarama_swim_tides.ics"
WINDOW = timedelta(minutes=90)   # either side of high tide (not trimmed by sunset)
SUNSET_BUFFER = timedelta(minutes=30)  # how far past sunset a high tide can still qualify
LOCATION_NAME = "Kohimarama Beach, Auckland"
TZID = "Pacific/Auckland"

TZ = zoneinfo.ZoneInfo(TZID)
LOC = LocationInfo("Kohimarama", "New Zealand", TZID, -36.8591, 174.8458)

# Earliest acceptable high-tide time, by weekday (Monday=0 ... Sunday=6)
# Mon-Thu 10:00, Fri 09:30, Sat/Sun 09:00 -- avoids peak traffic to the beach
START_TIME_BY_WEEKDAY = {
    0: time(10, 0), 1: time(10, 0), 2: time(10, 0), 3: time(10, 0),  # Mon-Thu
    4: time(9, 30),                                                    # Fri
    5: time(9, 0), 6: time(9, 0),                                      # Sat, Sun
}

def sunset_for(d):
    s = sun(LOC.observer, date=d, tzinfo=TZ)
    return s["sunset"]

def parse_rows(path):
    rows = []
    with open(path) as f:
        for r in csv.reader(f):
            if len(r) < 6:
                continue
            day, wk, month, year = r[0], r[1], r[2], r[3]
            pairs = []
            for i in range(4, len(r), 2):
                if i + 1 >= len(r):
                    break
                t, h = r[i].strip(), r[i + 1].strip()
                if t and h:
                    pairs.append((t, h))
            try:
                base = datetime(int(year), int(month), int(day))
            except ValueError:
                continue
            rows.append((base, pairs))
    return rows

def classify_tides(rows):
    """Return chronological list of (datetime, height, kind) for every tide event."""
    events = []
    for base, pairs in rows:
        for t, h in pairs:
            hh, mm = map(int, t.split(":"))
            events.append([base + timedelta(hours=hh, minutes=mm), float(h)])
    events.sort(key=lambda x: x[0])
    classified = []
    n = len(events)
    for i in range(n):
        dt, h = events[i]
        prev_h = events[i - 1][1] if i > 0 else None
        next_h = events[i + 1][1] if i < n - 1 else None
        if prev_h is None:
            kind = "high" if (next_h is not None and h > next_h) else "low"
        elif next_h is None:
            kind = "high" if h > prev_h else "low"
        else:
            kind = "high" if h > prev_h and h > next_h else "low"
        classified.append((dt, h, kind))
    return classified

def build_ics(swim_events):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Kohimarama Swim Tides//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Kohi Swim Windows",
        "X-WR-TIMEZONE:Pacific/Auckland",
        "BEGIN:VTIMEZONE",
        "TZID:Pacific/Auckland",
        "BEGIN:STANDARD",
        "DTSTART:19700405T030000",
        "RRULE:FREQ=YEARLY;BYMONTH=4;BYDAY=1SU",
        "TZOFFSETFROM:+1300",
        "TZOFFSETTO:+1200",
        "TZNAME:NZST",
        "END:STANDARD",
        "BEGIN:DAYLIGHT",
        "DTSTART:19700927T020000",
        "RRULE:FREQ=YEARLY;BYMONTH=9;BYDAY=-1SU",
        "TZOFFSETFROM:+1200",
        "TZOFFSETTO:+1300",
        "TZNAME:NZDT",
        "END:DAYLIGHT",
        "END:VTIMEZONE",
    ]
    for start, end, peak, height in swim_events:
        uid = f"{uuid.uuid4()}@kohimarama-swim-tides"
        dtstamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
        summary = f"High tide at {peak.strftime('%H:%M')} ({height:.1f}m)"
        desc = (
            f"High tide at {peak.strftime('%H:%M')} ({height:.1f}m). "
            f"Tide is flooding (rising) into the peak, then ebbing (falling) afterwards. "
            f"Window is 90 min either side of peak high tide at {LOCATION_NAME}. "
            f"Included based on day-of-week start time and sunset+30min cutoff. "
            f"Tide source: LINZ Auckland standard port predictions (not an official tide table)."
        )
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART;TZID={TZID}:{start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND;TZID={TZID}:{end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{desc}",
            f"LOCATION:{LOCATION_NAME}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

def main():
    rows = parse_rows(INPUT_CSV)
    classified = classify_tides(rows)
    highs = [(dt, h) for dt, h, kind in classified if kind == "high"]
    swim_events = []
    for dt, h in highs:
        start_threshold = START_TIME_BY_WEEKDAY[dt.weekday()]
        sunset = sunset_for(dt.date())
        cutoff = sunset + SUNSET_BUFFER
        dt_aware = dt.replace(tzinfo=TZ)
        qualifies = (dt.time() >= start_threshold) and (dt_aware <= cutoff)
        if qualifies:
            swim_events.append((dt - WINDOW, dt + WINDOW, dt, h))
    ics = build_ics(swim_events)
    with open(OUTPUT_ICS, "w") as f:
        f.write(ics)
    print(f"Wrote {len(swim_events)} swim-window events to {OUTPUT_ICS}")

if __name__ == "__main__":
    main()
