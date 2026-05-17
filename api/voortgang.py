from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request

KV_URL   = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL", "")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
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


def _kv_set(d: dict):
    if not KV_URL:
        return
    body = json.dumps({"value": json.dumps(d, ensure_ascii=False)}).encode()
    req = urllib.request.Request(
        f"{KV_URL}/set/{KEY}",
        data=body,
        headers={
            "Authorization": f"Bearer {KV_TOKEN}",
            "Content-Type": "application/json",
        },
    )
    urllib.request.urlopen(req)


class handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        self._send(200, json.dumps(_kv_get(), ensure_ascii=False).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        b = json.loads(self.rfile.read(length))
        pid = b.get("place_id", "")
        if not pid:
            self._send(400, b'{"ok":false}')
            return
        d = _kv_get()
        d[pid] = {
            "status":  b.get("status", ""),
            "notitie": b.get("notitie", ""),
            "naam":    b.get("naam", ""),
            "tijd":    b.get("tijd", ""),
        }
        _kv_set(d)
        self._send(200, b'{"ok":true}')
