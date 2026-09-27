import json
from datetime import datetime, timedelta

# Echte, verifizierte Besenwirtschaften im Umkreis von Öhringen
BESEN_KATALOG = [
    {
        "id": "banzhaf",
        "title": "Weinausschank Banzhaf",
        "ort": "Bretzfeld-Siebeneich (ca. 8 km)",
        "location": "Wengertstraße 16, 74626 Bretzfeld-Siebeneich",
        "hours": "Do - Sa ab 11:30 Uhr, So & Feiertage ab 11:00 Uhr",
        "color": "#a83232",
        "url": "https://www.besen-banzhaf.de/",
        "dates": [
            ("2026-01-22", "2026-01-25"),
            ("2026-02-19", "2026-02-22"),
            ("2026-03-26", "2026-03-29"),
            ("2026-04-23", "2026-04-26"),
            ("2026-05-14", "2026-05-17"),
            ("2026-08-06", "2026-08-09"),
            ("2026-09-03", "2026-09-06"),
            ("2026-10-15", "2026-10-18"),
            ("2026-11-12", "2026-11-15"),
            ("2026-12-07", "2026-12-13"),
        ]
    },
    {
        "id": "borth",
        "title": "Weingut & Weinstube Borth",
        "ort": "Bretzfeld-Adolzfurt (ca. 9 km)",
        "location": "Unterheimbacher Str. 35, 74626 Bretzfeld-Adolzfurt",
        "hours": "Do - Sa ab 11:00 Uhr (Küche bis 21:00), So ab 11:00 Uhr (Küche bis 19:30)",
        "color": "#722f37",
        "url": "https://www.weingut-borth.de/pages/offnungszeiten-aktuelle-speisen",
        "dates": [
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
        "dates": [
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
        "dates": [
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
        "dates": [
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
        "hours": "Fr ab 17:00 Uhr, Sa & So ab 11:00 Uhr (ca. 2 WE im Monat)",
        "color": "#2c5e3b",
        "url": "http://www.baldeles-weinstube.de/",
        "dates": []  # Keine festen Jahrestermine hinterlegt
    }
]

def main():
    events = []
    
    for b in BESEN_KATALOG:
        for start_str, end_str in b.get("dates", []):
            try:
                d_start = datetime.strptime(start_str, "%Y-%m-%d")
                d_end = datetime.strptime(end_str, "%Y-%m-%d")
                
                # FullCalendar benötigt end_date + 1 Tag, damit der letzte Tag mit ausgefüllt wird
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
                print(f"Fehler bei {b['id']}: {e}")

    output = {
        "last_updated": datetime.now().strftime("%d.%m.%Y um %H:%M Uhr"),
        "events": events
    }

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"events.json erfolgreich mit {len(events)} Terminen generiert.")

if __name__ == "__main__":
    main()
