#!/usr/bin/env python3
"""
Voortgang-server
Draai op laptop → open op telefoon via http://[jouw-ip]:8765 (zelfde wifi)
Slaat status en notities op per bedrijf in voortgang.json
"""

import json, socket
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_file, Response

app   = Flask(__name__)
DATA  = Path("voortgang.json")
KAART = Path("kaart_mobile.html")

def laad():
    return json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {}

def opslaan(d):
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

@app.route("/")
def index():
    return send_file(KAART)

@app.route("/api/voortgang")
def get_voortgang():
    return jsonify(laad())

@app.route("/api/voortgang", methods=["POST"])
def set_voortgang():
    d   = laad()
    b   = request.json
    pid = b.get("place_id", "")
    if not pid:
        return jsonify({"ok": False}), 400
    d[pid] = {
        "status":  b.get("status", ""),
        "notitie": b.get("notitie", ""),
        "naam":    b.get("naam", ""),
        "tijd":    datetime.now().strftime("%d/%m %H:%M"),
    }
    opslaan(d)
    return jsonify({"ok": True})

@app.route("/api/stats")
def stats():
    d = laad()
    tellers = {}
    for v in d.values():
        s = v.get("status", "")
        tellers[s] = tellers.get(s, 0) + 1
    return jsonify({"totaal": len(d), "per_status": tellers})

if __name__ == "__main__":
    if not KAART.exists():
        print("❌ kaart_mobile.html niet gevonden. Draai eerst: python3 filter_kaart.py")
        exit(1)

    # Zoek lokaal IP-adres
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()

    print("\n" + "─"*50)
    print("🗺  Voortgang-server draait!")
    print(f"   💻 Laptop  → http://localhost:8765")
    print(f"   📱 Telefoon → http://{local_ip}:8765")
    print("   (Telefoon moet op hetzelfde wifi zitten)")
    print("─"*50 + "\n")
    app.run(host="0.0.0.0", port=8765, debug=False)
