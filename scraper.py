import json
import re
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

def scrape_borth():
    url = "https://www.weingut-borth.de/pages/offnungszeiten-aktuelle-speisen"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()

        # Sucht nach Datumsangaben wie "24.09. bis 27.09.2026"
        m = re.search(r'(\d{1,2}\.\d{1,2}\.)\s*(?:bis|-)\s*(\d{1,2}\.\d{1,2}\.\d{4})', text)
        if m:
            start_raw, end_raw = m.groups()
            end_date = datetime.strptime(end_raw.strip(), "%d.%m.%Y")
            s_day, s_month = [int(x) for x in start_raw.strip('.').split('.')]
            start_date = datetime(end_date.year, s_month, s_day)
            fc_end = end_date + timedelta(days=1)

            # JSON-Datei einlesen & aktualisieren
            with open("events.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            for ev in data:
                if ev.get("id") == "borth":
                    ev["start"] = start_date.strftime("%Y-%m-%d")
                    ev["end"] = fc_end.strftime("%Y-%m-%d")
                    ev["notes"] = f"Öffnungszeiten: {start_date.strftime('%d.%m.')} bis {end_date.strftime('%d.%m.%Y')}. Eigene Weine & Besengerichte. Keine Reservierung."
                    print("Borth erfolgreich aktualisiert!")
                    break

            with open("events.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    scrape_borth()
