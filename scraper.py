import json
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# -------------------------------------------------------------
# Stammdaten & bekannte Jahres-Termine der Besenwirtschaften
# -------------------------------------------------------------
BESEN_KATALOG = [
    {
        "id": "borth",
        "title": "Weingut & Weinstube Borth",
        "ort": "Bretzfeld-Adolzfurt (ca. 7 km)",
        "location": "Unterheimbacher Straße 35, 74626 Bretzfeld-Adolzfurt",
        "hours": "Täglich ab 11:00 Uhr | Küche Do-Sa bis ca. 21:00 Uhr, So bis ca. 19:30 Uhr",
        "color": "#831843",
        "url": "https://www.weingut-borth.de/pages/offnungszeiten-aktuelle-speisen",
        "default_blocks": [
            ("2026-09-24", "2026-09-27"),
            ("2026-10-15", "2026-10-18"),
            ("2026-11-12", "2026-11-15"),
            ("2026-12-03", "2026-12-06"),
            ("2027-01-14", "2027-01-17"),
            ("2027-02-18", "2027-02-21"),
            ("2027-03-18", "2027-03-21"),
            ("2027-04-15", "2027-04-18")
        ]
    },
    {
        "id": "schluchter",
        "title": "Schluchter's Weinstube",
        "ort": "Pfedelbach-Baierbach (ca. 7 km)",
        "location": "Ruländerweg 3, 74629 Pfedelbach-Baierbach",
        "hours": "Fr & Sa ab 11:30 Uhr | So ab 11:00 Uhr",
        "color": "#15803d",
        "url": "https://www.schluchters-weinstube.de",
        "default_blocks": [
            ("2026-09-18", "2026-09-20"),
            ("2026-10-02", "2026-10-04"),
            ("2026-10-16", "2026-10-18"),
            ("2026-11-06", "2026-11-08"),
            ("2026-11-20", "2026-11-22"),
            ("2026-12-04", "2026-12-06"),
            ("2027-01-15", "2027-01-17"),
            ("2027-02-05", "2027-02-07"),
            ("2027-03-05", "2027-03-07")
        ]
    },
    {
        "id": "ungerer",
        "title": "Weingut & Weinstube Ungerer",
        "ort": "Pfedelbach-Renzen (ca. 8 km)",
        "location": "Harsberger Straße 15, 74629 Pfedelbach-Renzen",
        "hours": "Di bis So täglich ab 11:00 Uhr (Mo Ruhetag)",
        "color": "#b45309",
        "url": "https://www.weingut-ungerer.de",
        "default_blocks": [
            ("2026-09-08", "2026-09-13"),
            ("2026-11-03", "2026-11-08"),
            ("2026-12-01", "2026-12-06"),
            ("2027-01-12", "2027-01-17"),
            ("2027-02-09", "2027-02-14"),
            ("2027-03-09", "2027-03-14"),
            ("2027-04-06", "2027-04-11")
        ]
    },
    {
        "id": "schnapsdrossel",
        "title": "Besenwirtschaft Die Schnapsdrossel",
        "ort": "Pfedelbach (ca. 4 km)",
        "location": "Pfedelbacher Str. 15, 74629 Pfedelbach",
        "hours": "Fr & Sa ab 17:00 Uhr | So 11:00-14:00 & 17:00-22:00 Uhr",
        "color": "#0369a1",
        "url": "https://www.dieschnapsdrossel.de",
        "default_blocks": [
            ("2026-10-09", "2026-10-11"),
            ("2026-11-06", "2026-11-08"),
            ("2026-12-04", "2026-12-06"),
            ("2027-01-08", "2027-01-10"),
            ("2027-02-12", "2027-02-14"),
            ("2027-03-12", "2027-03-14")
        ]
    },
    {
        "id": "schwab",
        "title": "Weingut & Weinstube Schwab",
        "ort": "Bretzfeld-Dimbach (ca. 7 km)",
        "location": "Wassergasse 2-4, 74626 Bretzfeld-Dimbach",
        "hours": "Do bis Mo ab 11:30 Uhr durchgehend geöffnet",
        "color": "#7c2d12",
        "url": "https://www.weingut-schwab.de",
        "default_blocks": [
            ("2026-10-08", "2026-10-12"),
            ("2026-11-19", "2026-11-23"),
            ("2026-12-10", "2026-12-14"),
            ("2027-01-21", "2027-01-25"),
            ("2027-02-18", "2027-02-22"),
            ("2027-03-18", "2027-03-22")
        ]
    },
    {
        "id": "birkert",
        "title": "Besenwirtschaft Birkert",
        "ort": "Bretzfeld-Adolzfurt (ca. 7 km)",
        "location": "Unterheimbacher Str. 28, 74626 Bretzfeld-Adolzfurt",
        "hours": "Täglich ab 11:30 Uhr geöffnet",
        "color": "#4c1d95",
        "url": "https://www.weingut-birkert.de",
        "default_blocks": [
            ("2026-10-01", "2026-10-05"),
            ("2026-11-05", "2026-11-09"),
            ("2027-01-07", "2027-01-11"),
            ("2027-02-04", "2027-02-08"),
            ("2027-03-04", "2027-03-08")
        ]
    },
    {
        "id": "busch",
        "title": "Weinstube Busch",
        "ort": "Bretzfeld-Dimbach (ca. 8 km)",
        "location": "Greuthof 1, 74626 Bretzfeld-Dimbach",
        "hours": "Fr & Sa ab 14:00 Uhr | So & Feiertag ab 11:30 Uhr",
        "color": "#065f46",
        "url": "https://www.weinstube-busch.de",
        "default_blocks": [
            ("2026-10-02", "2026-10-04"),
            ("2026-10-23", "2026-10-25"),
            ("2026-11-13", "2026-11-15"),
            ("2026-12-04", "2026-12-06"),
            ("2027-01-15", "2027-01-17"),
            ("2027-02-19", "2027-02-21")
        ]
    },
    {
        "id": "weihbrecht",
        "title": "Weinstube Weihbrecht",
        "ort": "Bretzfeld-Schwabbach (ca. 6 km)",
        "location": "Hauptstraße 20, 74626 Bretzfeld-Schwabbach",
        "hours": "Do bis So ab 11:30 Uhr",
        "color": "#c2410c",
        "url": "https://www.weingut-weihbrecht.de",
        "default_blocks": [
            ("2026-10-15", "2026-10-18"),
            ("2026-11-12", "2026-11-15"),
            ("2026-12-10", "2026-12-13"),
            ("2027-01-21", "2027-01-24"),
            ("2027-02-18", "2027-02-21")
        ]
    },
    {
        "id": "banzhaf",
        "title": "Weinausschank Banzhaf",
        "ort": "Bretzfeld-Siebeneich (ca. 6 km)",
        "location": "Wengertstraße 16, 74626 Bretzfeld-Siebeneich",
        "hours": "Fr ab 16:00 Uhr | Sa & So ab 11:30 Uhr",
        "color": "#9d174d",
        "url": "https://www.weingut-banzhaf.de",
        "default_blocks": [
            ("2026-10-09", "2026-10-11"),
            ("2026-11-06", "2026-11-08"),
            ("2026-12-04", "2026-12-06"),
            ("2027-01-08", "2027-01-10"),
            ("2027-02-05", "2027-02-07")
        ]
    },
    {
        "id": "baldele",
        "title": "Baldele's Weinstube",
        "ort": "Öhringen-Cappel (ca. 2 km)",
        "location": "Obersteinbacher Straße 23, 74613 Öhringen-Cappel",
        "hours": "Fr & Sa ab 16:00 Uhr | So ab 11:30 Uhr | Mo ab 16:00 Uhr",
        "color": "#991b1b",
        "url": None,
        "default_blocks": [
            ("2026-10-02", "2026-10-05"),
            ("2026-11-06", "2026-11-09"),
            ("2026-12-04", "2026-12-07"),
            ("2027-01-08", "2027-01-11"),
            ("2027-02-05", "2027-02-08")
        ]
    },
    {
        "id": "laicher",
        "title": "Besenwirtschaft Laicher",
        "ort": "Obersulm-Willsbach (ca. 14 km)",
        "location": "Heerweg 21, 74182 Obersulm",
        "hours": "Täglich ab 11:30 Uhr geöffnet",
        "color": "#1e3a8a",
        "url": "https://www.weingut-laicher.de",
        "default_blocks": [
            ("2026-10-15", "2026-10-25"),
            ("2026-11-12", "2026-11-22"),
            ("2027-01-14", "2027-01-24"),
            ("2027-02-11", "2027-02-21")
        ]
    }
]

def find_all_date_ranges(text):
    """Findet alle Zeiträume im Format TT.MM. - TT.MM.JJJJ oder TT.MM.JJJJ - TT.MM.JJJJ"""
    monate = {
        "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4,
        "mai": 5, "juni": 6, "juli": 7, "august": 8, "september": 9,
        "oktober": 10, "november": 11, "dezember": 12
    }
    
    found_ranges = []
    
    # 1. Format: 24.09.2026 - 27.09.2026 oder 24.09. - 27.09.2026
    p1 = re.compile(r'(\d{1,2})\.(\d{1,2})\.?(?:(\d{4}))?\s*(?:bis|-)\s*(\d{1,2})\.(\d{1,2})\.(\d{4})', re.IGNORECASE)
    for match in p1.finditer(text):
        s_d, s_m, s_y, e_d, e_m, e_y = match.groups()
        s_y = int(s_y) if s_y else int(e_y)
        try:
            start_dt = datetime(s_y, int(s_m), int(s_d))
            end_dt = datetime(int(e_y), int(e_m), int(e_d))
            if start_dt <= end_dt:
                found_ranges.append((start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")))
        except ValueError:
            continue

    # 2. Format: 24. bis 27. September 2026
    p2 = re.compile(r'(\d{1,2})\.?\s*(?:bis|-)\s*(\d{1,2})\.\s*([a-zäöü]+)\s*(\d{4})', re.IGNORECASE)
    for match in p2.finditer(text):
        s_d, e_d, m_str, year = match.groups()
        m_str = m_str.lower()
        if m_str in monate:
            try:
                m_num = monate[m_str]
                start_dt = datetime(int(year), m_num, int(s_d))
                end_dt = datetime(int(year), m_num, int(e_d))
                if start_dt <= end_dt:
                    found_ranges.append((start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")))
            except ValueError:
                continue

    return list(set(found_ranges))

def scrape_all_besen():
    all_events = []

    for b in BESEN_KATALOG:
        blocks = list(b.get("default_blocks", []))

        if b["url"]:
            print(f"Scrape {b['title']}...")
            try:
                resp = requests.get(b["url"], headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    text = soup.get_text()
                    scraped_blocks = find_all_date_ranges(text)
                    if scraped_blocks:
                        # Gefundene Termine mit aufnehmen (Duplikate vermeiden)
                        for sb in scraped_blocks:
                            if sb not in blocks:
                                blocks.append(sb)
                        print(f" -> {len(scraped_blocks)} Termine auf Website gefunden!")
            except Exception as e:
                print(f" -> Fehler beim Abrufen: {e}")

        # Für jeden Terminblock einen Eintrag erstellen
        for start_str, end_str in blocks:
            s_dt = datetime.strptime(start_str, "%Y-%m-%d")
            e_dt = datetime.strptime(end_str, "%Y-%m-%d")
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

    # Nach Startdatum sortieren
    all_events.sort(key=lambda x: x["start"])

    now_str = datetime.now().strftime("%d.%m.%Y um %H:%M Uhr")
    output_data = {
        "last_updated": now_str,
        "events": all_events
    }

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"Fertig! Insgesamt {len(all_events)} Besentermine gespeichert.")

if __name__ == "__main__":
    scrape_all_besen()import json
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# -------------------------------------------------------------
# Stammdaten aller Besenwirtschaften im 15-km-Umkreis um Öhringen
# -------------------------------------------------------------
BESEN_LISTE = [
    {
        "id": "borth",
        "title": "Weingut & Weinstube Borth",
        "ort": "Bretzfeld-Adolzfurt (ca. 7 km)",
        "location": "Unterheimbacher Straße 35, 74626 Bretzfeld-Adolzfurt",
        "hours": "Täglich ab 11:00 Uhr | Küche Do-Sa bis ca. 21:00 Uhr, So bis ca. 19:30 Uhr",
        "color": "#831843",
        "url": "https://www.weingut-borth.de/pages/offnungszeiten-aktuelle-speisen"
    },
    {
        "id": "schluchter",
        "title": "Schluchter's Weinstube",
        "ort": "Pfedelbach-Baierbach (ca. 7 km)",
        "location": "Ruländerweg 3, 74629 Pfedelbach-Baierbach",
        "hours": "Mo bis Sa ab 11:30 Uhr | So ab 11:00 Uhr (an Besentagen)",
        "color": "#15803d",
        "url": "https://www.schluchters-weinstube.de"
    },
    {
        "id": "ungerer",
        "title": "Weingut & Weinstube Ungerer",
        "ort": "Pfedelbach-Renzen (ca. 8 km)",
        "location": "Harsberger Straße 15, 74629 Pfedelbach-Renzen",
        "hours": "Di bis So täglich ab 11:00 Uhr (Montag Ruhetag)",
        "color": "#b45309",
        "url": "https://www.weingut-ungerer.de"
    },
    {
        "id": "schnapsdrossel",
        "title": "Besenwirtschaft Die Schnapsdrossel",
        "ort": "Pfedelbach (ca. 4 km)",
        "location": "Pfedelbacher Str. 15, 74629 Pfedelbach",
        "hours": "Do & Fr ab 16:30 Uhr | Sa & So ab 11:30 Uhr",
        "color": "#0369a1",
        "url": "https://www.dieschnapsdrossel.de"
    },
    {
        "id": "schwab",
        "title": "Weingut & Weinstube Schwab",
        "ort": "Bretzfeld-Dimbach (ca. 7 km)",
        "location": "Wassergasse 2-4, 74626 Bretzfeld-Dimbach",
        "hours": "Do bis Mo ab 11:30 Uhr durchgehend",
        "color": "#7c2d12",
        "url": "https://www.weingut-schwab.de"
    },
    {
        "id": "birkert",
        "title": "Besenwirtschaft Birkert",
        "ort": "Bretzfeld-Adolzfurt (ca. 7 km)",
        "location": "Unterheimbacher Str. 28, 74626 Bretzfeld-Adolzfurt",
        "hours": "Täglich ab 11:30 Uhr",
        "color": "#4c1d95",
        "url": "https://www.weingut-birkert.de"
    },
    {
        "id": "busch",
        "title": "Weinstube Busch",
        "ort": "Bretzfeld-Dimbach (ca. 8 km)",
        "location": "Greuthof 1, 74626 Bretzfeld-Dimbach",
        "hours": "Fr & Sa ab 14:00 Uhr | So & Feiertag ab 11:30 Uhr",
        "color": "#065f46",
        "url": "https://www.weinstube-busch.de"
    },
    {
        "id": "weihbrecht",
        "title": "Weinstube Weihbrecht",
        "ort": "Bretzfeld-Schwabbach (ca. 6 km)",
        "location": "Hauptstraße 20, 74626 Bretzfeld-Schwabbach",
        "hours": "Do bis So ab 11:30 Uhr",
        "color": "#c2410c",
        "url": "https://www.weingut-weihbrecht.de"
    },
    {
        "id": "banzhaf",
        "title": "Weinausschank Banzhaf",
        "ort": "Bretzfeld-Siebeneich (ca. 6 km)",
        "location": "Wengertstraße 16, 74626 Bretzfeld-Siebeneich",
        "hours": "Fr ab 16:00 Uhr | Sa & So ab 11:30 Uhr",
        "color": "#9d174d",
        "url": "https://www.weingut-banzhaf.de"
    },
    {
        "id": "baldele",
        "title": "Baldele's Weinstube",
        "ort": "Öhringen-Cappel (ca. 2 km)",
        "location": "Obersteinbacher Straße 23, 74613 Öhringen-Cappel",
        "hours": "Fr & Sa ab 16:00 Uhr | So ab 11:30 Uhr | Mo ab 16:00 Uhr",
        "color": "#991b1b",
        "url": None
    },
    {
        "id": "laicher",
        "title": "Besenwirtschaft Laicher",
        "ort": "Obersulm-Willsbach (ca. 14 km)",
        "location": "Heerweg 21, 74182 Obersulm",
        "hours": "Täglich ab 11:30 Uhr geöffnet",
        "color": "#1e3a8a",
        "url": "https://www.weingut-laicher.de"
    }
]

def parse_dates_from_text(text):
    monate = {
        "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4,
        "mai": 5, "juni": 6, "juli": 7, "august": 8, "september": 9,
        "oktober": 10, "november": 11, "dezember": 12
    }

    # Format 1: 24.09. - 27.09.2026 oder 24.09. bis 27.09.2026
    m1 = re.search(r'(\d{1,2})\.(\d{1,2})\.?\s*(?:bis|-)\s*(\d{1,2})\.(\d{1,2})\.(\d{4})', text, re.IGNORECASE)
    if m1:
        s_day, s_mon, e_day, e_mon, year = [int(x) for x in m1.groups()]
        try:
            return datetime(year, s_mon, s_day), datetime(year, e_mon, e_day)
        except ValueError:
            pass

    # Format 2: 24. bis 27. September 2026
    m2 = re.search(r'(\d{1,2})\.?\s*(?:bis|-)\s*(\d{1,2})\.\s*([a-zäöü]+)\s*(\d{4})', text, re.IGNORECASE)
    if m2:
        s_day, e_day, mon_str, year = m2.groups()
        mon_str = mon_str.lower()
        if mon_str in monate:
            try:
                mon_idx = monate[mon_str]
                return datetime(int(year), mon_idx, int(s_day)), datetime(int(year), mon_idx, int(e_day))
            except ValueError:
                pass

    return None, None

def scrape_all_besen():
    current_events = {}
    try:
        with open("events.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                current_events[item["id"]] = item
    except Exception:
        pass

    results = []

    for b in BESEN_LISTE:
        bid = b["id"]
        event_entry = current_events.get(bid, {
            "id": bid,
            "title": b["title"],
            "ort": b["ort"],
            "location": b["location"],
            "hours": b["hours"],
            "color": b["color"],
            "start": "2026-10-01",
            "end": "2026-10-06",
            "notes": "Öffnungszeiten laut Aushang / Homepage."
        })

        # Felder sicherstellen
        event_entry["title"] = b["title"]
        event_entry["ort"] = b["ort"]
        event_entry["location"] = b["location"]
        event_entry["hours"] = b["hours"]
        event_entry["color"] = b["color"]

        if b["url"]:
            print(f"Prüfe {b['title']}...")
            try:
                resp = requests.get(b["url"], headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    text = soup.get_text()
                    start_date, end_date = parse_dates_from_text(text)

                    if start_date and end_date:
                        fc_end = end_date + timedelta(days=1)
                        event_entry["start"] = start_date.strftime("%Y-%m-%d")
                        event_entry["end"] = fc_end.strftime("%Y-%m-%d")
                        event_entry["notes"] = f"Geöffnet von {start_date.strftime('%d.%m.')} bis {end_date.strftime('%d.%m.%Y')}."
                        print(f" -> Aktualisiert: {start_date.strftime('%d.%m.')} - {end_date.strftime('%d.%m.%Y')}")
                    else:
                        print(f" -> Kein Datumsblock erkannt, behalte bisherige Werte.")
            except Exception as e:
                print(f" -> Fehler beim Abruf: {e}")

        results.append(event_entry)

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Fertig! events.json aktualisiert.")

if __name__ == "__main__":
    scrape_all_besen()import json
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# -------------------------------------------------------------
# Stammdaten aller Besenwirtschaften im 15-km-Umkreis um Öhringen
# -------------------------------------------------------------
BESEN_LISTE = [
    {
        "id": "borth",
        "title": "Weingut & Weinstube Borth",
        "ort": "Bretzfeld-Adolzfurt (ca. 7 km)",
        "location": "Unterheimbacher Straße 35, 74626 Bretzfeld-Adolzfurt",
        "hours": "Täglich ab 11:00 Uhr | Küche Do-Sa bis ca. 21:00 Uhr, So bis ca. 19:30 Uhr",
        "color": "#831843",
        "url": "https://www.weingut-borth.de/pages/offnungszeiten-aktuelle-speisen"
    },
    {
        "id": "schluchter",
        "title": "Schluchter's Weinstube",
        "ort": "Pfedelbach-Baierbach (ca. 7 km)",
        "location": "Ruländerweg 3, 74629 Pfedelbach-Baierbach",
        "hours": "Mo bis Sa ab 11:30 Uhr | So ab 11:00 Uhr (an Besentagen)",
        "color": "#15803d",
        "url": "https://www.schluchters-weinstube.de"
    },
    {
        "id": "ungerer",
        "title": "Weingut & Weinstube Ungerer",
        "ort": "Pfedelbach-Renzen (ca. 8 km)",
        "location": "Harsberger Straße 15, 74629 Pfedelbach-Renzen",
        "hours": "Di bis So täglich ab 11:00 Uhr (Montag Ruhetag)",
        "color": "#b45309",
        "url": "https://www.weingut-ungerer.de"
    },
    {
        "id": "schnapsdrossel",
        "title": "Besenwirtschaft Die Schnapsdrossel",
        "ort": "Pfedelbach (ca. 4 km)",
        "location": "Pfedelbacher Str. 15, 74629 Pfedelbach",
        "hours": "Do & Fr ab 16:30 Uhr | Sa & So ab 11:30 Uhr",
        "color": "#0369a1",
        "url": "https://www.dieschnapsdrossel.de"
    },
    {
        "id": "schwab",
        "title": "Weingut & Weinstube Schwab",
        "ort": "Bretzfeld-Dimbach (ca. 7 km)",
        "location": "Wassergasse 2-4, 74626 Bretzfeld-Dimbach",
        "hours": "Do bis Mo ab 11:30 Uhr durchgehend",
        "color": "#7c2d12",
        "url": "https://www.weingut-schwab.de"
    },
    {
        "id": "birkert",
        "title": "Besenwirtschaft Birkert",
        "ort": "Bretzfeld-Adolzfurt (ca. 7 km)",
        "location": "Unterheimbacher Str. 28, 74626 Bretzfeld-Adolzfurt",
        "hours": "Täglich ab 11:30 Uhr",
        "color": "#4c1d95",
        "url": "https://www.weingut-birkert.de"
    },
    {
        "id": "busch",
        "title": "Weinstube Busch",
        "ort": "Bretzfeld-Dimbach (ca. 8 km)",
        "location": "Greuthof 1, 74626 Bretzfeld-Dimbach",
        "hours": "Fr & Sa ab 14:00 Uhr | So & Feiertag ab 11:30 Uhr",
        "color": "#065f46",
        "url": "https://www.weinstube-busch.de"
    },
    {
        "id": "weihbrecht",
        "title": "Weinstube Weihbrecht",
        "ort": "Bretzfeld-Schwabbach (ca. 6 km)",
        "location": "Hauptstraße 20, 74626 Bretzfeld-Schwabbach",
        "hours": "Do bis So ab 11:30 Uhr",
        "color": "#c2410c",
        "url": "https://www.weingut-weihbrecht.de"
    },
    {
        "id": "banzhaf",
        "title": "Weinausschank Banzhaf",
        "ort": "Bretzfeld-Siebeneich (ca. 6 km)",
        "location": "Wengertstraße 16, 74626 Bretzfeld-Siebeneich",
        "hours": "Fr ab 16:00 Uhr | Sa & So ab 11:30 Uhr",
        "color": "#9d174d",
        "url": "https://www.weingut-banzhaf.de"
    },
    {
        "id": "baldele",
        "title": "Baldele's Weinstube",
        "ort": "Öhringen-Cappel (ca. 2 km)",
        "location": "Obersteinbacher Straße 23, 74613 Öhringen-Cappel",
        "hours": "Fr & Sa ab 16:00 Uhr | So ab 11:30 Uhr | Mo ab 16:00 Uhr",
        "color": "#991b1b",
        "url": None
    },
    {
        "id": "laicher",
        "title": "Besenwirtschaft Laicher",
        "ort": "Obersulm-Willsbach (ca. 14 km)",
        "location": "Heerweg 21, 74182 Obersulm",
        "hours": "Täglich ab 11:30 Uhr geöffnet",
        "color": "#1e3a8a",
        "url": "https://www.weingut-laicher.de"
    }
]

def parse_dates_from_text(text):
    monate = {
        "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4,
        "mai": 5, "juni": 6, "juli": 7, "august": 8, "september": 9,
        "oktober": 10, "november": 11, "dezember": 12
    }

    # Format 1: 24.09. - 27.09.2026 oder 24.09. bis 27.09.2026
    m1 = re.search(r'(\d{1,2})\.(\d{1,2})\.?\s*(?:bis|-)\s*(\d{1,2})\.(\d{1,2})\.(\d{4})', text, re.IGNORECASE)
    if m1:
        s_day, s_mon, e_day, e_mon, year = [int(x) for x in m1.groups()]
        try:
            return datetime(year, s_mon, s_day), datetime(year, e_mon, e_day)
        except ValueError:
            pass

    # Format 2: 24. bis 27. September 2026
    m2 = re.search(r'(\d{1,2})\.?\s*(?:bis|-)\s*(\d{1,2})\.\s*([a-zäöü]+)\s*(\d{4})', text, re.IGNORECASE)
    if m2:
        s_day, e_day, mon_str, year = m2.groups()
        mon_str = mon_str.lower()
        if mon_str in monate:
            try:
                mon_idx = monate[mon_str]
                return datetime(int(year), mon_idx, int(s_day)), datetime(int(year), mon_idx, int(e_day))
            except ValueError:
                pass

    return None, None

def scrape_all_besen():
    current_events = {}
    try:
        with open("events.json", "r", encoding="utf-8") as f:
            raw = json.load(f)
            # Unterstützt altes Listenformat sowie neues Objektformat
            event_items = raw.get("events", []) if isinstance(raw, dict) else raw
            for item in event_items:
                current_events[item["id"]] = item
    except Exception:
        pass

    results = []

    for b in BESEN_LISTE:
        bid = b["id"]
        event_entry = current_events.get(bid, {
            "id": bid,
            "title": b["title"],
            "ort": b["ort"],
            "location": b["location"],
            "hours": b["hours"],
            "color": b["color"],
            "start": "2026-10-01",
            "end": "2026-10-06",
            "notes": "Öffnungszeiten laut Homepage / Aushang."
        })

        event_entry["title"] = b["title"]
        event_entry["ort"] = b["ort"]
        event_entry["location"] = b["location"]
        event_entry["hours"] = b["hours"]
        event_entry["color"] = b["color"]

        if b["url"]:
            print(f"Prüfe {b['title']}...")
            try:
                resp = requests.get(b["url"], headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    text = soup.get_text()
                    start_date, end_date = parse_dates_from_text(text)

                    if start_date and end_date:
                        fc_end = end_date + timedelta(days=1)
                        event_entry["start"] = start_date.strftime("%Y-%m-%d")
                        event_entry["end"] = fc_end.strftime("%Y-%m-%d")
                        event_entry["notes"] = f"Geöffnet von {start_date.strftime('%d.%m.')} bis {end_date.strftime('%d.%m.%Y')}."
                        print(f" -> Gefunden: {start_date.strftime('%d.%m.')} - {end_date.strftime('%d.%m.%Y')}")
                    else:
                        print(f" -> Kein neues Datumsmuster erkannt, Daten beibehalten.")
            except Exception as e:
                print(f" -> Fehler beim Abruf von {b['url']}: {e}")

        results.append(event_entry)

    # Jetzt mit "last_updated"-Zeitstempel abspeichern
    now_str = datetime.now().strftime("%d.%m.%Y um %H:%M Uhr")
    output_data = {
        "last_updated": now_str,
        "events": results
    }

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"Fertig! events.json aktualisiert am {now_str}.")

if __name__ == "__main__":
    scrape_all_besen()import json
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# -------------------------------------------------------------
# Stammdaten aller Besenwirtschaften im 15-km-Umkreis um Öhringen
# -------------------------------------------------------------
BESEN_LISTE = [
    {
        "id": "borth",
        "title": "Weingut & Weinstube Borth",
        "ort": "Bretzfeld-Adolzfurt (ca. 7 km)",
        "location": "Unterheimbacher Straße 35, 74626 Bretzfeld-Adolzfurt",
        "hours": "Täglich ab 11:00 Uhr | Küche Do-Sa bis ca. 21:00 Uhr, So bis ca. 19:30 Uhr",
        "color": "#831843",
        "url": "https://www.weingut-borth.de/pages/offnungszeiten-aktuelle-speisen"
    },
    {
        "id": "schluchter",
        "title": "Schluchter's Weinstube",
        "ort": "Pfedelbach-Baierbach (ca. 7 km)",
        "location": "Ruländerweg 3, 74629 Pfedelbach-Baierbach",
        "hours": "Mo bis Sa ab 11:30 Uhr | So ab 11:00 Uhr (an Besentagen)",
        "color": "#15803d",
        "url": "https://www.schluchters-weinstube.de"
    },
    {
        "id": "ungerer",
        "title": "Weingut & Weinstube Ungerer",
        "ort": "Pfedelbach-Renzen (ca. 8 km)",
        "location": "Harsberger Straße 15, 74629 Pfedelbach-Renzen",
        "hours": "Di bis So täglich ab 11:00 Uhr (Montag Ruhetag)",
        "color": "#b45309",
        "url": "https://www.weingut-ungerer.de"
    },
    {
        "id": "schnapsdrossel",
        "title": "Besenwirtschaft Die Schnapsdrossel",
        "ort": "Pfedelbach (ca. 4 km)",
        "location": "Pfedelbacher Str. 15, 74629 Pfedelbach",
        "hours": "Do & Fr ab 16:30 Uhr | Sa & So ab 11:30 Uhr",
        "color": "#0369a1",
        "url": "https://www.dieschnapsdrossel.de"
    },
    {
        "id": "schwab",
        "title": "Weingut & Weinstube Schwab",
        "ort": "Bretzfeld-Dimbach (ca. 7 km)",
        "location": "Wassergasse 2-4, 74626 Bretzfeld-Dimbach",
        "hours": "Do bis Mo ab 11:30 Uhr durchgehend",
        "color": "#7c2d12",
        "url": "https://www.weingut-schwab.de"
    },
    {
        "id": "birkert",
        "title": "Besenwirtschaft Birkert",
        "ort": "Bretzfeld-Adolzfurt (ca. 7 km)",
        "location": "Unterheimbacher Str. 28, 74626 Bretzfeld-Adolzfurt",
        "hours": "Täglich ab 11:30 Uhr",
        "color": "#4c1d95",
        "url": "https://www.weingut-birkert.de"
    },
    {
        "id": "busch",
        "title": "Weinstube Busch",
        "ort": "Bretzfeld-Dimbach (ca. 8 km)",
        "location": "Greuthof 1, 74626 Bretzfeld-Dimbach",
        "hours": "Fr & Sa ab 14:00 Uhr | So & Feiertag ab 11:30 Uhr",
        "color": "#065f46",
        "url": "https://www.weinstube-busch.de"
    },
    {
        "id": "weihbrecht",
        "title": "Weinstube Weihbrecht",
        "ort": "Bretzfeld-Schwabbach (ca. 6 km)",
        "location": "Hauptstraße 20, 74626 Bretzfeld-Schwabbach",
        "hours": "Do bis So ab 11:30 Uhr",
        "color": "#c2410c",
        "url": "https://www.weingut-weihbrecht.de"
    },
    {
        "id": "banzhaf",
        "title": "Weinausschank Banzhaf",
        "ort": "Bretzfeld-Siebeneich (ca. 6 km)",
        "location": "Wengertstraße 16, 74626 Bretzfeld-Siebeneich",
        "hours": "Fr ab 16:00 Uhr | Sa & So ab 11:30 Uhr",
        "color": "#9d174d",
        "url": "https://www.weingut-banzhaf.de"
    },
    {
        "id": "baldele",
        "title": "Baldele's Weinstube",
        "ort": "Öhringen-Cappel (ca. 2 km)",
        "location": "Obersteinbacher Straße 23, 74613 Öhringen-Cappel",
        "hours": "Fr & Sa ab 16:00 Uhr | So ab 11:30 Uhr | Mo ab 16:00 Uhr",
        "color": "#991b1b",
        "url": None
    },
    {
        "id": "laicher",
        "title": "Besenwirtschaft Laicher",
        "ort": "Obersulm-Willsbach (ca. 14 km)",
        "location": "Heerweg 21, 74182 Obersulm",
        "hours": "Täglich ab 11:30 Uhr geöffnet",
        "color": "#1e3a8a",
        "url": "https://www.weingut-laicher.de"
    }
]

def parse_dates_from_text(text):
    monate = {
        "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4,
        "mai": 5, "juni": 6, "juli": 7, "august": 8, "september": 9,
        "oktober": 10, "november": 11, "dezember": 12
    }

    # Format 1: 24.09. - 27.09.2026 oder 24.09. bis 27.09.2026
    m1 = re.search(r'(\d{1,2})\.(\d{1,2})\.?\s*(?:bis|-)\s*(\d{1,2})\.(\d{1,2})\.(\d{4})', text, re.IGNORECASE)
    if m1:
        s_day, s_mon, e_day, e_mon, year = [int(x) for x in m1.groups()]
        try:
            return datetime(year, s_mon, s_day), datetime(year, e_mon, e_day)
        except ValueError:
            pass

    # Format 2: 24. bis 27. September 2026
    m2 = re.search(r'(\d{1,2})\.?\s*(?:bis|-)\s*(\d{1,2})\.\s*([a-zäöü]+)\s*(\d{4})', text, re.IGNORECASE)
    if m2:
        s_day, e_day, mon_str, year = m2.groups()
        mon_str = mon_str.lower()
        if mon_str in monate:
            try:
                mon_idx = monate[mon_str]
                return datetime(int(year), mon_idx, int(s_day)), datetime(int(year), mon_idx, int(e_day))
            except ValueError:
                pass

    return None, None

def scrape_all_besen():
    current_events = {}
    try:
        with open("events.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                current_events[item["id"]] = item
    except Exception:
        pass

    results = []

    for b in BESEN_LISTE:
        bid = b["id"]
        event_entry = current_events.get(bid, {
            "id": bid,
            "title": b["title"],
            "ort": b["ort"],
            "location": b["location"],
            "hours": b["hours"],
            "color": b["color"],
            "start": "2026-10-01",
            "end": "2026-10-06",
            "notes": "Öffnungszeiten laut Aushang / Homepage."
        })

        # Felder sicherstellen
        event_entry["title"] = b["title"]
        event_entry["ort"] = b["ort"]
        event_entry["location"] = b["location"]
        event_entry["hours"] = b["hours"]
        event_entry["color"] = b["color"]

        if b["url"]:
            print(f"Prüfe {b['title']}...")
            try:
                resp = requests.get(b["url"], headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    text = soup.get_text()
                    start_date, end_date = parse_dates_from_text(text)

                    if start_date and end_date:
                        fc_end = end_date + timedelta(days=1)
                        event_entry["start"] = start_date.strftime("%Y-%m-%d")
                        event_entry["end"] = fc_end.strftime("%Y-%m-%d")
                        event_entry["notes"] = f"Geöffnet von {start_date.strftime('%d.%m.')} bis {end_date.strftime('%d.%m.%Y')}."
                        print(f" -> Aktualisiert: {start_date.strftime('%d.%m.')} - {end_date.strftime('%d.%m.%Y')}")
                    else:
                        print(f" -> Kein Datumsblock erkannt, behalte bisherige Werte.")
            except Exception as e:
                print(f" -> Fehler beim Abruf: {e}")

        results.append(event_entry)

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Fertig! events.json aktualisiert.")

if __name__ == "__main__":
    scrape_all_besen()
