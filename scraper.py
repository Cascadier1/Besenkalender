import json
from datetime import datetime, timedelta

# Echte, verifizierte Besenwirtschaften im Umkreis von Öhringen (ca. 15 km)
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
        "title": "Weinstube Schwab",
        "ort": "Bretzfeld-Dimbach (ca. 7 km)",
        "location": "Lindelbergstraße 4, 74626 Bretzfeld-Dimbach",
        "hours": "Täglich geöffnet während der Besenzeiten",
        "color": "#8b5a2b",
        "url": "https://weinstube-schwab.de/",
        "dates": [
            ("2026-01-09", "2026-01-18"),
            ("2026-02-20", "2026-03-01"),
            ("2026-04-03", "2026-04-12"),
            ("2026-05-08", "2026-05-17"),
            ("2026-08-28", "2026-09-06"),
            ("2026-10-09", "2026-10-18"),
            ("2026-11-20", "2026-11-29"),
        ]
    },
    {
        "id": "ungerer",
        "title": "Weingut & Besen Ungerer",
        "ort": "Bretzfeld-Schwabbach (ca. 6 km)",
        "location": "Rappengasse 13, 74626 Bretzfeld-Schwabbach",
        "hours": "Do - Sa ab 11:30 Uhr, So ab 11:00 Uhr",
        "color": "#b86b27",
        "url": "https://www.weingut-ungerer.de/",
        "dates": [
            ("2026-01-29", "2026-02-01"),
            ("2026-02-26", "2026-03-01"),
            ("2026-04-09", "2026-04-12"),
            ("2026-10-08", "2026-10-11"),
            ("2026-11-05", "2026-11-08"),
        ]
    },
    {
        "id": "schluchter",
        "title": "Weingut Schluchter Besenstube",
        "ort": "Bretzfeld-Geddelsbach (ca. 11 km)",
        "location": "Öhringer Str. 12, 74626 Bretzfeld-Geddelsbach",
        "hours": "Fr & Sa ab 11:30 Uhr, So & Feiertage ab 11:00 Uhr",
        "color": "#4a2c5a",
        "url": "https://weingut-schluchter.de/",
        "dates": [
            ("2026-01-08", "2026-01-11"),
            ("2026-02-05", "2026-02-08"),
            ("2026-03-05", "2026-03-08"),
            ("2026-04-02", "2026-04-05"),
            ("2026-10-01", "2026-10-04"),
            ("2026-11-05", "2026-11-08"),
            ("2026-12-03", "2026-12-06"),
        ]
    },
    {
        "id": "baldele",
        "title": "Baldele's Weinstube",
        "ort": "Öhringen-Michelbach (ca. 4 km)",
        "location": "Obersteinbacher Str. 23, 74613 Öhringen-Michelbach",
        "hours": "Fr ab 17:00 Uhr, Sa & So ab 11:00 Uhr",
        "color": "#2c5e3b",
        "url": "http://www.baldeles-weinstube.de/",
        "dates": []
    }
]

def main():
    events = []
    
    for b in BESEN_KATALOG:
        for start_str, end_str in b.get("dates", []):
            try:
                d_start = datetime.strptime(start_str, "%Y-%m-%d")
                d_end = datetime.strptime(end_str, "%Y-%m-%d")
                
                # FullCalendar benötigt end_date + 1 Tag für die allDay-Darstellung
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

    print(f"events.json erfolgreich mit {len(events)} Terminen geschrieben.")

if __name__ == "__main__":
    main()import json
from datetime import datetime, timedelta

# Echte, verifizierte Besenwirtschaften im Umkreis von Öhringen (ca. 15 km)
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
        "title": "Weinstube Schwab",
        "ort": "Bretzfeld-Dimbach (ca. 7 km)",
        "location": "Lindelbergstraße 4, 74626 Bretzfeld-Dimbach",
        "hours": "Täglich geöffnet während der Besenzeiten",
        "color": "#8b5a2b",
        "url": "https://weinstube-schwab.de/",
        "dates": [
            ("2026-01-09", "2026-01-18"),
            ("2026-02-20", "2026-03-01"),
            ("2026-04-03", "2026-04-12"),
            ("2026-05-08", "2026-05-17"),
            ("2026-08-28", "2026-09-06"),
            ("2026-10-09", "2026-10-18"),
            ("2026-11-20", "2026-11-29"),
        ]
    },
    {
        "id": "ungerer",
        "title": "Weingut & Besen Ungerer",
        "ort": "Bretzfeld-Schwabbach (ca. 6 km)",
        "location": "Rappengasse 13, 74626 Bretzfeld-Schwabbach",
        "hours": "Do - Sa ab 11:30 Uhr, So ab 11:00 Uhr",
        "color": "#b86b27",
        "url": "https://www.weingut-ungerer.de/",
        "dates": [
            ("2026-01-29", "2026-02-01"),
            ("2026-02-26", "2026-03-01"),
            ("2026-04-09", "2026-04-12"),
            ("2026-10-08", "2026-10-11"),
            ("2026-11-05", "2026-11-08"),
        ]
    },
    {
        "id": "schluchter",
        "title": "Weingut Schluchter Besenstube",
        "ort": "Bretzfeld-Geddelsbach (ca. 11 km)",
        "location": "Öhringer Str. 12, 74626 Bretzfeld-Geddelsbach",
        "hours": "Fr & Sa ab 11:30 Uhr, So & Feiertage ab 11:00 Uhr",
        "color": "#4a2c5a",
        "url": "https://weingut-schluchter.de/",
        "dates": [
            ("2026-01-08", "2026-01-11"),
            ("2026-02-05", "2026-02-08"),
            ("2026-03-05", "2026-03-08"),
            ("2026-04-02", "2026-04-05"),
            ("2026-10-01", "2026-10-04"),
            ("2026-11-05", "2026-11-08"),
            ("2026-12-03", "2026-12-06"),
        ]
    },
    {
        "id": "baldele",
        "title": "Baldele's Weinstube",
        "ort": "Öhringen-Michelbach (ca. 4 km)",
        "location": "Obersteinbacher Str. 23, 74613 Öhringen-Michelbach",
        "hours": "Fr ab 17:00 Uhr, Sa & So ab 11:00 Uhr",
        "color": "#2c5e3b",
        "url": "http://www.baldeles-weinstube.de/",
        "dates": []
    }
]

def main():
    events = []
    
    for b in BESEN_KATALOG:
        for start_str, end_str in b.get("dates", []):
            try:
                d_start = datetime.strptime(start_str, "%Y-%m-%d")
                d_end = datetime.strptime(end_str, "%Y-%m-%d")
                
                # FullCalendar benötigt end_date + 1 Tag für die allDay-Darstellung
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

    print(f"events.json erfolgreich mit {len(events)} Terminen geschrieben.")

if __name__ == "__main__":
    main()
