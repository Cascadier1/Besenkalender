import requests
import json
import math
import re
from datetime import datetime, timezone, timedelta

# Zentrum: Pfedelbach
CENTER_LAT = 49.1764
CENTER_LON = 9.5056
MAX_DISTANCE_KM = 35.0

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

def extract_contact_info(item_obj):
    """Extrahiert Adresse, Ort, Telefon und Webseite aus window.ITEM."""
    street, zip_code, city, phone, website = "", "", "", "", ""
    if not isinstance(item_obj, dict):
        return street, zip_code, city, phone, website

    stack = [item_obj]
    while stack:
        curr = stack.pop()
        if isinstance(curr, dict):
            if not street and isinstance(curr.get("street"), str):
                street = curr["street"].strip()
            if not zip_code and isinstance(curr.get("zip"), str):
                zip_code = curr["zip"].strip()
            elif not zip_code and isinstance(curr.get("postalCode"), str):
                zip_code = curr["postalCode"].strip()
            if not city and isinstance(curr.get("city"), str):
                city = curr["city"].strip()
            if not phone and isinstance(curr.get("phone"), str):
                phone = curr["phone"].strip()
            elif not phone and isinstance(curr.get("telephone"), str):
                phone = curr["telephone"].strip()
            if not website and isinstance(curr.get("url"), str) and curr["url"].startswith("http"):
                if "besenstimme.de" not in curr["url"]:
                    website = curr["url"].strip()
            elif not website and isinstance(curr.get("website"), str):
                website = curr["website"].strip()

            for v in curr.values():
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(curr, list):
            for v in curr:
                if isinstance(v, (dict, list)):
                    stack.append(v)

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

            street, zip_code, city, phone, website = extract_contact_info(item_obj)
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

            #Zusätzlich im sichtbaren HTML nach "dd.mm.yyyy bis dd.mm.yyyy" suchen (wie bei Banzhaf)
            for m_txt in re.finditer(r'(\d{2})\.(\d{2})\.(\d{4})\s*(?:bis|-|–)\s*(\d{2})\.(\d{2})\.(\d{4})', html):
                d1, m1, y1, d2, m2, y2 = m_txt.groups()
                s_txt = f"{y1}-{m1}-{d1}"
                e_txt = f"{y2}-{m2}-{d2}"
                if "2025" <= y2 <= "2030":
                    raw_ranges.append((s_txt, e_txt))

            # Überlappende oder direkt aneinandergrenzende Zeiträume desselben Besens zusammenfassen
            # (z.B. wenn ein Besen für Fr-So und Di-So desselben Besen-Zeitraums zwei Intervalle hat)
            raw_ranges = sorted(set(raw_ranges))
            merged_ranges = []
            for s_str, e_str in raw_ranges:
                if merged_ranges:
                    prev_s, prev_e = merged_ranges[-1]
                    # Wenn der neue Zeitraum sich mit dem vorherigen überschneidet oder <= 1 Tag Abstand hat
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
                    "distance_km": round(dist, 1),
                    "address": address_str,
                    "city": city,
                    "phone": phone,
                    "website": website,
                    "url": detail_url
                })
                found += 1

            if found > 0:
                loc_info = f" ({city})" if city else ""
                print(f"🎯 [{dist:4.1f} km] {name}{loc_info} -> {found} Termine")

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

    print("\n==========================================")
    print("ERFOLG!")
    print(f"- {len(places)} Besen im Umkreis von {MAX_DISTANCE_KM} km erfasst")
    print(f"- {len(events)} bereinigte Kalender-Einträge in 'events.json' gespeichert.")

if __name__ == "__main__":
    main()