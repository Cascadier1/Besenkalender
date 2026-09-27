import json
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Besenkatalog im Umkreis von ca. 15 km um Öhringen
BESEN_KATALOG = [
    {
        "id": "banzhaf",
        "title": "Weinausschank Banzhaf",
        "ort": "Bretzfeld-Siebeneich (ca. 8 km)",
        "location": "Wengertstraße 16, 74626 Bretzfeld-Siebeneich",
        "hours": "Do - Sa ab 11:30 Uhr, So & Feiertage ab 11:00 Uhr",
        "color": "#a83232",
        "url": "https://www.besen-banzhaf.de/",
        # Ausschließlich offizielle Weinausschank-Termine (ohne externe Feste/Catering):
        "fallback_ranges": [
            ("2026-01-22", "2026-01-25"),
            ("2026-02-19", "2026-02-22"),
            ("2026-03-26", "2026-03-29"),
            ("2026-04-23", "2026-04-26"),
            ("2026-05-14", "2026-05-17"),
            ("2026-08-06", "2026-08-09"),
            ("2026-09-03", "2026-09-06"),
            ("2026-10-15", "2026-10-18"),
            ("2026-11-12", "2026-11-15"),
            ("2026-12-07", "2026-12-13"),  # Hauseigener Weihnachtsmarkt
        ]
    },
    {
        "id": "borth",
        "title": "Weingut & Weinstube Borth",
        "ort": "Bretzfeld-Adolzfurt (ca. 9 km)",
        "location": "Unterheimbacher Str. 35, 74626 Bretzfeld-Adolzfurt",
        "hours": "Do - Sa ab 11:00 Uhr (Küche bis 21:00 Uhr), So ab 11:00 Uhr (Küche bis 19:30 Uhr)",
        "color": "#722f37",
        "url": "https://www.weingut-borth.de/pages/offnungszeiten-aktuelle-speisen",
        "fallback_ranges": [
            ("2026-01-15", "2026-01-18"),
            ("2026-02-12", "2026-02-15"),
            ("2026-03-12", "2026-03-15"),
            ("2026-04-16", "2026-04-19"),
            ("2026-05-21", "2026-05-24"),
            ("2026-09-24", "2026-09-27"),
            ("2026-10-22", "2026-10-25"),
            ("2026-11-19", "2026-11-22"),
            ("2026-12-03", "2026-12-06"),
        ]
    },
    {
        "id": "schwab",
        "title": "Besenwirtschaft Schwab",
        "ort": "Pfedelbach-Dimbach (ca. 6 km)",
        "location": "Schwabbacher Str. 8, 74629 Pfedelbach-Dimbach",
        "hours": "Täglich ab 11:00 Uhr geöffnet",
        "color": "#1f5f8b",
        "url": "https://www.weinbau-schwab.de/",
        "fallback_ranges": [
            ("2026-01-09", "2026-01-18"),
            ("2026-02-06", "2026-02-15"),
            ("2026-03-06", "2026-03-15"),
            ("2026-04-10", "2026-04-19"),
            ("2026-05-08", "2026-05-17"),
            ("2026-09-11", "2026-09-20"),
            ("2026-10-09", "2026-10-18"),
            ("2026-11-06", "2026-11-15"),
        ]
    },
    {
        "id": "ungerer",
        "title": "Weingut Ungerer",
        "ort": "Pfedelbach-Renzen (ca. 7 km)",
        "location": "Harsberger Str. 15, 74629 Pfedelbach-Renzen",
        "hours": "Täglich ab 11:00 Uhr geöffnet",
        "color": "#d48806",
        "url": "https://www.weingut-ungerer.de/",
        "fallback_ranges": [
            ("2026-01-09", "2026-01-18"),
            ("2026-02-13", "2026-02-22"),
            ("2026-03-13", "2026-03-22"),
            ("2026-04-10", "2026-04-19"),
            ("2026-05-08", "2026-05-17"),
            ("2026-06-12", "2026-06-21"),
            ("2026-07-10", "2026-07-19"),
            ("2026-09-11", "2026-09-20"),
            ("2026-11-06", "2026-11-15"),
            ("2026-12-04", "2026-12-13"),
        ]
    },
    {
        "id": "schluchter",
        "title": "Weingut Schluchter",
        "ort": "Pfedelbach-Baierbach (ca. 7 km)",
        "location": "Baierbacher Str. 12, 74629 Pfedelbach-Baierbach",
        "hours": "Mo - Sa ab 11:00 Uhr, So ab 10:30 Uhr",
        "color": "#843b62",
        "url": "https://www.weingut-schluchter.de/",
        "fallback_ranges": [
            ("2026-01-23", "2026-02-01"),
            ("2026-02-20", "2026-03-01"),
            ("2026-03-20", "2026-03-29"),
            ("2026-04-24", "2026-05-03"),
            ("2026-10-09", "2026-10-18"),
            ("2026-11-20", "2026-11-29"),
        ]
    },
    {
        "id": "baldele",
        "title": "Baldele's Weinstube",
        "ort": "Öhringen-Michelbach (ca. 4 km)",
        "location": "Obersteinbacher Str. 23, 74613 Öhringen-Michelbach",
        "hours": "Do & Fr ab 17:00 Uhr, Sa & So ab 11:00 Uhr (ca. 2 WE pro Monat)",
        "color": "#2c5e3b",
        "url": "http://www.baldeles-weinstube.de/",
        # Baldele veröffentlicht keinen Ganzjahresplan – Scraper liest nur echte Website-Ankündigungen ein:
        "fallback_ranges": []
    }
]

MONTH_MAP = {
    "januar": 1, "jan": 1,
    "februar": 2, "feb": 2,
    "märz": 3, "maerz": 3, "mrz": 3,
    "april": 4, "apr": 4,
    "mai": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9,
    "oktober": 10, "okt": 10,
    "november": 11, "nov": 11,
    "dezember": 12, "dez": 12
}

def parse_dates_from_text(text, year=2026):
    """Sucht nach Datumsintervallen (z.B. '15. - 18. Januar' oder '15.01. - 18.01.2026')"""
    ranges = []

    # Muster 1: DD.MM. - DD.MM.YYYY oder DD.MM.YYYY - DD.MM.YYYY
    p1 = re.finditer(r'(\d{1,2})\.(\d{1,2})\.(?:\d{2,4})?\s*(?:bis|-|–)\s*(\d{1,2})\.(\d{1,2})\.(\d{2,4})', text)
    for m in p1:
        d1, m1, d2, m2, y2 = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
        if y2 < 100:
            y2 += 2000
        ranges.append((f"{y2:04d}-{m1:02d}-{d1:02d}", f"{y2:04d}-{m2:02d}-{d2:02d}"))

    # Muster 2: DD. - DD. Monat (YYYY)
    p2 = re.finditer(r'(\d{1,2})\.?\s*(?:bis|-|–)\s*(\d{1,2})\.\s*([A-Za-zäöüÄÖÜ]+)(?:\s*(\d{4}))?', text)
    for m in p2:
        d1, d2 = int(m.group(1)), int(m.group(2))
        mon_str = m.group(3).lower()
        y = int(m.group(4)) if m.group(4) else year
        if mon_str in MONTH_MAP:
            mon = MONTH_MAP[mon_str]
            ranges.append((f"{y:04d}-{mon:02d}-{d1:02d}", f"{y:04d}-{mon:02d}-{d2:02d}"))

    return ranges

def scrape_besen(besen):
    url = besen.get("url")
    if url:
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                text = soup.get_text(separator=" ")
                scraped = parse_dates_from_text(text)
                if scraped:
                    return scraped
        except Exception:
            pass
    return besen.get("fallback_ranges", [])

def main():
    events = []
    
    for b in BESEN_KATALOG:
        ranges = scrape_besen(b)
        
        # Duplikate filtern und chronologisch sortieren
        unique_ranges = sorted(list(set(ranges)), key=lambda x: x[0])
        
        for start_str, end_str in unique_ranges:
            try:
                d_start = datetime.strptime(start_str, "%Y-%m-%d")
                d_end = datetime.strptime(end_str, "%Y-%m-%d")
                
                # +1 Tag für FullCalendar:
                # FullCalendar interpretiert das Enddatum als exklusiv (00:00:00 Uhr).
                # Durch +1 Tag wird der Sonntag / Endtag im Kalender vollständig markiert.
                fc_end = (d_end + timedelta(days=1)).strftime("%Y-%m-%d")
                
                label_text = f"{d_start.strftime('%d.%m.%Y')} – {d_end.strftime('%d.%m.%Y')}"
                
                event = {
                    "id": f"{b['id']}_{start_str}",
                    "besenId": b["id"],
                    "title": b["title"],
                    "start": start_str,
                    "end": fc_end,
                    "backgroundColor": b.get("color", "#722f37"),
                    "borderColor": b.get("color", "#722f37"),
                    "allDay": True,
                    "extendedProps": {
                        "besenTitle": b["title"],
                        "ort": b["ort"],
                        "location": b["location"],
                        "hours": b["hours"],
                        "url": b.get("url", ""),
                        "period": label_text
                    }
                }
                events.append(event)
            except Exception as e:
                print(f"Fehler bei {b['id']} ({start_str} - {end_str}): {e}")

    # Speichern als JSON
    output = {
        "last_updated": datetime.now().strftime("%d.%m.%Y um %H:%M Uhr"),
        "events": events
    }

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Erfolgreich {len(events)} Termine in events.json geschrieben.")

if __name__ == "__main__":
    main()
