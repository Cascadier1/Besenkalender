import requests
import json
import math
import re
import html as html_lib
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
        return ""

    try:
        ts = float(raw_ts)
        if ts > 1e11:
            ts /= 1000.0
        dt_utc = datetime.fromtimestamp(ts, tz=timezone.utc)
        dt_local = dt_utc + timedelta(minutes=offset_min)
        if is_end and dt_local.hour < 5:
            dt_local -= timedelta(days=1)
        return dt_local.strftime("%Y-%m-%d")
    except Exception:
        return ""

def extract_contact_info(html):
    street, zip_code, city, phone, website = "", "", "", "", ""
    
    # 1. Adresse aus PostalAddress JSON
    m_addr = re.search(r'"@type"\s*:\s*"PostalAddress"(.*?)\}', html, re.DOTALL)
    if m_addr:
        block = m_addr.group(1)
        m_s = re.search(r'"streetAddress"\s*:\s*"([^"]+)"', block)
        m_z = re.search(r'"postalCode"\s*:\s*"([^"]+)"', block)
        m_c = re.search(r'"addressLocality"\s*:\s*"([^"]+)"', block)
        if m_s: street = m_s.group(1).encode('utf-8').decode('unicode_escape', 'ignore').strip()
        if m_z: zip_code = m_z.group(1).strip()
        if m_c: city = m_c.group(1).encode('utf-8').decode('unicode_escape', 'ignore').strip()

    # 2. Telefonnummer aus tel:-Link
    m_tel = re.search(r'href=[\'"]tel:([^\'"]+)[\'"]', html)
    if m_tel:
        phone = m_tel.group(1).strip()

    # 3. Webseite: Link mit Text "Webseite" oder "www...."
    m_web = re.search(r'<a[^>]+href=[\'"](https?://[^\'"]+)[\'"][^>]*>\s*Webseite\s*</a>', html, re.I)
    if not m_web:
        m_web = re.search(r'<a[^>]+href=[\'"](https?://[^\'"]+)[\'"][^>]*>\s*(?:www\.[^<]+)\s*</a>', html, re.I)
    
    if m_web:
        found_url = m_web.group(1).strip()
        blacklist = ["besenstimme.de", "destination.one", "bahn.de", "google.", "instagram.com", "facebook.com", "ecmaps.de", "et4.de"]
        if not any(b in found_url for b in blacklist):
            website = found_url

    parts = []
    if street: parts.append(street)
    if zip_code or city: parts.append(f"{zip_code} {city}".strip())
    address_str = ", ".join(parts)

    return address_str, city, phone, website

def main():
    base_url = "https://www.besenstimme.de"
    portal_url = f"{base_url}/de/besenstimme/wlan/portal"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9"
    }

    session = requests.Session()
    session.headers.update(headers)

    print("1. Lade Portal-Übersicht von besenstimme.de...")
    r = session.get(portal_url, timeout=20)
    r.raise_for_status()

    # Portal-Links parsen
    detail_links = set(re.findall(r'href=[\'"](/de/besenstimme/wlan/detail/Gastro/[^\'"]+)[\'"]', r.text))
    print(f"2. {len(detail_links)} Besenwirtschaften im Portal gefunden.")
    print(f"3. Prüfe Entfernungen und lade Termine (Radius: {MAX_DISTANCE_KM} km ab Pfedelbach)...")

    events = []
    places = []

    for path in sorted(detail_links):
        detail_url = f"{base_url}{path}"
        try:
            resp = session.get(detail_url, timeout=10)
            if resp.status_code != 200:
                continue

            html_text = resp.text

            # window.ITEM extrahieren
            m_item = re.search(r'window\.ITEM\s*=\s*(\{.+?\});\s*(?:window\.|\n|<)', html_text, re.DOTALL)
            if not m_item:
                continue

            try:
                item_data = json.loads(m_item.group(1))
            except Exception:
                continue

            gid = item_data.get("global_id") or item_data.get("id") or path
            name = item_data.get("title") or "Unbenannter Besen"

            # Koordinaten & Distanz prüfen
            geo = item_data.get("geo") or {}
            main_geo = geo.get("main") or geo
            lat = main_geo.get("latitude")
            lon = main_geo.get("longitude")

            if not lat or not lon:
                continue

            dist = haversine(CENTER_LAT, CENTER_LON, float(lat), float(lon))
            if dist > MAX_DISTANCE_KM:
                continue

            # Kontaktdaten & Webseite extrahieren
            address_str, city, phone, website = extract_contact_info(html_text)

            places.append({
                "id": gid,
                "name": name,
                "lat": float(lat),
                "lon": float(lon),
                "distance_km": round(dist, 1),
                "address": address_str,
                "city": city,
                "phone": phone,
                "website": website,
                "url": detail_url
            })

            # Termine aus timeIntervals auswerten
            intervals = item_data.get("timeIntervals") or []
            raw_ranges = []

            for iv in intervals:
                s_obj = iv.get("start")
                e_obj = iv.get("repeatUntil") or iv.get("end") or s_obj
                s_txt = parse_dt_obj(s_obj, is_end=False)
                e_txt = parse_dt_obj(e_obj, is_end=True)

                if s_txt and e_txt and s_txt <= e_txt and e_txt >= "2024-01-01" and s_txt <= "2030-12-31":
                    raw_ranges.append((s_txt, e_txt))

            # Überlappende oder zusammenhängende Tage verschmelzen
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
                    "distance_km": round(dist, 1),
                    "address": address_str,
                    "city": city,
                    "phone": phone,
                    "website": website,
                    "url": detail_url
                })
                found += 1

            if found > 0:
                print(f"🎯 [{dist:4.1f} km] {name} -> {found} Termine | 📍 {address_str or 'k.A.'} | 🌐 {website or '-'}")

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
    with_web = sum(1 for p in places if p.get("website"))
    print("\n==========================================")
    print("ERFOLG!")
    print(f"- {len(places)} Besen im Umkreis von {MAX_DISTANCE_KM} km erfasst ({with_addr} mit Adresse, {with_web} mit Webseite)")
    print(f"- {len(events)} bereinigte Kalender-Einträge in 'events.json' gespeichert.")

if __name__ == "__main__":
    main()
