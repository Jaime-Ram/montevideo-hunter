#!/usr/bin/env python3
"""
Haal openingstijden op voor de gefilterde prospects.
Slaat op in openingstijden.json — hervatbaar (checkpoint-gebaseerd).
Gebruik:
    export GOOGLE_PLACES_API_KEY="AIza..."
    python3 haal_uren.py
Kosten: ~$0.017 per call ≈ $62 voor 3660 prospects
"""

import csv
import json
import os
import time
from pathlib import Path

try:
    import googlemaps
except ImportError:
    raise SystemExit("pip install googlemaps")

API_KEY    = os.getenv("GOOGLE_PLACES_API_KEY", "")
INPUT_CSV  = "prospects_gefilterd.csv"
OUTPUT_JSON = "openingstijden.json"


def main():
    if not API_KEY:
        raise SystemExit(
            "❌ Stel de API key in:\n"
            "   export GOOGLE_PLACES_API_KEY='AIza...'"
        )

    # Laad gefilterde place_ids
    place_ids: list[str] = []
    with open(INPUT_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = row.get("place_id", "").strip()
            if pid:
                place_ids.append(pid)

    print(f"📍 {len(place_ids)} prospects in {INPUT_CSV}")

    # Laad bestaande data (hervatbaar)
    uren: dict = {}
    if Path(OUTPUT_JSON).exists():
        uren = json.loads(Path(OUTPUT_JSON).read_text(encoding="utf-8"))
        met = sum(1 for v in uren.values() if v and v.get("periods"))
        print(f"♻  Al opgehaald: {len(uren)} ({met} met uren)")

    todo = [pid for pid in place_ids if pid not in uren]
    print(f"🔄 Nog te halen: {len(todo)}")
    print(f"💰 Geschatte kosten: ~${len(todo) * 0.017:.0f} USD")
    print("\nDruk ENTER om te starten, Ctrl+C om te stoppen.")
    try:
        input()
    except KeyboardInterrupt:
        return

    client = googlemaps.Client(key=API_KEY)

    try:
        for i, pid in enumerate(todo):
            try:
                r  = client.place(pid, fields=["opening_hours"], language="es")
                oh = r.get("result", {}).get("opening_hours")
                uren[pid] = oh if oh else {}
            except Exception as e:
                print(f"  ⚠ {pid}: {e}")
                uren[pid] = {}

            if (i + 1) % 100 == 0:
                Path(OUTPUT_JSON).write_text(
                    json.dumps(uren, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(f"  [{i+1}/{len(todo)}] checkpoint opgeslagen")

            time.sleep(0.08)

    except KeyboardInterrupt:
        print("\n⏸  Onderbroken — checkpoint bewaard.")

    Path(OUTPUT_JSON).write_text(
        json.dumps(uren, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    met = sum(1 for v in uren.values() if v and v.get("periods"))
    print(f"\n✅ Klaar! {met}/{len(uren)} bedrijven hebben openingstijden.")
    print("Draai daarna: python3 filter_kaart.py  (om de kaart bij te werken)")


if __name__ == "__main__":
    main()
