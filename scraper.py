import requests
import re
import json
import math
from datetime import datetime, timezone

# ==========================================
# KONFIGURATION: Zentrum Pfedelbach
# ==========================================
CENTER_LAT = 49.1756
CENTER_LON = 9.5050
MAX_RADIUS_KM = 35.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9"
}

def haversine(lat1, lon1, lat2, lon2):
    """Berechnet die Entfernung zweier Koordinaten in Kilometern."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)

def extract_contact_info(html):
    """Extrahiert Adresse, Telefon und die Homepage des Besens sauber aus dem Detail-HTML."""
    street, zip_code, city, phone, website = "", "", "", "", ""
    
    # 1. Adresse aus Schema.org PostalAddress
    m_addr = re.search(r'"@type"\s*:\s*"PostalAddress"(.*?)\}', html, re.DOTALL)
    if m_addr:
        block = m_addr.group(1)
        m_s = re.search(r'"streetAddress"\s*:\s*"([^"]+)"', block)
        m_z = re.search(r'"postalCode"\s*:\s*"([^"]+)"', block)
        m_c = re.search(r'"addressLocality"\s*:\s*"([^"]+)"', block)
        if m_s: street = m_s.group(1).encode('utf-8').decode('unicode_escape', 'ignore').strip()
        if m_z: zip_code = m_z.group(1).strip()
        if m_c: city = m_c.group(1).encode('utf-8').decode('unicode_escape', 'ignore').strip()

    # Fallback Adresse falls nicht in schema.org
    if not zip_code or not city:
        m_plz = re.search(r'\b(7\d{4})\s+([A-Za-zäöüÄÖÜß\-\s]{3,30})', html)
        if m_plz:
            if not zip_code: zip_code = m_plz.group(1).strip()
            if not city: city = m_plz.group(2).split('\n')[0].strip()

    # 2. Telefonnummer
    m_tel = re.search(r'href=[\'"]tel:([^\'"]+)[\'"]', html)
    if m_tel:
        phone = m_tel.group(1).strip()

    # 3. Externe Homepage des Betriebs finden
    ignore_domains = (
        'besenstimme.de', 'bahn.de', 'google.', 'et4.de', 'apple.com', 
        'destination.one', 'vrs.de', 'facebook.com', 'instagram.com', 
        'schema.org', 'w3.org'
    )
    
    # Alle <a>-Tags nach externen Links durchsuchen (keine Grafiken, Styles, Icons)
    matches = re.findall(r'<a[^>]+href=[\'"](https?://[^\'"]+)[\'"][^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
    for href, text in matches:
        clean_href = href.strip()
        
        # Ignoriere Bilder, Icons und Mediendateien (verhindert favicon-shortcut.png)
        if clean_href.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif', '.ico', '.css', '.js', '.pdf')):
            continue
            
        # Ignoriere Portal-eigene und Werbelinks
        if any(bad in clean_href.lower() for bad in ignore_domains):
            continue
            
        # Wenn Linktext typische Schlüsselwörter hat oder eine Domain abbildet
        clean_text_lower = text.lower()
        if re.search(r'webseite|homepage|website|internet|besuchen|unsere seite', clean_text_lower) or 'www.' in clean_text_lower:
            website = clean_href
            break
        elif not website and ('www.' in clean_href or clean_href.startswith('http')):
            website = clean_href

    return street, zip_code, city, phone, website

def run():
    print("1. Lade Portal-Übersicht von besenstimme.de...")
    list_url = "https://www.besenstimme.de/de/besenstimme/wlan/list/Gastro"
    try:
        resp = requests.get(list_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"FEHLER beim Laden der Hauptseite: {e}")
        return

    # Suche nach dem eingebetteten JSON-Array der Betriebe
    match = re.search(r'window\.ITEMS\s*=\s*(\[\{.*?\}\]);', resp.text, re.DOTALL)
    if not match:
        match = re.search(r'var\s+items\s*=\s*(\[\{.*?\}\]);', resp.text, re.DOTALL)
    
    if not match:
        print("FEHLER: Konnte Betriebe-Array auf besenstimme.de nicht finden.")
        return

    try:
        all_venues = json.loads(match.group(1))
    except Exception as e:
        print(f"FEHLER beim JSON-Parsen: {e}")
        return

    print(f"2. {len(all_venues)} Betriebe im Portal gefunden.")
    print(f"3. Filtere nach Umkreis (<= {MAX_RADIUS_KM} km ab Pfedelbach) und hole Detail-Infos...")

    events_list = []
    venues_count = 0

    session = requests.Session()
    session.headers.update(HEADERS)

    for item in all_venues:
        # Geokoordinaten ermitteln
        lat = None
        lon = None
        geo = item.get("geo") or item.get("location") or {}
        if isinstance(geo, dict):
            lat = geo.get("lat") or geo.get("latitude")
            lon = geo.get("lon") or geo.get("lng") or geo.get("longitude")
        
        if not lat or not lon:
            lat = item.get("lat") or item.get("latitude")
            lon = item.get("lon") or item.get("lng") or item.get("longitude")

        if not lat or not lon:
            continue

        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            continue

        distance_km = haversine(CENTER_LAT, CENTER_LON, lat, lon)
        if distance_km > MAX_RADIUS_KM:
            continue

        venues_count += 1
        name = item.get("title") or item.get("name") or "Besenwirtschaft"
        detail_path = item.get("url") or item.get("detailUrl") or ""
        
        detail_url = ""
        if detail_path:
            if detail_path.startswith("http"):
                detail_url = detail_path
            else:
                detail_url = "https://www.besenstimme.de" + detail_path

        street, zip_code, city, phone, website = "", "", "", "", ""
        detail_html = ""

        # Detailseite abrufen für Adresse & Homepage & Termine
        if detail_url:
            try:
                res_d = session.get(detail_url, timeout=12)
                if res_d.status_code == 200:
                    detail_html = res_d.text
                    street, zip_code, city, phone, website = extract_contact_info(detail_html)
            except Exception:
                pass

        # Termine extrahieren (entweder aus dem Item selbst oder aus dem Detail-HTML)
        dates_raw = item.get("dates") or item.get("openingHours") or item.get("events") or []
        
        # Falls Termine als Liste vorhanden sind
        if isinstance(dates_raw, list):
            for d in dates_raw:
                if isinstance(d, dict):
                    start = d.get("from") or d.get("start") or d.get("startDate")
                    end = d.get("to") or d.get("end") or d.get("endDate") or start
                    note = d.get("note") or d.get("info") or ""
                    if start:
                        events_list.append({
                            "name": name,
                            "street": street,
                            "zip": zip_code,
                            "city": city,
                            "phone": phone,
                            "website": website,
                            "distance_km": distance_km,
                            "start": str(start)[:10],
                            "end": str(end)[:10],
                            "note": note
                        })

        # Fallback: Termine aus Schema.org oder Textblöcken im Detail-HTML
        if not any(e["name"] == name for e in events_list) and detail_html:
            event_matches = re.findall(r'(\d{2}\.\d{2}\.\d{4})\s*(?:bis|-)\s*(\d{2}\.\d{2}\.\d{4})', detail_html)
            for m_from, m_to in event_matches:
                try:
                    s_dt = datetime.strptime(m_from, "%d.%m.%Y").strftime("%Y-%m-%d")
                    e_dt = datetime.strptime(m_to, "%d.%m.%Y").strftime("%Y-%m-%d")
                    events_list.append({
                        "name": name,
                        "street": street,
                        "zip": zip_code,
                        "city": city,
                        "phone": phone,
                        "website": website,
                        "distance_km": distance_km,
                        "start": s_dt,
                        "end": e_dt,
                        "note": ""
                    })
                except Exception:
                    pass

    # Sortierung: zuerst nach Datum aufsteigend, dann nach Entfernung
    events_list.sort(key=lambda x: (x.get("start", ""), x.get("distance_km", 999)))

    # Metadaten hinzufügen & speichern
    now_str = datetime.now(timezone.utc).strftime("%d.%m.%Y, %H:%M Uhr UTC")
    output_data = {
        "updated_at": now_str,
        "events": events_list
    }

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("\n==========================================")
    print("ERFOLG!")
    print(f"- {venues_count} Besen im Umkreis von {MAX_RADIUS_KM} km gefunden.")
    print(f"- {len(events_list)} Termine in 'events.json' gespeichert.")
    print(f"- Stand: {now_str}")

if __name__ == "__main__":
    run()
