#!/usr/bin/env python3
"""Static server + mock license server for SimDrive 3D clone."""
import json, os, re, sys, html
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import traceback
import licensing

REPO = os.environ.get("REPO_DIR", "/root/simdrive-3d")
PORT = int(os.environ.get("PORT", "8099"))

# skema yang diminta klien: {licensed, trialUsed, trialLeftMs, expiresAt}
# licensed:true + expiresAt:null -> status 'lifetime_active' -> simulator terbuka penuh
TRIAL_LICENSE = json.dumps({
    "licensed": True, "trialUsed": True, "trialLeftMs": 0, "expiresAt": None
})
ACTIVATE_OK = json.dumps({"ok": True, "message": "Lisensi berhasil diaktifkan"})
ACTIVATE_BAD = json.dumps({"ok": False, "message": "Kode lisensi tidak valid"})
SESSION_OK = json.dumps({"valid": True})

# hash -> (name, response)
SERVER_FNS = {
    "7a469d2260b69be33667b773b6cf0b17f5b3172b09e9e53d31b7c179d228239f": ("check", TRIAL_LICENSE),
    "5f9688103a94c2b709cbdbc756d787f674ee2878a65f2f3430016c0786ed1639": ("verify", TRIAL_LICENSE),
    "ddd70843e0985a45c37b01bfe84b1f703ef93bfffdcaccc52a4545ff9fe3d012": ("activate", ACTIVATE_OK),
    "f6c2d91ec64a2386829008c4e4dbb5535db43181e96f0f0508554643530294c4": ("deactivate", TRIAL_LICENSE),
    "512c1ed33d8f9f2d8c0e27abffde2948fcecbc1c65e3a63765e465504995672e": ("device_identify", "{}"),
    "94066eae80d63dbc8098ba48c5ff92c2db6c6556d13b73057a4cc8197674a626": ("device_bind", "{}"),
    "3165138a4c311591f80a31d2569667280f9204b28349b37af60ab0c83cac680d": ("session_validate", SESSION_OK),
}

MIME = {
    ".js": "application/javascript", ".mjs": "application/javascript",
    ".css": "text/css", ".json": "application/json", ".html": "text/html",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".gif": "image/gif", ".svg": "image/svg+xml",
    ".glb": "model/gltf-binary", ".gltf": "model/gltf+json",
    ".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".webm": "video/webm",
    ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf",
    ".txt": "text/plain",
}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=REPO, **kwargs)

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n) if n else b""
            obj = json.loads(raw.decode("utf-8", "ignore") or "{}")
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}

    def _api(self, path, payload):
        """Lisensi milik sendiri. Return dict | None kalau bukan route API."""
        if path in ("/api/license/check", "/api/license/verify"):
            print(f"[dev] {str(payload.get('deviceId'))[:16]}", file=sys.stderr, flush=True)
            return licensing.check(payload.get("deviceId", ""), payload.get("hw", ""), payload.get("info"))
        if path == "/api/license/activate":
            return licensing.activate(str(payload.get("code", "")).strip(),
                                      payload.get("deviceId", ""), payload.get("hw", ""))
        if path == "/api/license/deactivate":
            return licensing.deactivate(payload.get("deviceId", ""))
        if path == "/api/license/identify":
            return {"deviceId": payload.get("deviceId", "")}
        if path == "/api/license/bind":
            licensing.bind(payload.get("deviceId", ""), payload.get("hw", ""))
            return {"ok": True}
        if path == "/api/license/session":
            return {"valid": True}
        if path == "/api/license/stats":
            return licensing.stats()
        if path.startswith("/api/license/admin/"):
            if not licensing.auth(self.headers.get("x-admin-token")):
                return {"ok": False, "message": "Token admin salah."}
            act = path.rsplit("/", 1)[1]
            if act == "list":
                return {"ok": True, "codes": licensing.list_codes(), "stats": licensing.stats()}
            if act == "create":
                return licensing.create_codes(payload.get("count", 1), payload.get("days", 0),
                                              payload.get("note", ""), payload.get("customer", ""))
            if act == "revoke":
                return licensing.revoke(str(payload.get("code", "")).strip())
            if act == "auto":
                return {"ok": True, "auto": licensing.set_auto(bool(payload.get("on")))}
            if act == "token":
                return {"ok": True, "token": licensing.token()}
        return None

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        fs = os.path.join(REPO, path.lstrip("/"))
        # SPA fallback: route tanpa ekstensi (mis. /play, /admin) -> index.html
        if not os.path.splitext(path)[1] and not os.path.isdir(fs):
            if not os.path.isfile(fs):
                self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        payload = self._read_json()
        print(f"[POST] {parsed.path}", file=sys.stderr, flush=True)
        if parsed.path.startswith("/api/license/"):
            try:
                out = self._api(parsed.path, payload)
            except Exception as e:
                traceback.print_exc()
                out = {"ok": False, "message": f"server error: {e}"}
            if out is not None:
                print(f"[license] {parsed.path} -> {json.dumps(out)[:200]}", file=sys.stderr, flush=True)
                self._json(out)
                return
        if parsed.path.startswith("/_serverFn/"):
            fn_id = parsed.path.split("/_serverFn/", 1)[1].strip("/")
            resp = SERVER_FNS.get(fn_id)
            if resp is None:
                # serverFn lain (simpan peta, checkout/premium): balas sukses generik
                out = {"ok": True, "success": True, "status": "ok", "data": {}, "products": [],
                       "paid": True, "orderId": "local", "url": None}
                print(f"[serverFn] {fn_id[:12]} -> generic ok", file=sys.stderr, flush=True)
                self._json(out)
                return
            if resp:
                name, body = resp
                # activation: check code from body
                if name == "activate":
                    try:
                        data = payload.get("data", payload)
                        if isinstance(data, str):
                            data = {}
                        code = str(data.get("code", "")).strip()
                        dev = data.get("deviceId", "")
                        hw = data.get("hw", "")
                        if code:
                            res = licensing.activate(code, dev, hw)
                            print(f"[+] Activate: {code} -> {res}", file=sys.stderr)
                            body = json.dumps(res, ensure_ascii=False)
                        else:
                            body = ACTIVATE_BAD
                    except Exception as e:
                        print(f"[!] activate parse err: {e}", file=sys.stderr)
                        body = ACTIVATE_BAD
                elif name == "device_identify":
                    dev = payload.get("data", {}).get("deviceId", "unknown") if isinstance(payload.get("data"), dict) else "unknown"
                    print(f"[*] Device: {str(dev)[:20]}", file=sys.stderr)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(body))
                self.end_headers()
                self.wfile.write(body.encode())
                return
            # unknown server fn
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"{}")
            return

        self.send_error(405)

    def send_response(self, code, message=None):
        if hasattr(self, '_original_send_response'):
            super().send_response(code, message)
        else:
            super().send_response(code, message)

    def guess_type(self, path):
        base, ext = os.path.splitext(path)
        if ext.lower() in MIME:
            return MIME[ext.lower()]
        return super().guess_type(path)

    def log_message(self, fmt, *args):
        # quiet default logging, log errors only
        pass

def run():
    srv = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"SimDrive 3D mock server → http://0.0.0.0:{PORT}/", flush=True)
    print(f"Serving: {REPO}", flush=True)
    print(f"License mock: {len(SERVER_FNS)} serverFns active", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()

if __name__ == "__main__":
    run()
