#!/usr/bin/env python3
"""
Filter & Kaart — v4
- Enkel prospects met telefoon + rating
- Precieze categorieën
- Categorie-filter panel op mobiele kaart (multi-select, slide-in)
- Standaard Leaflet popup (vanuit bolletje)
"""

import csv
import json
from pathlib import Path

INPUT_CSV  = "prospects.csv"
OUTPUT_CSV = "prospects_gefilterd.csv"
OUTPUT_MAP = "kaart_gefilterd.html"

# ── CATEGORIEËN (precies) ─────────────────────────────────────────────────────

CATEGORIEEN = {
    "Kapper":             {"types": ["hair_care", "barber"],                         "kleur": "#F472B6"},
    "Nagelstudio":        {"types": ["nail_salon"],                                  "kleur": "#EC4899"},
    "Schoonheidssalon":   {"types": ["beauty_salon", "skin_care"],                   "kleur": "#DB2777"},
    "Spa & Massage":      {"types": ["spa", "massage"],                              "kleur": "#A855F7"},
    "Restaurant":         {"types": ["restaurant", "meal_takeaway", "meal_delivery"],"kleur": "#F97316"},
    "Café & Bar":         {"types": ["cafe", "bar", "coffee_shop", "night_club"],    "kleur": "#FB923C"},
    "Bakkerij":           {"types": ["bakery"],                                      "kleur": "#FBBF24"},
    "Sportschool":        {"types": ["gym", "sports_club"],                          "kleur": "#22C55E"},
    "Supermarkt":         {"types": ["supermarket", "convenience_store",
                                     "grocery_or_supermarket"],                      "kleur": "#16A34A"},
    "Kledingwinkel":      {"types": ["clothing_store", "shoe_store"],                "kleur": "#3B82F6"},
    "Elektronicawinkel":  {"types": ["electronics_store"],                           "kleur": "#1D4ED8"},
    "Bloemenwinkel":      {"types": ["florist"],                                     "kleur": "#10B981"},
    "Dierenwinkel":       {"types": ["pet_store"],                                   "kleur": "#059669"},
    "Winkel (overig)":    {"types": ["store", "book_store", "home_goods_store",
                                     "furniture_store", "jewelry_store",
                                     "bicycle_store", "hardware_store",
                                     "shopping_mall", "gift_shop"],                 "kleur": "#60A5FA"},
    "Tandarts":           {"types": ["dentist"],                                     "kleur": "#EF4444"},
    "Apotheek":           {"types": ["pharmacy"],                                    "kleur": "#DC2626"},
    "Dokter / Kliniek":   {"types": ["doctor", "hospital", "physiotherapist",
                                     "health"],                                      "kleur": "#B91C1C"},
    "Dierenarts":         {"types": ["veterinary_care"],                             "kleur": "#991B1B"},
    "Autogarage":         {"types": ["car_repair", "car_wash"],                      "kleur": "#6B7280"},
    "Wasserette":         {"types": ["laundry"],                                     "kleur": "#9CA3AF"},
    "Makelaar":           {"types": ["real_estate_agency"],                          "kleur": "#64748B"},
    "Diensten (overig)":  {"types": ["locksmith", "travel_agency", "insurance_agency",
                                     "accounting", "lawyer", "electrician"],         "kleur": "#94A3B8"},
    "Hotel / Verblijf":   {"types": ["lodging", "hotel", "hostel", "motel"],         "kleur": "#EAB308"},
    "Overig":             {"types": [],                                              "kleur": "#CBD5E1"},
}

# ── ZONES op basis van echte straten (geocoded) ───────────────────────────────

ZONES = {
    "Centro — Convención / Ejido":
        {"sw": (-34.912, -56.202), "ne": (-34.892, -56.185), "kleur": "#4F46E5"},
    "Centro — Ejido / Bulevar Artigas":
        {"sw": (-34.912, -56.185), "ne": (-34.892, -56.162), "kleur": "#818CF8"},
    "Cordón — boven 18 de Julio":
        {"sw": (-34.904, -56.166), "ne": (-34.888, -56.152), "kleur": "#7C3AED"},
    "Cordón — 18 Jul → Bulevar España":
        {"sw": (-34.914, -56.166), "ne": (-34.904, -56.152), "kleur": "#A78BFA"},
    "Palermo — Jackson / Solano García":
        {"sw": (-34.918, -56.159), "ne": (-34.888, -56.144), "kleur": "#C026D3"},
    "Parque Rodó — Rbla. Wilson / Gonzalo":
        {"sw": (-34.920, -56.178), "ne": (-34.900, -56.162), "kleur": "#BE185D"},
    "Punta Carretas — Ellauri / Benito Blanco":
        {"sw": (-34.930, -56.158), "ne": (-34.908, -56.143), "kleur": "#0284C7"},
    "Punta Carretas — Benito Blanco / 26 Marzo":
        {"sw": (-34.940, -56.150), "ne": (-34.930, -56.120), "kleur": "#38BDF8"},
    "Pocitos — Artigas / 21 de Setiembre":
        {"sw": (-34.924, -56.168), "ne": (-34.904, -56.156), "kleur": "#0EA5E9"},
    "Pocitos — 21 Set / Ellauri":
        {"sw": (-34.924, -56.156), "ne": (-34.904, -56.147), "kleur": "#22D3EE"},
    "Pocitos — Ellauri / 26 de Marzo":
        {"sw": (-34.924, -56.147), "ne": (-34.904, -56.128), "kleur": "#67E8F9"},
}

# ── FUNCTIES ──────────────────────────────────────────────────────────────────

def bepaal_categorie(types_str: str) -> str:
    types = [t.strip() for t in (types_str or "").split(",")]
    for naam, info in CATEGORIEEN.items():
        if naam == "Overig":
            continue
        if any(t in info["types"] for t in types):
            return naam
    return "Overig"

def bepaal_zone(lat: float, lon: float) -> str:
    for naam, z in ZONES.items():
        if z["sw"][0] <= lat <= z["ne"][0] and z["sw"][1] <= lon <= z["ne"][1]:
            return naam
    return "Buiten zones"

def laad_en_filter(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("phone"):
                continue
            if not row.get("rating"):
                continue
            try:
                lat    = float(row["lat"])
                lon    = float(row["lon"])
                rating = float(row["rating"])
            except (ValueError, TypeError):
                continue
            row["lat"]       = lat
            row["lon"]       = lon
            row["rating"]    = rating
            row["categorie"] = bepaal_categorie(row.get("types", ""))
            row["zone"]      = bepaal_zone(lat, lon)
            rows.append(row)
    return rows

def sla_csv(rows: list[dict], path: str):
    if not rows:
        return
    volgorde   = list(CATEGORIEEN.keys())
    gesorteerd = sorted(rows, key=lambda r: (volgorde.index(r["categorie"]), r["name"].lower()))
    velden = ["zone", "categorie", "name", "address", "phone", "rating",
              "reviews", "web_type", "social_url", "lat", "lon", "maps_url"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=velden, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(gesorteerd)
    print(f"✅ CSV: {path} ({len(gesorteerd)} bedrijven)")

def maak_kaart(rows: list[dict], path: str):
    markers = []
    for r in rows:
        web_label = {"geen": "Geen website", "instagram": "Instagram", "facebook": "Facebook"}.get(r.get("web_type","geen"), "")
        kleur_cat = CATEGORIEEN.get(r["categorie"], {}).get("kleur", "#CBD5E1")
        markers.append({
            "n":  r["name"],
            "a":  r.get("address", "")[:55],
            "p":  r.get("phone", ""),
            "r":  r.get("rating", ""),
            "rv": r.get("reviews", ""),
            "wl": web_label,
            "s":  r.get("social_url", "") or "",
            "m":  r.get("maps_url", "") or "",
            "lt": r["lat"],
            "ln": r["lon"],
            "c":  r["categorie"],
            "kl": kleur_cat,
            "z":  r["zone"],
        })

    zones_js     = json.dumps(
        {naam: {"sw": z["sw"], "ne": z["ne"], "kleur": z["kleur"]} for naam, z in ZONES.items()},
        ensure_ascii=False
    )
    cats_js      = json.dumps({naam: info["kleur"] for naam, info in CATEGORIEEN.items()}, ensure_ascii=False)
    markers_js   = json.dumps(markers, ensure_ascii=False, separators=(",", ":"))
    totaal       = len(markers)
    zone_counts: dict[str, int] = {}
    for r in rows:
        zone_counts[r["zone"]] = zone_counts.get(r["zone"], 0) + 1
    aantallen_js = json.dumps(zone_counts, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Montevideo — {totaal} prospects</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:sans-serif;font-size:13px}}
#map{{position:fixed;top:0;left:320px;right:0;bottom:0}}
#panel{{position:fixed;top:0;left:0;width:320px;height:100vh;background:#1e1e2e;
        color:#cdd6f4;overflow-y:auto;display:flex;flex-direction:column;z-index:1000}}
#panel-header{{padding:14px 16px;background:#313244;flex-shrink:0}}
#panel-header h2{{font-size:15px;font-weight:700;color:#cba6f7}}
#counter{{font-size:12px;color:#a6adc8;margin-top:3px}}
.section-title{{padding:10px 16px 4px;font-size:11px;font-weight:700;
                letter-spacing:.08em;text-transform:uppercase;color:#6c7086;flex-shrink:0}}
.zone-btn{{display:flex;align-items:center;gap:8px;padding:6px 16px;cursor:pointer;
           border:none;background:none;color:#cdd6f4;width:100%;text-align:left;font-size:13px}}
.zone-btn:hover{{background:#313244}}
.zone-btn.active{{background:#45475a}}
.zone-dot{{width:12px;height:12px;border-radius:2px;flex-shrink:0}}
.zone-count{{margin-left:auto;color:#6c7086;font-size:11px}}
.divider{{height:1px;background:#313244;margin:6px 0;flex-shrink:0}}
.cat-row{{display:flex;align-items:center;gap:8px;padding:5px 16px;cursor:pointer}}
.cat-row:hover{{background:#313244}}
.cat-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.cat-label{{flex:1;font-size:12px}}
.cat-count{{color:#6c7086;font-size:11px}}
input[type=checkbox]{{accent-color:#cba6f7;cursor:pointer}}
#btn-row{{padding:10px 16px;display:flex;gap:8px;flex-shrink:0}}
.btn{{flex:1;padding:6px;border-radius:6px;border:none;cursor:pointer;font-size:12px;font-weight:600}}
.btn-all{{background:#45475a;color:#cdd6f4}}
.btn-none{{background:#313244;color:#a6adc8}}
#zone-hint{{padding:0 16px 10px;font-size:11px;color:#6c7086;flex-shrink:0}}
</style>
</head>
<body>
<div id="panel">
  <div id="panel-header">
    <h2>Montevideo Prospects</h2>
    <div id="counter">Laden...</div>
  </div>
  <div class="section-title">Zones</div>
  <div id="zone-hint">Geen selectie = alles zichtbaar.</div>
  <div id="zone-list"></div>
  <div class="divider"></div>
  <div class="section-title">Categorieën</div>
  <div id="btn-row">
    <button class="btn btn-all" onclick="selectAllCats()">Alles aan</button>
    <button class="btn btn-none" onclick="deselectAllCats()">Alles uit</button>
  </div>
  <div id="cat-list"></div>
</div>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
var ZONES={zones_js};var CATS={cats_js};var MARKERS={markers_js};var AANTALLEN={aantallen_js};
var map=L.map('map').setView([-34.906,-56.160],14);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{attribution:'© OSM',maxZoom:19}}).addTo(map);
var selectedZones=new Set();var selectedCats=new Set(Object.keys(CATS));
var zoneCounts={{}};var catCounts={{}};
MARKERS.forEach(function(m){{zoneCounts[m.z]=(zoneCounts[m.z]||0)+1;catCounts[m.c]=(catCounts[m.c]||0)+1;}});
var cluster=L.markerClusterGroup({{maxClusterRadius:55,disableClusteringAtZoom:17,chunkedLoading:true,iconCreateFunction:function(c){{var n=c.getChildCount(),sz=n>100?42:n>30?36:30;return L.divIcon({{html:'<div style="background:#cba6f7;color:#1e1e2e;border-radius:50%;width:'+sz+'px;height:'+sz+'px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;box-shadow:0 2px 6px rgba(0,0,0,0.4)">'+n+'</div>',className:'',iconSize:[sz,sz],iconAnchor:[sz/2,sz/2]}});}}}});
map.addLayer(cluster);
var leafletMarkers=MARKERS.map(function(p){{var m=L.circleMarker([p.lt,p.ln],{{radius:7,color:'#1e1e2e',weight:1.2,fillColor:p.kl,fillOpacity:0.92}});var social=p.s?'<br><a href="'+p.s+'" target="_blank" style="color:#cba6f7;font-size:12px">Social →</a>':'';m.bindPopup('<div style="font-family:sans-serif;min-width:210px"><b style="font-size:14px">'+p.n+'</b><br><span style="background:'+p.kl+';color:white;font-size:11px;padding:1px 7px;border-radius:4px">'+p.c+'</span><br><br><span style="color:#555;font-size:12px">'+p.a+'</span><br>☎ <b>'+p.p+'</b><br>★ '+p.r+' ('+p.rv+' reviews)'+social+'<br><a href="'+p.m+'" target="_blank" style="display:inline-block;margin-top:7px;background:#4285F4;color:white;padding:4px 10px;border-radius:5px;text-decoration:none;font-size:12px">Open in Maps</a></div>',{{maxWidth:260}});return m;}});
function render(){{var toShow=[];var zA=selectedZones.size>0;MARKERS.forEach(function(p,i){{if((!zA||selectedZones.has(p.z))&&selectedCats.has(p.c))toShow.push(leafletMarkers[i]);}});cluster.clearLayers();cluster.addLayers(toShow);document.getElementById('counter').textContent=toShow.length+' van '+MARKERS.length+' prospects zichtbaar';}}
var zoneRects={{}};
Object.keys(ZONES).forEach(function(naam){{var z=ZONES[naam],cnt=AANTALLEN[naam]||0;var rect=L.rectangle([z.sw,z.ne],{{color:z.kleur,weight:2.5,fillColor:z.kleur,fillOpacity:0.07,dashArray:'8,5'}});var mid=[(z.sw[0]+z.ne[0])/2,(z.sw[1]+z.ne[1])/2];var short=naam.replace(/^.*— /,'');L.marker(mid,{{icon:L.divIcon({{html:'<div style="background:rgba(30,30,46,0.82);color:'+z.kleur+';padding:3px 7px;border-radius:5px;font-size:11px;font-weight:700;white-space:nowrap;border:1px solid '+z.kleur+';pointer-events:none">'+short+'<span style="color:#6c7086;font-weight:400"> '+cnt+'</span></div>',className:'',iconAnchor:[0,0]}}),interactive:false,zIndexOffset:-100}}).addTo(map);rect.on('click',function(){{toggleZone(naam);}});rect.addTo(map);zoneRects[naam]=rect;}});
function toggleZone(naam){{if(selectedZones.has(naam)){{selectedZones.delete(naam);zoneRects[naam].setStyle({{fillOpacity:0.08,weight:2}});document.querySelector('[data-zone="'+naam+'"]').classList.remove('active');}}else{{selectedZones.add(naam);zoneRects[naam].setStyle({{fillOpacity:0.25,weight:3}});document.querySelector('[data-zone="'+naam+'"]').classList.add('active');}}render();}}
var zl=document.getElementById('zone-list');Object.keys(ZONES).forEach(function(naam){{var z=ZONES[naam],cnt=zoneCounts[naam]||0;var btn=document.createElement('button');btn.className='zone-btn';btn.dataset.zone=naam;btn.innerHTML='<span class="zone-dot" style="background:'+z.kleur+'"></span><span>'+naam+'</span><span class="zone-count">'+cnt+'</span>';btn.onclick=function(){{toggleZone(naam);}};zl.appendChild(btn);}});
var cl=document.getElementById('cat-list');Object.keys(CATS).forEach(function(cat){{var cnt=catCounts[cat]||0;if(!cnt)return;var row=document.createElement('label');row.className='cat-row';row.innerHTML='<input type="checkbox" checked data-cat="'+cat+'"><span class="cat-dot" style="background:'+CATS[cat]+'"></span><span class="cat-label">'+cat+'</span><span class="cat-count">'+cnt+'</span>';row.querySelector('input').onchange=function(){{if(this.checked)selectedCats.add(cat);else selectedCats.delete(cat);render();}};cl.appendChild(row);}});
function selectAllCats(){{document.querySelectorAll('[data-cat]').forEach(function(cb){{cb.checked=true;selectedCats.add(cb.dataset.cat);}});render();}}
function deselectAllCats(){{document.querySelectorAll('[data-cat]').forEach(function(cb){{cb.checked=false;selectedCats.delete(cb.dataset.cat);}});render();}}
render();
</script>
</body>
</html>"""

    Path(path).write_text(html, encoding="utf-8")
    print(f"🗺  Kaart: {path} ({totaal} markers)")

def main():
    print("📂 Laden en filteren...")
    rows = laad_en_filter(INPUT_CSV)

    per_cat: dict[str, int]  = {}
    per_zone: dict[str, int] = {}
    for r in rows:
        per_cat[r["categorie"]]  = per_cat.get(r["categorie"], 0) + 1
        per_zone[r["zone"]]      = per_zone.get(r["zone"], 0) + 1

    print(f"\n✅ {len(rows)} prospects met nummer + rating\n")
    print("Categorieën:")
    for cat, n in sorted(per_cat.items(), key=lambda x: -x[1]):
        print(f"  {cat:<24} {n}")
    print("\nZones:")
    for zone, n in sorted(per_zone.items(), key=lambda x: -x[1]):
        print(f"  {zone:<24} {n}")

    sla_csv(rows, OUTPUT_CSV)
    maak_kaart(rows, OUTPUT_MAP)
    maak_mobiele_kaart(rows, "kaart_mobile.html")
    print(f"\nDesktop kaart: open {OUTPUT_MAP}")
    print(f"Mobiele kaart: python3 server.py")

def maak_mobiele_kaart(rows: list[dict], path: str):
    cat_counts: dict[str, int] = {}
    for r in rows:
        cat_counts[r["categorie"]] = cat_counts.get(r["categorie"], 0) + 1

    markers = []
    for r in rows:
        kleur = CATEGORIEEN.get(r["categorie"], {}).get("kleur", "#CBD5E1")
        markers.append({
            "id": r.get("place_id", ""),
            "n":  r["name"],
            "a":  r.get("address", "")[:55],
            "p":  r.get("phone", ""),
            "r":  str(r.get("rating", "")),
            "rv": str(r.get("reviews", "")),
            "c":  r["categorie"],
            "kl": kleur,
            "s":  r.get("social_url", "") or "",
            "m":  r.get("maps_url", "") or "",
            "lt": r["lat"],
            "ln": r["lon"],
        })

    markers_js = json.dumps(markers, ensure_ascii=False, separators=(",", ":"))
    cats_js    = json.dumps({n: i["kleur"] for n, i in CATEGORIEEN.items()}, ensure_ascii=False)
    totaal     = len(markers)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>Montevideo {totaal}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,system-ui,sans-serif;overflow:hidden}}
#map{{position:fixed;top:50px;left:0;right:0;bottom:0}}
#topbar{{
  position:fixed;top:0;left:0;right:0;height:50px;z-index:1000;
  background:rgba(20,20,30,0.95);backdrop-filter:blur(8px);
  display:flex;align-items:center;padding:0 12px;gap:10px;
  border-bottom:1px solid #333
}}
#topbar-title{{font-size:14px;font-weight:700;color:#cba6f7;white-space:nowrap}}
#counter{{font-size:12px;color:#888;flex:1}}
#filter-btn{{
  background:#2a2a3e;border:1px solid #555;color:#cdd6f4;
  border-radius:20px;padding:6px 14px;font-size:12px;cursor:pointer;
  white-space:nowrap;flex-shrink:0
}}
#filter-btn.active{{background:#cba6f7;color:#1e1e2e;border-color:#cba6f7}}
#overlay{{
  position:fixed;inset:0;background:rgba(0,0,0,0.45);z-index:1999;
  display:none;backdrop-filter:blur(1px)
}}
#overlay.open{{display:block}}
#fp{{
  position:fixed;top:0;right:-300px;bottom:0;width:280px;z-index:2000;
  background:#1e1e2e;border-left:1px solid #333;
  display:flex;flex-direction:column;transition:right .25s ease
}}
#fp.open{{right:0}}
#fp-head{{
  display:flex;align-items:center;padding:14px 16px;
  background:#313244;flex-shrink:0;gap:10px
}}
#fp-head span{{font-size:14px;font-weight:700;color:#cba6f7;flex:1}}
#fp-close{{
  background:none;border:none;color:#888;font-size:18px;cursor:pointer;
  width:28px;height:28px;display:flex;align-items:center;justify-content:center
}}
#fp-btns{{display:flex;gap:8px;padding:10px 14px;flex-shrink:0}}
.fp-btn{{
  flex:1;padding:7px;border-radius:8px;border:none;cursor:pointer;
  font-size:12px;font-weight:600
}}
.fp-all{{background:#45475a;color:#cdd6f4}}
.fp-none{{background:#313244;color:#888}}
#fp-list{{overflow-y:auto;flex:1;padding-bottom:8px}}
#fp-export{{padding:12px 14px;flex-shrink:0;border-top:1px solid #313244}}
#btn-export{{
  width:100%;padding:10px;background:#22C55E;color:white;
  border:none;border-radius:8px;font-size:13px;font-weight:700;cursor:pointer
}}
#btn-export:active{{background:#16a34a}}
.fp-row{{
  display:flex;align-items:center;gap:10px;
  padding:9px 16px;cursor:pointer;color:#cdd6f4
}}
.fp-row:active{{background:#313244}}
.fp-dot{{width:11px;height:11px;border-radius:50%;flex-shrink:0}}
.fp-label{{flex:1;font-size:13px}}
.fp-cnt{{font-size:11px;color:#6c7086}}
input[type=checkbox]{{
  accent-color:#cba6f7;width:17px;height:17px;flex-shrink:0;cursor:pointer
}}
.leaflet-popup-content-wrapper{{border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.18)}}
.leaflet-popup-content{{margin:14px 16px;min-width:230px}}
.pop-name{{font-size:16px;font-weight:700;margin-bottom:4px;line-height:1.2}}
.pop-badge{{display:inline-block;font-size:10px;padding:2px 7px;border-radius:4px;color:white;margin-bottom:8px}}
.pop-addr{{font-size:12px;color:#666;margin-bottom:6px;line-height:1.4}}
.pop-phone{{font-size:15px;font-weight:600;color:#16a34a;text-decoration:none;display:block;margin-bottom:5px}}
.pop-rating{{font-size:12px;color:#555;margin-bottom:8px}}
.pop-status{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px}}
.pop-sb{{
  padding:5px 9px;border-radius:7px;border:1.5px solid;cursor:pointer;
  font-size:11px;font-weight:600;background:white;opacity:0.45;transition:opacity .15s
}}
.pop-sb.active{{opacity:1;background:#f8f8f8}}
.pop-note{{
  width:100%;border:1px solid #ddd;border-radius:7px;padding:7px 8px;
  font-size:13px;resize:none;min-height:52px;font-family:inherit;
  background:#fafafa;margin-bottom:8px;display:block
}}
.pop-save{{
  width:100%;background:#cba6f7;color:#1e1e2e;border:none;border-radius:8px;
  padding:9px;font-size:13px;font-weight:700;cursor:pointer;display:block
}}
</style>
</head>
<body>

<div id="topbar">
  <span id="topbar-title">Montevideo</span>
  <span id="counter">{totaal} prospects</span>
  <button id="filter-btn">☰ Categorieën</button>
</div>

<div id="overlay"></div>

<div id="fp">
  <div id="fp-head">
    <span>Categorieën</span>
    <button id="fp-close">✕</button>
  </div>
  <div id="fp-btns">
    <button class="fp-btn fp-all" id="btn-all">Alles aan</button>
    <button class="fp-btn fp-none" id="btn-none">Alles uit</button>
  </div>
  <div id="fp-list"></div>
  <div id="fp-export">
    <button id="btn-export">📥 Exporteer naar Excel</button>
  </div>
</div>

<div id="map"></div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
var DATA        = {markers_js};
var CATS        = {cats_js};
var STATUS_KLEUR = {{verkocht:'#22C55E',interesse:'#3B82F6',later:'#F97316',nee:'#6B7280',dicht:'#EAB308'}};
var voortgang   = {{}};
var pending     = {{}};
var activePopup = {{pid:'',naam:''}};
var selectedCats = new Set(Object.keys(CATS));

// ── Kaart ─────────────────────────────────────────────────────────────────
var map = L.map('map',{{zoomControl:false}}).setView([-34.906,-56.160],14);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{attribution:'© OSM',maxZoom:19}}).addTo(map);
L.control.zoom({{position:'bottomright'}}).addTo(map);

var cluster = L.markerClusterGroup({{
  maxClusterRadius:55, disableClusteringAtZoom:17, chunkedLoading:true,
  iconCreateFunction:function(c) {{
    var n=c.getChildCount(), sz=n>100?44:n>30?38:32;
    return L.divIcon({{
      html:'<div style="background:#cba6f7;color:#1e1e2e;border-radius:50%;width:'+sz+'px;height:'+sz+'px;'+
           'display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;'+
           'box-shadow:0 2px 8px rgba(0,0,0,0.4)">'+n+'</div>',
      className:'', iconSize:[sz,sz], iconAnchor:[sz/2,sz/2]
    }});
  }}
}});
map.addLayer(cluster);

var pidToIdx = {{}};
DATA.forEach(function(p,i){{ pidToIdx[p.id]=i; }});

// ── Marker kleur ───────────────────────────────────────────────────────────
function markerKleur(p) {{
  var vg=voortgang[p.id], st=vg?vg.status:'';
  return STATUS_KLEUR[st] || p.kl;
}}

// ── Popup ──────────────────────────────────────────────────────────────────
function popupHtml(p) {{
  activePopup = {{pid:p.id, naam:p.n}};
  var vg=voortgang[p.id]||{{}};
  var pend=pending[p.id];
  var st=pend!==undefined ? pend : (vg.status||'');
  var STATUSSEN=[
    {{s:'verkocht', l:'✅ Verkocht',  c:'#22C55E'}},
    {{s:'interesse',l:'📞 Follow-up', c:'#3B82F6'}},
    {{s:'later',    l:'🔄 Later',     c:'#F97316'}},
    {{s:'nee',      l:'🚫 Nee',       c:'#6B7280'}},
    {{s:'dicht',    l:'🔒 Dicht',     c:'#EAB308'}},
  ];
  var sb='<div class="pop-status">';
  STATUSSEN.forEach(function(sv) {{
    var a=st===sv.s?' active':'';
    sb+='<button class="pop-sb'+a+'" data-s="'+sv.s+'" style="color:'+sv.c+';border-color:'+sv.c+'">'+sv.l+'</button>';
  }});
  sb+='</div>';
  return '<div class="pop-name">'+p.n+'</div>'+
    '<div><span class="pop-badge" style="background:'+p.kl+'">'+p.c+'</span></div>'+
    '<div class="pop-addr">'+p.a+'</div>'+
    (p.p ? '<a class="pop-phone" href="tel:'+p.p+'">📞 '+p.p+'</a>' : '')+
    (p.r ? '<div class="pop-rating">⭐ '+p.r+' <span style="color:#aaa">('+p.rv+' reviews)</span></div>' : '')+
    '<a href="'+p.m+'" target="_blank" style="font-size:12px;color:#4285F4;display:block;margin-bottom:10px">🗺 Maps (openingstijden →)</a>'+
    sb+
    '<textarea class="pop-note" id="nt_'+p.id+'" placeholder="Notitie...">'+( vg.notitie||'')+'</textarea>'+
    '<button class="pop-save">Opslaan</button>';
}}

function selStatus(status) {{
  var pid=activePopup.pid;
  pending[pid]=status;
  document.querySelectorAll('.pop-sb').forEach(function(btn) {{
    btn.classList.toggle('active', btn.dataset.s===status);
  }});
}}

function slaOp() {{
  var pid=activePopup.pid, naam=activePopup.naam;
  var st=pending[pid]!==undefined ? pending[pid] : (voortgang[pid] ? voortgang[pid].status : '');
  var ntEl=document.getElementById('nt_'+pid);
  var notitie=ntEl ? ntEl.value : '';
  voortgang[pid]={{status:st, notitie:notitie}};
  delete pending[pid];
  var idx=pidToIdx[pid];
  if (idx!==undefined) {{
    var kl=markerKleur(DATA[idx]);
    leafletMarkers[idx].setStyle({{fillColor:kl,color:st?kl:'#111',weight:st?2.5:1.5,fillOpacity:st==='nee'?0.4:0.9}});
  }}
  fetch('/api/voortgang',{{
    method:'POST', headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{place_id:pid,naam:naam,status:st,notitie:notitie}})
  }}).catch(function(){{}});
  map.closePopup();
}}

// ── Markers ────────────────────────────────────────────────────────────────
var leafletMarkers = DATA.map(function(p) {{
  var m=L.circleMarker([p.lt,p.ln],{{radius:8,color:'#111',weight:1.5,fillColor:p.kl,fillOpacity:0.9}});
  m.bindPopup(function(){{return popupHtml(p);}},{{maxWidth:300,minWidth:240}});
  return m;
}});

// ── Render ─────────────────────────────────────────────────────────────────
function render() {{
  var toShow=[];
  DATA.forEach(function(p,i) {{
    if (selectedCats.has(p.c)) toShow.push(leafletMarkers[i]);
  }});
  cluster.clearLayers();
  cluster.addLayers(toShow);
  document.getElementById('counter').textContent = toShow.length+' prospects';
}}

// ── Filter panel ───────────────────────────────────────────────────────────
function openFilter() {{
  document.getElementById('fp').classList.add('open');
  document.getElementById('overlay').classList.add('open');
  document.getElementById('filter-btn').classList.add('active');
}}
function closeFilter() {{
  document.getElementById('fp').classList.remove('open');
  document.getElementById('overlay').classList.remove('open');
  document.getElementById('filter-btn').classList.remove('active');
}}

// Categorielijst opbouwen (gesorteerd op aantal)
var catCounts={{}};
DATA.forEach(function(p){{ catCounts[p.c]=(catCounts[p.c]||0)+1; }});
var catsSorted=Object.keys(catCounts).sort(function(a,b){{return catCounts[b]-catCounts[a];}});
var fpList=document.getElementById('fp-list');
catsSorted.forEach(function(cat) {{
  var cnt=catCounts[cat], kleur=CATS[cat]||'#CBD5E1';
  var row=document.createElement('label');
  row.className='fp-row';
  row.innerHTML=
    '<input type="checkbox" checked data-cat="'+cat+'">'+
    '<span class="fp-dot" style="background:'+kleur+'"></span>'+
    '<span class="fp-label">'+cat+'</span>'+
    '<span class="fp-cnt">'+cnt+'</span>';
  row.querySelector('input').addEventListener('change',function() {{
    if(this.checked) selectedCats.add(cat); else selectedCats.delete(cat);
    render();
  }});
  fpList.appendChild(row);
}});

// ── Event delegation (popup knoppen) ───────────────────────────────────────
document.addEventListener('click',function(e) {{
  var sb=e.target.closest&&e.target.closest('.pop-sb');
  if (sb) {{selStatus(sb.dataset.s);return;}}
  var sv=e.target.closest&&e.target.closest('.pop-save');
  if (sv) {{slaOp();return;}}
}});

// ── Knop-listeners ─────────────────────────────────────────────────────────
document.getElementById('filter-btn').addEventListener('click',openFilter);
document.getElementById('fp-close').addEventListener('click',closeFilter);
document.getElementById('overlay').addEventListener('click',closeFilter);

document.getElementById('btn-all').addEventListener('click',function() {{
  document.querySelectorAll('[data-cat]').forEach(function(cb){{cb.checked=true;selectedCats.add(cb.dataset.cat);}});
  render();
}});
document.getElementById('btn-none').addEventListener('click',function() {{
  document.querySelectorAll('[data-cat]').forEach(function(cb){{cb.checked=false;selectedCats.delete(cb.dataset.cat);}});
  render();
}});

// ── Export naar CSV (opent in Excel) ──────────────────────────────────────
function exportCSV() {{
  var STATUS_NL = {{verkocht:'Verkocht',interesse:'Follow-up',later:'Later',nee:'Nee',dicht:'Dicht'}};
  var rijen = [['Naam','Status','Notitie','Categorie','Adres','Telefoon','Maps URL','Tijd']];
  DATA.forEach(function(p) {{
    var vg = voortgang[p.id];
    if (!vg || !vg.status) return;
    rijen.push([
      p.n,
      STATUS_NL[vg.status] || vg.status,
      vg.notitie || '',
      p.c,
      p.a,
      p.p || '',
      p.m || '',
      vg.tijd || ''
    ]);
  }});
  if (rijen.length <= 1) {{
    alert('Nog geen bedrijven gemarkeerd om te exporteren.');
    return;
  }}
  var csv = rijen.map(function(r) {{
    return r.map(function(c) {{ return '"' + String(c).replace(/"/g,'""') + '"'; }}).join(',');
  }}).join('\r\n');
  var blob = new Blob(['﻿' + csv], {{type:'text/csv;charset=utf-8;'}});
  var url  = URL.createObjectURL(blob);
  var a    = document.createElement('a');
  var datum = new Date().toISOString().slice(0,10);
  a.href = url; a.download = 'voortgang_' + datum + '.csv';
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(url);
}}
document.getElementById('btn-export').addEventListener('click', exportCSV);

// ── Voortgang laden ────────────────────────────────────────────────────────
fetch('/api/voortgang').then(function(r){{return r.json();}}).then(function(d){{
  voortgang=d;
  DATA.forEach(function(p,i) {{
    var vg=voortgang[p.id], st=vg?vg.status:'';
    if (st) {{
      var kl=markerKleur(p);
      leafletMarkers[i].setStyle({{fillColor:kl,color:kl,weight:2.5,fillOpacity:st==='nee'?0.4:0.9}});
    }}
  }});
}}).catch(function(){{}});

render();
</script>
</body>
</html>"""

    Path(path).write_text(html, encoding="utf-8")
    print(f"📱 Mobiel: {path} ({totaal} markers)")


if __name__ == "__main__":
    main()
