import requests
import json
import math
import re
import html as html_lib
from datetime import datetime, timezone, timedelta

# Standard-Zentrum: Pfedelbach (als Basis für die Vorauswahl; im Frontend ist der Standort frei wählbar)
CENTER_LAT = 49.1764
CENTER_LON = 9.5056
MAX_DISTANCE_KM = 80.0

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def parse_dt_obj(val, default_offset=60, is_end=False):
    """Liest {'timestamp': 1675868400, 'offsetMinutes': 60} oder Zahl/ISO-String und gibt 'YYYY-MM-DD' zurück."""
    if val is None:
        return ""

    offset_min = default_offset
    if isinstance(val, dict):
        if val.get("offsetMinutes") is not None:
            offset_min = val.get("offsetMinutes")
        elif val.get("tzOffset") is not None:
            offset_min = val.get("tzOffset")
        raw_ts = val.get("timestamp") or val.get("date") or val.get("time") or val.get("value")
    else:
        raw_ts = val

    if raw_ts is None:
        return ""

    try:
        offset_min = float(offset_min)
    except Exception:
        offset_min = 60.0

    if isinstance(raw_ts, str):
        s = raw_ts.strip()
        m_iso = re.search(r'(\d{4}-\d{2}-\d{2})', s)
        if m_iso:
            return m_iso.group(1)
        m_de = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', s)
        if m_de:
            return f"{m_de.group(3)}-{m_de.group(2)}-{m_de.group(1)}"

    try:
        ts = float(raw_ts)
        if ts > 10000000000:
            ts = ts / 1000.0
        if 1577836800 <= ts <= 2051222400:
            dt = datetime.fromtimestamp(ts, tz=timezone.utc) + timedelta(minutes=offset_min)
            # Wenn ein Endzeitpunkt exakt auf 00:00 Uhr (Mitternacht des Folgetags) fällt,
            # zählt der Besentag zum Vortag (z.B. geöffnet bis 24:00 Uhr)
            if is_end and dt.hour == 0 and dt.minute == 0:
                dt = dt - timedelta(minutes=1)
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return ""

def extract_window_item(html_text):
    decoder = json.JSONDecoder()
    for m in re.finditer(r'window\.ITEM\s*=\s*\{', html_text):
        brace_pos = html_text.find('{', m.start())
        try:
            obj, _ = decoder.raw_decode(html_text[brace_pos:])
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    return None

def find_all_intervals(obj):
    results = []
    if isinstance(obj, dict):
        if "timeIntervals" in obj and isinstance(obj["timeIntervals"], list):
            results.extend(obj["timeIntervals"])
        for v in obj.values():
            results.extend(find_all_intervals(v))
    elif isinstance(obj, list):
        for elem in obj:
            results.extend(find_all_intervals(elem))
    return results

def find_coords(obj, html_text):
    if isinstance(obj, dict):
        stack = [obj]
        while stack:
            curr = stack.pop()
            if isinstance(curr, dict):
                lat = curr.get("latitude") or curr.get("lat")
                lon = curr.get("longitude") or curr.get("lon") or curr.get("lng")
                if lat is not None and lon is not None:
                    try:
                        lat_f, lon_f = float(lat), float(lon)
                        if 47.0 <= lat_f <= 51.0 and 7.0 <= lon_f <= 12.0:
                            return lat_f, lon_f
                    except Exception:
                        pass
                for v in curr.values():
                    if isinstance(v, (dict, list)):
                        stack.append(v)
            elif isinstance(curr, list):
                for v in curr:
                    if isinstance(v, (dict, list)):
                        stack.append(v)

    m_lat = re.search(r'"latitude"\s*:\s*(4[89]\.\d+)', html_text)
    m_lon = re.search(r'"longitude"\s*:\s*([89]\.\d+|10\.\d+)', html_text)
    if m_lat and m_lon:
        return float(m_lat.group(1)), float(m_lon.group(1))
    return None

def extract_contact_info(html_text):
    """Extrahiert Straße, PLZ, Ort, Telefon und Webseite direkt aus dem Schema.org JSON-LD / HTML der Detailseite."""
    street, zip_code, city, phone, website = "", "", "", "", ""
    if not html_text:
        return street, zip_code, city, phone, website

    # 1. Aus eingebettetem Schema.org PostalAddress JSON-LD lesen:
    # "address":{"@type":"PostalAddress","addressLocality":"Bretzfeld","postalCode":"74626","streetAddress":"Unterheimbacherstraße 35"...}
    m_street = re.search(r'"streetAddress"\s*:\s*"([^"]+)"', html_text)
    if m_street:
        street = html_lib.unescape(m_street.group(1)).strip()

    m_zip = re.search(r'"postalCode"\s*:\s*"([^"]+)"', html_text)
    if m_zip:
        zip_code = html_lib.unescape(m_zip.group(1)).strip()

    m_city = re.search(r'"addressLocality"\s*:\s*"([^"]+)"', html_text)
    if m_city:
        city = html_lib.unescape(m_city.group(1)).strip()

    # 2. Fallback über Deutsche-Bahn-Routing-Link oder JS-Variablen im Quelltext
    if not (street and zip_code and city):
        m_db = re.search(r'bahn\.de/buchung/start#zo=(\d{5})\s+([^\'"<>]+)', html_text)
        if m_db:
            if not zip_code:
                zip_code = m_db.group(1).strip()
            rest = html_lib.unescape(m_db.group(2)).strip()
            if not city and not street:
                parts = rest.split(" ", 1)
                city = parts[0]
                if len(parts) > 1:
                    street = parts[1]

    # 3. Telefonnummer (aus JSON-LD "telephone" oder tel:-Link)
    m_tel = re.search(r'"telephone"\s*:\s*"([^"]+)"', html_text)
    if m_tel:
        phone = html_lib.unescape(m_tel.group(1)).strip()
    else:
        m_tel2 = re.search(r'href=["\']tel:([^"\']+)["\']', html_text, re.IGNORECASE)
        if m_tel2:
            phone = html_lib.unescape(m_tel2.group(1)).strip()

    # 4. Externe Webseite des Besens (nur echte <a href="..."> Links, keine Icons/Assets!)
    ignore_domains = (
        "besenstimme.de", "heilbronnerland.de", "bahn.de", "bwegt.de",
        "google.", "facebook.", "instagram.", "toubiz.", "openstreetmap.",
        "w3.org", "schema.org", "cloudflare", "jquery", "bootstrap", "font",
        "destination.one", "et4.de", "stimme.de"
    )
    bad_ext = (
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
        ".css", ".js", ".woff", ".woff2", ".ttf", ".xml", ".json", ".webmanifest"
    )

    for m_web in re.finditer(r'<a\b[^>]*?\bhref=["\'](https?://[^"\'\s<>]+)["\']', html_text, re.IGNORECASE):
        u = html_lib.unescape(m_web.group(1)).strip()
        u_low = u.lower().split("?")[0].split("#")[0]
        if u_low.endswith(bad_ext):
            continue
        if not any(ig in u_low for ig in ignore_domains):
            website = u
            break

    return street, zip_code, city, phone, website

def main():
    base_url = "https://www.besenstimme.de"
    portal_url = f"{base_url}/de/besenstimme/wlan/portal"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9"
    }

    session = requests.Session()
    session.headers.update(headers)

    print("1. Lade Portal-Übersicht von besenstimme.de...")
    r = session.get(portal_url, timeout=20)
    r.raise_for_status()

    matches = re.findall(r'(/(?:de|cs)/besenstimme/wlan/detail/Gastro/(g_\d+)[^"\'\s<>]*)', r.text)
    seen_ids = set()
    besen_list = []
    for path, gid in matches:
        if gid not in seen_ids:
            seen_ids.add(gid)
            clean_path = re.sub(r'^/cs/', '/de/', path)
            besen_list.append((gid, f"{base_url}{clean_path}"))

    print(f"2. {len(besen_list)} Besenwirtschaften im Portal gefunden.")
    print(f"3. Prüfe Entfernungen und lade Termine (Radius: {MAX_DISTANCE_KM} km ab Pfedelbach)...")

    places = []
    events = []

    for gid, detail_url in besen_list:
        try:
            res = session.get(detail_url, timeout=15)
            if res.status_code != 200:
                continue

            html = res.text
            item_obj = extract_window_item(html)
            coords = find_coords(item_obj, html)
            if not coords:
                continue

            lat, lon = coords
            dist = haversine(CENTER_LAT, CENTER_LON, lat, lon)
            if dist > MAX_DISTANCE_KM:
                continue

            name = None
            if isinstance(item_obj, dict):
                name = item_obj.get("title") or item_obj.get("name") or item_obj.get("value")
            if not name:
                m_h1 = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE)
                if m_h1:
                    name = re.sub(r'<[^>]+>', '', m_h1.group(1)).strip()
            if not name:
                name = detail_url.split("/")[-1].replace("-", " ").title()

            street, zip_code, city, phone, website = extract_contact_info(html)
            address_parts = [p for p in [street, f"{zip_code} {city}".strip()] if p]
            address_str = ", ".join(address_parts)

            places.append({
                "id": gid,
                "name": name,
                "lat": lat,
                "lon": lon,
                "distance_km": round(dist, 1),
                "address": address_str,
                "city": city,
                "phone": phone,
                "website": website,
                "url": detail_url
            })

            intervals = find_all_intervals(item_obj) if item_obj else []

            raw_ranges = []
            for inv in intervals:
                if not isinstance(inv, dict):
                    continue

                s_obj = inv.get("start") or inv.get("startDate") or inv.get("dateFrom")
                # WICHTIG: repeatUntil ist das Ende des Besen-Zeitraums, end nur das Ende des 1. Öffnungstags!
                e_obj = inv.get("repeatUntil") or inv.get("end") or inv.get("endDate") or inv.get("dateTo") or s_obj

                s_str = parse_dt_obj(s_obj, is_end=False)
                e_str = parse_dt_obj(e_obj, is_end=True)

                # Falls repeatUntil vor start liegen sollte, Fallback auf end
                if s_str and (not e_str or e_str < s_str):
                    e_str = parse_dt_obj(inv.get("end"), is_end=True) or s_str

                if s_str and e_str:
                    raw_ranges.append((s_str, e_str))

            # Zusätzlich im sichtbaren HTML nach "dd.mm.yyyy bis dd.mm.yyyy" suchen
            for m_txt in re.finditer(r'(\d{2})\.(\d{2})\.(\d{4})\s*(?:bis|-|–)\s*(\d{2})\.(\d{2})\.(\d{4})', html):
                d1, m1, y1, d2, m2, y2 = m_txt.groups()
                s_txt = f"{y1}-{m1}-{d1}"
                e_txt = f"{y2}-{m2}-{d2}"
                if "2025" <= y2 <= "2030":
                    raw_ranges.append((s_txt, e_txt))

            # Überlappende oder direkt aneinandergrenzende Zeiträume desselben Besens zusammenfassen
            raw_ranges = sorted(set(raw_ranges))
            merged_ranges = []
            for s_str, e_str in raw_ranges:
                if merged_ranges:
                    prev_s, prev_e = merged_ranges[-1]
                    dt_prev_e = datetime.strptime(prev_e, "%Y-%m-%d")
                    dt_curr_s = datetime.strptime(s_str, "%Y-%m-%d")
                    if (dt_curr_s - dt_prev_e).days <= 1:
                        new_e = max(prev_e, e_str)
                        merged_ranges[-1] = (prev_s, new_e)
                        continue
                merged_ranges.append((s_str, e_str))

            found = 0
            for s_str, e_str in merged_ranges:
                events.append({
                    "place_id": gid,
                    "title": name,
                    "start": s_str,
                    "end": e_str,
                    "lat": lat,
                    "lon": lon,
                    "distance_km": round(dist, 1),
                    "address": address_str,
                    "city": city,
                    "phone": phone,
                    "website": website,
                    "url": detail_url
                })
                found += 1

            if found > 0:
                print(f"🎯 [{dist:4.1f} km] {name} -> {found} Termine | 📍 {address_str or 'k.A.'}")

        except Exception:
            continue

    events.sort(key=lambda x: (x["start"], x["distance_km"]))
    places.sort(key=lambda x: x["distance_km"])

    now_berlin = datetime.now(timezone(timedelta(hours=2)))
    data_out = {
        "updated_at": now_berlin.strftime("%d.%m.%Y, %H:%M Uhr"),
        "center": {"name": "Pfedelbach", "lat": CENTER_LAT, "lon": CENTER_LON},
        "places": places,
        "events": events
    }

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, indent=2)

    with_addr = sum(1 for p in places if p.get("address"))
    print("\n==========================================")
    print("ERFOLG!")
    print(f"- {len(places)} Besen im Umkreis von {MAX_DISTANCE_KM} km erfasst ({with_addr} mit Adresse)")
    print(f"- {len(events)} bereinigte Kalender-Einträge in 'events.json' gespeichert.")

if __name__ == "__main__":
    main()
