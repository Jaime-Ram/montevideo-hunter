#!/usr/bin/env python3
"""
Montevideo Website Hunter
Vindt bedrijven op Google Maps zonder eigen website — verkoopkansen voor webdesign.

Gebruik:
    export GOOGLE_PLACES_API_KEY="AIza..."
    python scraper.py
    python scraper.py --kaart-only   # alleen kaart opnieuw genereren uit checkpoint
"""

import argparse
import csv
import json
import os
import time
from pathlib import Path

try:
    import googlemaps
except ImportError:
    raise SystemExit("pip install googlemaps")

try:
    import folium
    from folium.plugins import MarkerCluster, Search
except ImportError:
    raise SystemExit("pip install folium")

# ── CONFIGURATIE ──────────────────────────────────────────────────────────────

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

# Montevideo dekking — pas aan om een specifieke wijk te targeten
# Standaard: Ciudad Vieja t/m Pocitos / Punta Carretas
GEBIEDEN = {
    "centro":         [(-34.912, -56.198), (-34.893, -56.175)],
    "cordon":         [(-34.910, -56.175), (-34.892, -56.155)],
    "palermo":        [(-34.905, -56.160), (-34.888, -56.140)],
    "parque_rodo":    [(-34.918, -56.168), (-34.903, -56.148)],
    "punta_carretas": [(-34.930, -56.155), (-34.908, -56.135)],
    "pocitos":        [(-34.920, -56.165), (-34.893, -56.140)],
}

ZOEK_RADIUS = 700        # meter per gridpunt (overlap is OK, duplicaten worden gefilterd)
LAT_STAP    = 0.008      # ≈ 900 m
LON_STAP    = 0.010      # ≈ 900 m

# Bedrijfstypes (lege lijst = álles, maar dat is duurder)
TYPES = [
    "restaurant", "cafe", "bakery", "bar", "lodging",
    "store", "clothing_store", "shoe_store", "hair_care",
    "beauty_salon", "spa", "gym",
    "electronics_store", "book_store", "florist",
    "car_repair", "laundry", "pharmacy",
    "supermarket", "convenience_store",
    "real_estate_agency", "travel_agency",
    "insurance_agency", "accounting",
    "dentist", "doctor", "veterinary_care",
]

DETAIL_VELDEN = [
    "name", "website", "formatted_address",
    "formatted_phone_number", "geometry/location",
    "business_status", "type", "url", "rating",
    "user_ratings_total",
]

CHECKPOINT = "checkpoint.json"
CSV_BESTAND = "prospects.csv"
KAART_BESTAND = "kaart_prospects.html"


# ── HULPFUNCTIES ──────────────────────────────────────────────────────────────

def maak_grid(gebieden: dict) -> list[tuple[float, float]]:
    punten: set[tuple[float, float]] = set()
    for naam, (sw, ne) in gebieden.items():
        lat = sw[0]
        while lat <= ne[0]:
            lon = sw[1]
            while lon <= ne[1]:
                punten.add((round(lat, 5), round(lon, 5)))
                lon += LON_STAP
            lat += LAT_STAP
    return sorted(punten)


def zoek_nearby(client, lat: float, lon: float, btype: str | None = None) -> set[str]:
    ids: set[str] = set()
    kwargs = dict(location=(lat, lon), radius=ZOEK_RADIUS, language="es")
    if btype:
        kwargs["type"] = btype

    try:
        result = client.places_nearby(**kwargs)
    except Exception as e:
        print(f"    ⚠ Search fout ({btype}): {e}")
        return ids

    while True:
        for p in result.get("results", []):
            ids.add(p["place_id"])
        token = result.get("next_page_token")
        if not token:
            break
        time.sleep(2.2)  # Google vereist pauze voor next_page_token
        try:
            result = client.places_nearby(page_token=token)
        except Exception:
            break

    return ids


def haal_details(client, place_id: str) -> dict:
    try:
        r = client.place(place_id, fields=DETAIL_VELDEN, language="es")
        return r.get("result", {})
    except Exception as e:
        print(f"    ⚠ Detail fout {place_id}: {e}")
        return {}


def laad_checkpoint() -> tuple[set[str], list[dict]]:
    p = Path(CHECKPOINT)
    if p.exists():
        data = json.loads(p.read_text())
        print(f"♻  Checkpoint gevonden: {len(data['done'])} verwerkt, {len(data['prospects'])} prospects")
        return set(data["done"]), data["prospects"]
    return set(), []


def sla_checkpoint(done: set[str], prospects: list[dict]):
    Path(CHECKPOINT).write_text(
        json.dumps({"done": list(done), "prospects": prospects}, ensure_ascii=False, indent=2)
    )


def sla_csv(prospects: list[dict]):
    if not prospects:
        return
    velden = ["name", "address", "phone", "rating", "reviews", "types", "web_type", "social_url", "lat", "lon", "maps_url", "place_id"]
    with open(CSV_BESTAND, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=velden, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(prospects)
    print(f"✅ CSV: {CSV_BESTAND} ({len(prospects)} bedrijven)")


def maak_kaart(prospects: list[dict]):
    if not prospects:
        print("Geen prospects voor kaart.")
        return

    geen  = sum(1 for p in prospects if p.get("web_type") == "geen")
    insta = sum(1 for p in prospects if p.get("web_type") == "instagram")
    fb    = sum(1 for p in prospects if p.get("web_type") == "facebook")

    # Compacte dataset — alleen wat de kaart nodig heeft
    data = [
        {
            "n": p.get("name", ""),
            "a": p.get("address", "")[:60],
            "p": p.get("phone", "") or "",
            "t": p.get("web_type", "geen"),
            "s": p.get("social_url", "") or "",
            "m": p.get("maps_url", "") or "",
            "lt": p.get("lat"),
            "ln": p.get("lon"),
        }
        for p in prospects if p.get("lat") and p.get("lon")
    ]

    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Montevideo Prospects ({len(data)})</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  #map {{ height: 100vh; width: 100%; }}
  #legend {{
    position: fixed; bottom: 20px; left: 20px;
    background: white; padding: 14px; border-radius: 10px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.25);
    font-family: sans-serif; font-size: 13px; z-index: 1000;
    line-height: 1.8;
  }}
  .dot {{ font-size: 18px; vertical-align: middle; }}
</style>
</head>
<body>
<div id="map"></div>
<div id="legend">
  <b>Montevideo — {len(data)} prospects</b><br>
  <span class="dot" style="color:#EF4444">●</span> Geen website ({geen})<br>
  <span class="dot" style="color:#8B5CF6">●</span> Alleen Instagram ({insta})<br>
  <span class="dot" style="color:#1877F2">●</span> Alleen Facebook ({fb})
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
var map = L.map('map').setView([-34.906, -56.171], 14);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '&copy; OpenStreetMap contributors',
  maxZoom: 19
}}).addTo(map);

var COLORS = {{geen:'#EF4444', instagram:'#8B5CF6', facebook:'#1877F2'}};
var LABELS = {{geen:'Geen website', instagram:'Alleen Instagram', facebook:'Alleen Facebook'}};
var data = {data_json};

var cluster = L.markerClusterGroup({{maxClusterRadius: 60, disableClusteringAtZoom: 17}});

data.forEach(function(p) {{
  var color = COLORS[p.t] || '#EF4444';
  var label = LABELS[p.t] || 'Geen website';
  var marker = L.circleMarker([p.lt, p.ln], {{
    radius: 8, color: '#fff', weight: 1,
    fillColor: color, fillOpacity: 0.9
  }});
  var social = p.s ? '<br><a href="' + p.s + '" target="_blank" style="color:#8B5CF6">Social profiel →</a>' : '';
  marker.bindPopup(
    '<b>' + p.n + '</b><br>' +
    '<span style="color:#666;font-size:12px">' + p.a + '</span><br>' +
    (p.p ? '📞 ' + p.p + '<br>' : '') +
    '<span style="background:' + color + ';color:white;font-size:11px;padding:1px 6px;border-radius:4px">' + label + '</span>' +
    social +
    '<br><a href="' + p.m + '" target="_blank" ' +
    'style="display:inline-block;margin-top:6px;background:#4285F4;color:white;' +
    'padding:3px 8px;border-radius:4px;text-decoration:none;font-size:12px">Open in Maps</a>',
    {{maxWidth: 240}}
  );
  cluster.addLayer(marker);
}});

map.addLayer(cluster);
</script>
</body>
</html>"""

    Path(KAART_BESTAND).write_text(html, encoding="utf-8")
    print(f"🗺  Kaart: {KAART_BESTAND} ({len(data)} markers)")


# ── HOOFDPROGRAMMA ────────────────────────────────────────────────────────────

def bereken_kosten(grid: list, types: list) -> float:
    zoek_calls = len(grid) * len(types) * 1.5  # gem. 1.5 pagina's
    zoek_kosten = zoek_calls * 0.032
    # Schat 30% van resultaten als nieuw + details
    detail_calls = zoek_calls * 20 * 0.30  # 20 results per call, 30% nieuw
    detail_kosten = detail_calls * 0.020
    return zoek_kosten + detail_kosten


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kaart-only", action="store_true", help="Genereer alleen kaart uit checkpoint")
    parser.add_argument("--wijken", nargs="+", choices=list(GEBIEDEN.keys()),
                        help="Alleen deze wijken doorzoeken")
    parser.add_argument("--ja", action="store_true", help="Sla bevestigingsvraag over")
    args = parser.parse_args()

    # Kaart-only modus
    if args.kaart_only:
        _, prospects = laad_checkpoint()
        maak_kaart(prospects)
        sla_csv(prospects)
        return

    if not API_KEY:
        raise SystemExit(
            "❌ Stel de API-key in:\n"
            "   export GOOGLE_PLACES_API_KEY='AIza...'\n"
            "   Gratis credits: console.cloud.google.com → nieuw project → Places API"
        )

    gebieden = {k: v for k, v in GEBIEDEN.items() if not args.wijken or k in args.wijken}
    grid = maak_grid(gebieden)
    geschatte_kosten = bereken_kosten(grid, TYPES)

    print(f"\n🗺  Wijken: {', '.join(gebieden.keys())}")
    print(f"📍 Grid: {len(grid)} punten × {len(TYPES)} types")
    print(f"💰 Geschatte API-kosten: ~${geschatte_kosten:.0f} USD")
    print(f"   (Google geeft nieuwe accounts $300 gratis krediet)")
    if not args.ja:
        print("\nDruk ENTER om te starten, Ctrl+C om te stoppen.")
        try:
            input()
        except KeyboardInterrupt:
            return

    client = googlemaps.Client(key=API_KEY)
    done_ids, prospects = laad_checkpoint()
    seen_ids = set(done_ids)

    try:
        for i, (lat, lon) in enumerate(grid):
            print(f"\n[{i+1}/{len(grid)}] ({lat:.4f}, {lon:.4f})")

            alle_ids: set[str] = set()
            for btype in TYPES:
                ids = zoek_nearby(client, lat, lon, btype)
                alle_ids |= ids
                time.sleep(0.15)

            nieuwe_ids = alle_ids - seen_ids
            print(f"  Gevonden: {len(alle_ids)} | Nieuw te checken: {len(nieuwe_ids)}")

            for pid in nieuwe_ids:
                seen_ids.add(pid)
                details = haal_details(client, pid)
                time.sleep(0.08)

                if details.get("business_status") != "OPERATIONAL":
                    continue

                website = (details.get("website") or "").lower()
                SOCIAAL = ("instagram.com", "instagr.am", "facebook.com", "fb.com", "fb.me")
                is_sociaal = any(s in website for s in SOCIAAL)

                if website and not is_sociaal:
                    continue  # Heeft echte website — skip

                if is_sociaal:
                    web_type = "instagram" if "instagram" in website or "instagr.am" in website else "facebook"
                else:
                    web_type = "geen"

                loc = details.get("geometry", {}).get("location", {})
                prospect = {
                    "name":       details.get("name", "Onbekend"),
                    "address":    details.get("formatted_address", ""),
                    "phone":      details.get("formatted_phone_number", ""),
                    "rating":     details.get("rating", ""),
                    "reviews":    details.get("user_ratings_total", ""),
                    "types":      ", ".join(details.get("types", details.get("type", []))),
                    "web_type":   web_type,
                    "social_url": details.get("website", "") if is_sociaal else "",
                    "lat":        loc.get("lat"),
                    "lon":        loc.get("lng"),
                    "maps_url":   details.get("url", ""),
                    "place_id":   pid,
                }
                prospects.append(prospect)
                print(f"  ➕ {prospect['name']}")

            sla_checkpoint(seen_ids, prospects)

    except KeyboardInterrupt:
        print("\n\n⏸  Onderbroken — checkpoint bewaard.")

    sla_csv(prospects)
    maak_kaart(prospects)
    print(f"\n🎯 Klaar! {len(prospects)} prospects gevonden zonder website.")


if __name__ == "__main__":
    main()
