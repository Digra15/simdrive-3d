#!/usr/bin/env python3
"""Static server + mock license server for BangPay Simulator clone."""
import json, os, re, sys, html
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import traceback

REPO = os.environ.get("REPO_DIR", "/root/bangpay-simulator")
PORT = int(os.environ.get("PORT", "8099"))

TRIAL_LICENSE = json.dumps({
    "t": {"i": 6, "s": "{}", "c": 2, "e": 1, "a": "", "f": 1, "b": 0, "o": 0},
    "f": 127, "m": []
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

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/_serverFn/"):
            fn_id = parsed.path[12:]
            resp = SERVER_FNS.get(fn_id)
            if resp:
                name, body = resp
                # activation: check code from body
                if name == "activate":
                    try:
                        length = int(self.headers.get("Content-Length", 0))
                        body_raw = self.rfile.read(length).decode("utf-8", "ignore")
                        # try parse as JSON / seroval
                        obj = json.loads(body_raw) if body_raw.strip().startswith("{") else {}
                        data = obj.get("data", {})
                        if isinstance(data, str):
                            data = {}
                        code = str(data.get("code", "")).strip()
                        if code and len(code) == 6 and code.isdigit():
                            print(f"[+] Activate: {code}", file=sys.stderr)
                            body = ACTIVATE_OK
                        else:
                            body = ACTIVATE_BAD
                    except Exception as e:
                        print(f"[!] activate parse err: {e}", file=sys.stderr)
                        body = ACTIVATE_BAD
                elif name == "device_identify":
                    try:
                        length = int(self.headers.get("Content-Length", 0))
                        body_raw = self.rfile.read(length).decode("utf-8", "ignore")
                        obj = json.loads(body_raw) if body_raw.strip().startswith("{") else {}
                        dev = obj.get("data", {}).get("deviceId", "unknown") if isinstance(obj.get("data"), dict) else "unknown"
                        print(f"[*] Device: {dev[:20]}", file=sys.stderr)
                    except: pass
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

        if parsed.path == "/__l5e/trackevents":
            self.send_response(200)
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
    print(f"BangPay Simulator mock server → http://0.0.0.0:{PORT}/", flush=True)
    print(f"Serving: {REPO}", flush=True)
    print(f"License mock: {len(SERVER_FNS)} serverFns active", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()

if __name__ == "__main__":
    run()
