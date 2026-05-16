from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request

KV_URL   = os.environ.get("KV_REST_API_URL", "")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN", "")
KEY      = "voortgang"


def _kv_get() -> dict:
    if not KV_URL:
        return {}
    req = urllib.request.Request(
        f"{KV_URL}/get/{KEY}",
        headers={"Authorization": f"Bearer {KV_TOKEN}"}
    )
    try:
        with urllib.request.urlopen(req) as r:
            raw = json.loads(r.read()).get("result")
        if not raw:
            return {}
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return {}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        d = _kv_get()
        tellers: dict = {}
        for v in d.values():
            s = v.get("status", "")
            tellers[s] = tellers.get(s, 0) + 1
        body = json.dumps({"totaal": len(d), "per_status": tellers}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
