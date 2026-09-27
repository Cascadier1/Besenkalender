import json
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Vollständiger Katalog aller 11 Besenwirtschaften im Raum Öhringen
BESEN_KATALOG = [
    {
        "id": "borth",
        "title": "Weingut & Weinstube Borth",
        "ort": "Bretzfeld-Adolzfurt (ca. 7 km)",
        "location": "Unterheimbacher Straße 35, 74626 Bretzfeld-Adolzfurt",
        "hours": "Täglich ab 11:00 Uhr | Küche Do-Sa bis ca. 21:00 Uhr, So bis ca. 19:30 Uhr",
        "color": "#800020",
        "url": "https://www.weingut-borth.de/pages/oeffnungszeiten-speisekarte",
        "fallback_ranges": [
            ("2026-09-24", "2026-09-27"),
            ("2026-10-08", "2026-10-11"),
            ("2026-10-22", "2026-10-25"),
            ("2026-11-05", "2026-11-08"),
            ("2026-11-19", "2026-11-22"),
            ("2026-12-03", "2026-12-06"),
        ]
    },
    {
        "id": "schluchter",
        "title": "Schluchters Weinstube",
        "ort": "Pfedelbach-Baierbach (ca. 5 km)",
        "location": "Ruländerweg 3, 74629 Pfedelbach-Baierbach",
        "hours": "Fr & Sa ab 14:00 Uhr, So ab 11:30 Uhr (oder ab 12 Uhr)",
        "color": "#2c5e3b",
        "url": "https://www.schluchters-weinstube.de/oeffnungszeiten/",
        "fallback_ranges": [
            ("2026-09-18", "2026-09-20"),
            ("2026-10-02", "2026-10-04"),
            ("2026-10-16", "2026-10-18"),
            ("2026-10-30", "2026-11-01"),
            ("2026-11-13", "2026-11-15"),
            ("2026-11-27", "2026-11-29"),
        ]
    },
    {
        "id": "baldele",
        "title": "Weinstube Baldele",
        "ort": "Bretzfeld-Unterheimbach (ca. 9 km)",
        "location": "Waldbachstraße 16, 74626 Bretzfeld-Unterheimbach",
        "hours": "Täglich ab 11:00 Uhr | Besenküche durchgehend",
        "color": "#8b5a2b",
        "url": "http://www.weinstube-baldele.de/",
        "fallback_ranges": [
            ("2026-09-25", "2026-09-28"),
            ("2026-10-09", "2026-10-12"),
            ("2026-10-23", "2026-10-26"),
            ("2026-11-06", "2026-11-09"),
            ("2026-11-20", "2026-11-23"),
            ("2026-12-04", "2026-12-07"),
        ]
    },
    {
        "id": "schwab",
        "title": "Weingut Schwab – Weinstube",
        "ort": "Bretzfeld-Dimbach (ca. 6 km)",
        "location": "Schwabbacher Straße 4, 74626 Bretzfeld-Dimbach",
        "hours": "Do-Sa ab 11:30 Uhr, So & Feiertag ab 11:00 Uhr",
        "color": "#1a5276",
        "url": "https://www.weingut-schwab.de/",
        "fallback_ranges": [
            ("2026-10-01", "2026-10-04"),
            ("2026-10-15", "2026-10-18"),
            ("2026-10-29", "2026-11-01"),
            ("2026-11-12", "2026-11-15"),
            ("2026-11-26", "2026-11-29"),
            ("2026-12-10", "2026-12-13"),
        ]
    },
    {
        "id": "ungerer",
        "title": "Besenwirtschaft Ungerer",
        "ort": "Pfedelbach-Windischenbach (ca. 4 km)",
        "location": "Lindenstraße 12, 74629 Pfedelbach",
        "hours": "Do-Sa ab 11:30 Uhr, So ab 11:00 Uhr",
        "color": "#b03a2e",
        "url": "https://www.weingut-ungerer.de/",
        "fallback_ranges": [
            ("2026-10-08", "2026-10-11"),
            ("2026-10-22", "2026-10-25"),
            ("2026-11-05", "2026-11-08"),
            ("2026-11-19", "2026-11-22"),
        ]
    },
    {
        "id": "birkert",
        "title": "Weingut Birkert – Besenstüble",
        "ort": "Bretzfeld-Adolzfurt (ca. 7 km)",
        "location": "Schmiedgasse 14, 74626 Bretzfeld-Adolzfurt",
        "hours": "Fr & Sa ab 14:00 Uhr, So ab 11:30 Uhr",
        "color": "#6c3483",
        "url": "https://www.weingut-birkert.com/besenkalender/",
        "fallback_ranges": [
            ("2026-10-02", "2026-10-04"),
            ("2026-10-16", "2026-10-18"),
            ("2026-10-30", "2026-11-01"),
            ("2026-11-13", "2026-11-15"),
            ("2026-11-27", "2026-11-29"),
        ]
    },
    {
        "id": "busch",
        "title": "Besenwirtschaft Familie Busch",
        "ort": "Bretzfeld-Dimbach (ca. 6 km)",
        "location": "Waldenburger Str. 8, 74626 Bretzfeld-Dimbach",
        "hours": "Fr ab 15:00 Uhr, Sa ab 14:00 Uhr, So ab 11:30 Uhr",
        "color": "#784212",
        "url": "https://www.weingut-busch.de/",
        "fallback_ranges": [
            ("2026-10-09", "2026-10-11"),
            ("2026-10-23", "2026-10-25"),
            ("2026-11-06", "2026-11-08"),
            ("2026-11-20", "2026-11-22"),
        ]
    },
    {
        "id": "schnapsdrossel",
        "title": "Zur Schnapsdrossel – Familie Mozer",
        "ort": "Pfedelbach-Gleichen (ca. 7 km)",
        "location": "Gleichener Str. 20, 74629 Pfedelbach",
        "hours": "Fr ab 16:00 Uhr, Sa ab 14:00 Uhr, So ab 11:30 Uhr",
        "color": "#935116",
        "url": "https://www.brennerei-mozer.de/",
        "fallback_ranges": [
            ("2026-10-16", "2026-10-18"),
            ("2026-10-30", "2026-11-01"),
            ("2026-11-13", "2026-11-15"),
            ("2026-11-27", "2026-11-29"),
        ]
    },
    {
        "id": "weihbrecht",
        "title": "Weingut Weihbrecht – Bretzfelder Besen",
        "ort": "Bretzfeld-Schwabbach (ca. 6 km)",
        "location": "Hauptstraße 45, 74626 Bretzfeld-Schwabbach",
        "hours": "Do-Sa ab 12:00 Uhr, So ab 11:00 Uhr",
        "color": "#117864",
        "url": "https://www.weingut-weihbrecht.de/",
        "fallback_ranges": [
            ("2026-10-01", "2026-10-04"),
            ("2026-10-15", "2026-10-18"),
            ("2026-10-29", "2026-11-01"),
            ("2026-11-12", "2026-11-15"),
        ]
    },
    {
        "id": "banzhaf",
        "title": "Weingut Banzhaf",
        "ort": "Pfedelbach-Untersteinbach (ca. 10 km)",
        "location": "Öhringer Str. 12, 74629 Pfedelbach",
        "hours": "Fr & Sa ab 15:00 Uhr, So ab 11:30 Uhr",
        "color": "#2874a6",
        "url": "https://www.weingut-banzhaf.de/",
        "fallback_ranges": [
            ("2026-10-09", "2026-10-11"),
            ("2026-10-23", "2026-10-25"),
            ("2026-11-06", "2026-11-08"),
            ("2026-11-20", "2026-11-22"),
        ]
    },
    {
        "id": "laicher",
        "title": "Weingut Laicher – Besenstube",
        "ort": "Obersulm-Willsbach (ca. 13 km)",
        "location": "Löwensteiner Str. 18, 74182 Obersulm",
        "hours": "Do-Sa ab 11:30 Uhr, So ab 11:00 Uhr",
        "color": "#4a235a",
        "url": "https://www.weingut-laicher.de/",
        "fallback_ranges": [
            ("2026-10-15", "2026-10-18"),
            ("2026-10-29", "2026-11-01"),
            ("2026-11-12", "2026-11-15"),
            ("2026-11-26", "2026-11-29"),
        ]
    }
]

def parse_dates_from_text(text, year=2026):
    """Sucht nach Datumsbereichen wie '24.09. bis 27.09.2026' oder '01.10. - 04.10.'"""
    results = []
    # Muster: DD.MM.(YYYY) bis/– DD.MM.(YYYY)
    pattern = r'(\d{1,2})\.(\d{1,2})\.?(?:\s*(\d{4}))?\s*(?:bis|[-–—])\s*(\d{1,2})\.(\d{1,2})\.(?:\s*(\d{4}))?'
    matches = re.finditer(pattern, text)
    for m in matches:
        d1, m1, y1, d2, m2, y2 = m.groups()
        yr1 = int(y1) if y1 else year
        yr2 = int(y2) if y2 else yr1
        try:
            start_dt = datetime(yr1, int(m1), int(d1))
            end_dt = datetime(yr2, int(m2), int(d2))
            if start_dt <= end_dt and (end_dt - start_dt).days <= 21:
                results.append((start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")))
        except ValueError:
            continue
    return results

def scrape_besen(besen_info):
    url = besen_info.get("url")
    found_ranges = []
    if url:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                text = soup.get_text(separator=" ")
                found_ranges = parse_dates_from_text(text)
        except Exception:
            pass

    # Wenn online nichts Neues/Gültiges gefunden wurde, Fallback-Termine nutzen
    if not found_ranges:
        found_ranges = besen_info.get("fallback_ranges", [])

    return found_ranges

def scrape_all_besen():
    all_events = []

    for b in BESEN_KATALOG:
        ranges = scrape_besen(b)
        for start_str, end_str in ranges:
            try:
                s_dt = datetime.strptime(start_str, "%Y-%m-%d")
                e_dt = datetime.strptime(end_str, "%Y-%m-%d")
                # FullCalendar benötigt exklusives Enddatum (+1 Tag)
                fc_end = (e_dt + timedelta(days=1)).strftime("%Y-%m-%d")

                event_obj = {
                    "id": f"{b['id']}_{start_str}",
                    "title": b["title"],
                    "ort": b["ort"],
                    "location": b["location"],
                    "hours": b["hours"],
                    "color": b["color"],
                    "start": start_str,
                    "end": fc_end,
                    "notes": f"Geöffnet von {s_dt.strftime('%d.%m.')} bis {e_dt.strftime('%d.%m.%Y')}."
                }
                all_events.append(event_obj)
            except Exception:
                continue

    all_events.sort(key=lambda x: x["start"])

    now_str = datetime.now().strftime("%d.%m.%Y um %H:%M Uhr")
    output_data = {
        "last_updated": now_str,
        "events": all_events
    }

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"Erfolg: {len(all_events)} Besentermine in events.json geschrieben.")

if __name__ == "__main__":
    scrape_all_besen()import json
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Vollständiger Katalog aller 11 Besenwirtschaften im Raum Öhringen
BESEN_KATALOG = [
    {
        "id": "borth",
        "title": "Weingut & Weinstube Borth",
        "ort": "Bretzfeld-Adolzfurt (ca. 7 km)",
        "location": "Unterheimbacher Straße 35, 74626 Bretzfeld-Adolzfurt",
        "hours": "Täglich ab 11:00 Uhr | Küche Do-Sa bis ca. 21:00 Uhr, So bis ca. 19:30 Uhr",
        "color": "#800020",
        "url": "https://www.weingut-borth.de/pages/oeffnungszeiten-speisekarte",
        "fallback_ranges": [
            ("2026-09-24", "2026-09-27"),
            ("2026-10-08", "2026-10-11"),
            ("2026-10-22", "2026-10-25"),
            ("2026-11-05", "2026-11-08"),
            ("2026-11-19", "2026-11-22"),
            ("2026-12-03", "2026-12-06"),
        ]
    },
    {
        "id": "schluchter",
        "title": "Schluchters Weinstube",
        "ort": "Pfedelbach-Baierbach (ca. 5 km)",
        "location": "Ruländerweg 3, 74629 Pfedelbach-Baierbach",
        "hours": "Fr & Sa ab 14:00 Uhr, So ab 11:30 Uhr (oder ab 12 Uhr)",
        "color": "#2c5e3b",
        "url": "https://www.schluchters-weinstube.de/oeffnungszeiten/",
        "fallback_ranges": [
            ("2026-09-18", "2026-09-20"),
            ("2026-10-02", "2026-10-04"),
            ("2026-10-16", "2026-10-18"),
            ("2026-10-30", "2026-11-01"),
            ("2026-11-13", "2026-11-15"),
            ("2026-11-27", "2026-11-29"),
        ]
    },
    {
        "id": "baldele",
        "title": "Weinstube Baldele",
        "ort": "Bretzfeld-Unterheimbach (ca. 9 km)",
        "location": "Waldbachstraße 16, 74626 Bretzfeld-Unterheimbach",
        "hours": "Täglich ab 11:00 Uhr | Besenküche durchgehend",
        "color": "#8b5a2b",
        "url": "http://www.weinstube-baldele.de/",
        "fallback_ranges": [
            ("2026-09-25", "2026-09-28"),
            ("2026-10-09", "2026-10-12"),
            ("2026-10-23", "2026-10-26"),
            ("2026-11-06", "2026-11-09"),
            ("2026-11-20", "2026-11-23"),
            ("2026-12-04", "2026-12-07"),
        ]
    },
    {
        "id": "schwab",
        "title": "Weingut Schwab – Weinstube",
        "ort": "Bretzfeld-Dimbach (ca. 6 km)",
        "location": "Schwabbacher Straße 4, 74626 Bretzfeld-Dimbach",
        "hours": "Do-Sa ab 11:30 Uhr, So & Feiertag ab 11:00 Uhr",
        "color": "#1a5276",
        "url": "https://www.weingut-schwab.de/",
        "fallback_ranges": [
            ("2026-10-01", "2026-10-04"),
            ("2026-10-15", "2026-10-18"),
            ("2026-10-29", "2026-11-01"),
            ("2026-11-12", "2026-11-15"),
            ("2026-11-26", "2026-11-29"),
            ("2026-12-10", "2026-12-13"),
        ]
    },
    {
        "id": "ungerer",
        "title": "Besenwirtschaft Ungerer",
        "ort": "Pfedelbach-Windischenbach (ca. 4 km)",
        "location": "Lindenstraße 12, 74629 Pfedelbach",
        "hours": "Do-Sa ab 11:30 Uhr, So ab 11:00 Uhr",
        "color": "#b03a2e",
        "url": "https://www.weingut-ungerer.de/",
        "fallback_ranges": [
            ("2026-10-08", "2026-10-11"),
            ("2026-10-22", "2026-10-25"),
            ("2026-11-05", "2026-11-08"),
            ("2026-11-19", "2026-11-22"),
        ]
    },
    {
        "id": "birkert",
        "title": "Weingut Birkert – Besenstüble",
        "ort": "Bretzfeld-Adolzfurt (ca. 7 km)",
        "location": "Schmiedgasse 14, 74626 Bretzfeld-Adolzfurt",
        "hours": "Fr & Sa ab 14:00 Uhr, So ab 11:30 Uhr",
        "color": "#6c3483",
        "url": "https://www.weingut-birkert.com/besenkalender/",
        "fallback_ranges": [
            ("2026-10-02", "2026-10-04"),
            ("2026-10-16", "2026-10-18"),
            ("2026-10-30", "2026-11-01"),
            ("2026-11-13", "2026-11-15"),
            ("2026-11-27", "2026-11-29"),
        ]
    },
    {
        "id": "busch",
        "title": "Besenwirtschaft Familie Busch",
        "ort": "Bretzfeld-Dimbach (ca. 6 km)",
        "location": "Waldenburger Str. 8, 74626 Bretzfeld-Dimbach",
        "hours": "Fr ab 15:00 Uhr, Sa ab 14:00 Uhr, So ab 11:30 Uhr",
        "color": "#784212",
        "url": "https://www.weingut-busch.de/",
        "fallback_ranges": [
            ("2026-10-09", "2026-10-11"),
            ("2026-10-23", "2026-10-25"),
            ("2026-11-06", "2026-11-08"),
            ("2026-11-20", "2026-11-22"),
        ]
    },
    {
        "id": "schnapsdrossel",
        "title": "Zur Schnapsdrossel – Familie Mozer",
        "ort": "Pfedelbach-Gleichen (ca. 7 km)",
        "location": "Gleichener Str. 20, 74629 Pfedelbach",
        "hours": "Fr ab 16:00 Uhr, Sa ab 14:00 Uhr, So ab 11:30 Uhr",
        "color": "#935116",
        "url": "https://www.brennerei-mozer.de/",
        "fallback_ranges": [
            ("2026-10-16", "2026-10-18"),
            ("2026-10-30", "2026-11-01"),
            ("2026-11-13", "2026-11-15"),
            ("2026-11-27", "2026-11-29"),
        ]
    },
    {
        "id": "weihbrecht",
        "title": "Weingut Weihbrecht – Bretzfelder Besen",
        "ort": "Bretzfeld-Schwabbach (ca. 6 km)",
        "location": "Hauptstraße 45, 74626 Bretzfeld-Schwabbach",
        "hours": "Do-Sa ab 12:00 Uhr, So ab 11:00 Uhr",
        "color": "#117864",
        "url": "https://www.weingut-weihbrecht.de/",
        "fallback_ranges": [
            ("2026-10-01", "2026-10-04"),
            ("2026-10-15", "2026-10-18"),
            ("2026-10-29", "2026-11-01"),
            ("2026-11-12", "2026-11-15"),
        ]
    },
    {
        "id": "banzhaf",
        "title": "Weingut Banzhaf",
        "ort": "Pfedelbach-Untersteinbach (ca. 10 km)",
        "location": "Öhringer Str. 12, 74629 Pfedelbach",
        "hours": "Fr & Sa ab 15:00 Uhr, So ab 11:30 Uhr",
        "color": "#2874a6",
        "url": "https://www.weingut-banzhaf.de/",
        "fallback_ranges": [
            ("2026-10-09", "2026-10-11"),
            ("2026-10-23", "2026-10-25"),
            ("2026-11-06", "2026-11-08"),
            ("2026-11-20", "2026-11-22"),
        ]
    },
    {
        "id": "laicher",
        "title": "Weingut Laicher – Besenstube",
        "ort": "Obersulm-Willsbach (ca. 13 km)",
        "location": "Löwensteiner Str. 18, 74182 Obersulm",
        "hours": "Do-Sa ab 11:30 Uhr, So ab 11:00 Uhr",
        "color": "#4a235a",
        "url": "https://www.weingut-laicher.de/",
        "fallback_ranges": [
            ("2026-10-15", "2026-10-18"),
            ("2026-10-29", "2026-11-01"),
            ("2026-11-12", "2026-11-15"),
            ("2026-11-26", "2026-11-29"),
        ]
    }
]

def parse_dates_from_text(text, year=2026):
    """Sucht nach Datumsbereichen wie '24.09. bis 27.09.2026' oder '01.10. - 04.10.'"""
    results = []
    # Muster: DD.MM.(YYYY) bis/– DD.MM.(YYYY)
    pattern = r'(\d{1,2})\.(\d{1,2})\.?(?:\s*(\d{4}))?\s*(?:bis|[-–—])\s*(\d{1,2})\.(\d{1,2})\.(?:\s*(\d{4}))?'
    matches = re.finditer(pattern, text)
    for m in matches:
        d1, m1, y1, d2, m2, y2 = m.groups()
        yr1 = int(y1) if y1 else year
        yr2 = int(y2) if y2 else yr1
        try:
            start_dt = datetime(yr1, int(m1), int(d1))
            end_dt = datetime(yr2, int(m2), int(d2))
            if start_dt <= end_dt and (end_dt - start_dt).days <= 21:
                results.append((start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")))
        except ValueError:
            continue
    return results

def scrape_besen(besen_info):
    url = besen_info.get("url")
    found_ranges = []
    if url:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                text = soup.get_text(separator=" ")
                found_ranges = parse_dates_from_text(text)
        except Exception:
            pass

    # Wenn online nichts Neues/Gültiges gefunden wurde, Fallback-Termine nutzen
    if not found_ranges:
        found_ranges = besen_info.get("fallback_ranges", [])

    return found_ranges

def scrape_all_besen():
    all_events = []

    for b in BESEN_KATALOG:
        ranges = scrape_besen(b)
        for start_str, end_str in ranges:
            try:
                s_dt = datetime.strptime(start_str, "%Y-%m-%d")
                e_dt = datetime.strptime(end_str, "%Y-%m-%d")
                # FullCalendar benötigt exklusives Enddatum (+1 Tag)
                fc_end = (e_dt + timedelta(days=1)).strftime("%Y-%m-%d")

                event_obj = {
                    "id": f"{b['id']}_{start_str}",
                    "title": b["title"],
                    "ort": b["ort"],
                    "location": b["location"],
                    "hours": b["hours"],
                    "color": b["color"],
                    "start": start_str,
                    "end": fc_end,
                    "notes": f"Geöffnet von {s_dt.strftime('%d.%m.')} bis {e_dt.strftime('%d.%m.%Y')}."
                }
                all_events.append(event_obj)
            except Exception:
                continue

    all_events.sort(key=lambda x: x["start"])

    now_str = datetime.now().strftime("%d.%m.%Y um %H:%M Uhr")
    output_data = {
        "last_updated": now_str,
        "events": all_events
    }

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"Erfolg: {len(all_events)} Besentermine in events.json geschrieben.")

if __name__ == "__main__":
    scrape_all_besen()
