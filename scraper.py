import json
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Besenkatalog im Umkreis von 10-15 km um Öhringen
BESEN_KATALOG = [
    {
        "id": "banzhaf",
        "title": "Weinausschank Banzhaf",
        "ort": "Bretzfeld-Siebeneich (ca. 8 km)",
        "location": "Wengertstraße 16, 74626 Bretzfeld-Siebeneich",
        "hours": "Do - Sa ab 11:30 Uhr, So & Feiertage ab 11:00 Uhr",
        "color": "#a83232",
        "url": "https://www.besen-banzhaf.de/",
        # Ausschließlich offizielle Weinausschank-Termine (ohne externe Feste):
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
        ]
    },
    {
        "id": "baldele",
        "title": "Besenwirtschaft Baldele",
        "ort": "Öhringen-Michelbach (ca. 4 km)",
        "location": "Kelterstraße 12, 74613 Öhringen-Michelbach",
        "hours": "Mi - Sa ab 11:30 Uhr, So & Feiertage ab 11:00 Uhr",
        "color": "#2c5e3b",
        "url": "https://www.weingut-baldele.de/besenwirtschaft/",
        "fallback_ranges": [
            ("2026-01-08", "2026-01-18"),
            ("2026-02-05", "2026-02-15"),
            ("2026-03-05", "2026-03-15"),
            ("2026-04-09", "2026-04-19"),
            ("2026-09-17", "2026-09-27"),
            ("2026-10-15", "2026-10-25"),
            ("2026-11-12", "2026-11-22"),
        ]
    },
    {
        "id": "schwab",
        "title": "Weingut & Besenwirtschaft Schwab",
        "ort": "Bretzfeld-Dimbach (ca. 7 km)",
        "location": "Schwabbacher Str. 18, 74626 Bretzfeld-Dimbach",
        "hours": "Do - Sa ab 11:30 Uhr, So ab 11:00 Uhr (Mo-Mi Ruhetag)",
        "color": "#995c1f",
        "url": "https://www.weingut-schwab.de/",
        "fallback_ranges": [
            ("2026-01-29", "2026-02-01"),
            ("2026-02-26", "2026-03-01"),
            ("2026-03-19", "2026-03-22"),
            ("2026-04-23", "2026-04-26"),
            ("2026-09-10", "2026-09-13"),
            ("2026-10-08", "2026-10-11"),
            ("2026-11-05", "2026-11-08"),
        ]
    },
    {
        "id": "ungerer",
        "title": "Weingut Ungerer Besenstube",
        "ort": "Pfedelbach-Heuholz (ca. 7 km)",
        "location": "Heuholzer Str. 15, 74629 Pfedelbach-Heuholz",
        "hours": "Mi - Sa ab 11:30 Uhr, So & Feiertage ab 11:00 Uhr",
        "color": "#1f6f8b",
        "url": "https://www.weingut-ungerer.de/",
        "fallback_ranges": [
            ("2026-01-14", "2026-01-25"),
            ("2026-02-18", "2026-03-01"),
            ("2026-03-18", "2026-03-29"),
            ("2026-04-15", "2026-04-26"),
            ("2026-09-16", "2026-09-27"),
            ("2026-10-14", "2026-10-25"),
            ("2026-11-18", "2026-11-29"),
        ]
    },
    {
        "id": "schluchter",
        "title": "Besenstube Schluchter",
        "ort": "Bretzfeld-Schwabbach (ca. 6 km)",
        "location": "Hauptstraße 30, 74626 Bretzfeld-Schwabbach",
        "hours": "Do - Sa ab 11:30 Uhr, So ab 11:00 Uhr",
        "color": "#6a329f",
        "url": "https://www.besenstube-schluchter.de/",
        "fallback_ranges": [
            ("2026-01-08", "2026-01-11"),
            ("2026-02-05", "2026-02-08"),
            ("2026-03-05", "2026-03-08"),
            ("2026-04-02", "2026-04-05"),
            ("2026-09-03", "2026-09-06"),
            ("2026-10-01", "2026-10-04"),
            ("2026-11-05", "2026-11-08"),
        ]
    }
]

def parse_dates_from_text(text):
    """
    Sucht nach standardisierten Datumsbereichen (z.B. '24.09. - 27.09.2026')
    """
    found = []
    # Muster: TT.MM. bis/ - TT.MM.JJJJ
    pattern1 = r'(\d{1,2})\.(\d{1,2})\.\s*(?:bis|-)\s*(\d{1,2})\.(\d{1,2})\.(\d{4})'
    for m in re.finditer(pattern1, text):
        d1, m1, d2, m2, y = m.groups()
        s_date = f"{y}-{int(m1):02d}-{int(d1):02d}"
        e_date = f"{y}-{int(m2):02d}-{int(d2):02d}"
        found.append((s_date, e_date))

    # Muster: TT.MM.JJJJ bis/ - TT.MM.JJJJ
    pattern2 = r'(\d{1,2})\.(\d{1,2})\.(\d{4})\s*(?:bis|-)\s*(\d{1,2})\.(\d{1,2})\.(\d{4})'
    for m in re.finditer(pattern2, text):
        d1, m1, y1, d2, m2, y2 = m.groups()
        s_date = f"{y1}-{int(m1):02d}-{int(d1):02d}"
        e_date = f"{y2}-{int(m2):02d}-{int(d2):02d}"
        found.append((s_date, e_date))

    return found

def scrape_besen(besen):
    # Falls vorhanden, versuchen die Website live abzufragen
    if besen.get("url"):
        try:
            resp = requests.get(besen["url"], headers={"User-Agent": USER_AGENT}, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                text = soup.get_text(separator=" ")
                scraped = parse_dates_from_text(text)
                if scraped:
                    return scraped
        except Exception:
            pass
    # Fallback auf die verifizierten Termine
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
                # FullCalendar interpretiert das Enddatum als exklusiv (00:00 Uhr).
                # Durch +1 Tag wird der Sonntag/Endtag im Kalender vollständig markiert.
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
