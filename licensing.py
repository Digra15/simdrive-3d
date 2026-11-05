"""Sistem lisensi sendiri untuk SimDrive 3D.

Skema:
- kode 6 digit (dibuat via CLI / API admin bertoken)
- 1 kode = 1 perangkat (bind saat aktivasi)
- days=0 -> permanen (lifetime), days>0 -> expiry dihitung saat aktivasi
- mode `auto` = semua perangkat otomatis licensed (default ON, biar app langsung jalan)
"""
import json, os, secrets, threading, datetime, hmac, hashlib

STORE = os.environ.get("SD_LICENSE_STORE", "/root/simdrive-3d/license_store.json")
TRIAL_MS = 120000
# Harus identik dengan SECRET di sd-license.js
SIG_SECRET = os.environ.get("SD_SIG_SECRET", "s3cr3t-simdrive3d-v1-8f2c1d94a7b34e6f")
_lock = threading.Lock()


def keygen(device_id):
    """Kode 6 digit terikat perangkat: HMAC-SHA256(secret, 'simdrive3d|v1|'+deviceId)."""
    msg = ("simdrive3d|v1|" + str(device_id)).encode()
    dig = hmac.new(SIG_SECRET.encode(), msg, hashlib.sha256).digest()
    v = int.from_bytes(dig[:4], "big")
    return f"{v % 1000000:06d}"


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


def _parse(s):
    return datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def _default():
    return {
        "version": 1,
        "auto": True,
        "admin_token": secrets.token_hex(8),
        "codes": {},
        "bindings": {},
        "trials": {},
        "devices": {},
        "created": _iso(_now()),
    }


def load():
    if not os.path.exists(STORE):
        st = _default()
        _save(st)
        return st
    with open(STORE) as f:
        st = json.load(f)
    changed = False
    for k, v in _default().items():
        if k not in st:
            st[k] = v
            changed = True
    if changed:
        _save(st)
    return st


def _save(st):
    tmp = STORE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f, indent=2)
    os.replace(tmp, STORE)


def token():
    return load().get("admin_token", "")


def auth(t):
    tok = token()
    return bool(t) and bool(tok) and secrets.compare_digest(str(t), tok)


def _license_for(st, dev):
    code = st["bindings"].get(dev)
    if not code:
        return None
    c = st["codes"].get(code)
    if not c or c.get("revoked"):
        st["bindings"].pop(dev, None)
        return None
    return c


def _unlicensed():
    return {"licensed": False, "trialUsed": True, "trialLeftMs": 0, "expiresAt": None}


def check(dev, hw="", info=None):
    with _lock:
        st = load()
        if dev:
            st["devices"][dev] = {"last": _iso(_now()), "hw": hw, "info": info or {}}
        c = _license_for(st, dev) if dev else None
        if c:
            if c.get("permanent"):
                _save(st)
                return {"licensed": True, "trialUsed": True, "trialLeftMs": 0, "expiresAt": None}
            exp = c.get("expiresAt")
            if exp and _now() < _parse(exp):
                _save(st)
                return {"licensed": True, "trialUsed": True, "trialLeftMs": 0, "expiresAt": exp}
            _save(st)
            return _unlicensed()
        if st.get("auto"):
            _save(st)
            return {"licensed": True, "trialUsed": True, "trialLeftMs": 0, "expiresAt": None}
        t = st["trials"].get(dev)
        if not t:
            # cek pertama: trial tersedia, BELUM dimulai
            st["devices"][dev] = st["devices"].get(dev, {"last": _iso(_now()), "hw": hw, "info": info or {}})
            _save(st)
            return {"licensed": False, "trialUsed": False, "trialLeftMs": TRIAL_MS, "expiresAt": None}
        remaining = TRIAL_MS - int((_now() - _parse(t["started"])).total_seconds() * 1000)
        if remaining > 0:
            _save(st)
            return {"licensed": False, "trialUsed": True, "trialLeftMs": TRIAL_MS, "expiresAt": None}
        _save(st)
        return _unlicensed()


def activate(code, dev, hw=""):
    with _lock:
        st = load()
        c = st["codes"].get(code)
        if not c and dev and code == keygen(dev):
            # kode hasil keygen offline (terikat perangkat), belum tercatat
            c = {"code": code, "days": 0, "permanent": True, "created": _iso(_now()),
                 "note": "keygen", "customer": "", "deviceId": None, "activatedAt": None, "revoked": False}
            st["codes"][code] = c
        if not c:
            return {"ok": False, "message": "Kode lisensi tidak ditemukan."}
        if c.get("revoked"):
            return {"ok": False, "message": "Kode lisensi sudah dicabut."}
        if c.get("deviceId") and c["deviceId"] != dev:
            return {"ok": False, "message": "Kode sudah dipakai di perangkat lain."}
        c["deviceId"] = dev
        c["activatedAt"] = _iso(_now())
        c["hw"] = hw
        if not c.get("permanent"):
            c["expiresAt"] = _iso(_now() + datetime.timedelta(days=int(c.get("days") or 0)))
        st["bindings"][dev] = code
        _save(st)
        msg = "Lisensi aktif — lifetime." if c.get("permanent") else f"Lisensi aktif {c.get('days')} hari."
        return {"ok": True, "message": msg}


def deactivate(dev):
    with _lock:
        st = load()
        code = st["bindings"].pop(dev, None)
        if code and code in st["codes"]:
            c = st["codes"][code]
            c["deviceId"] = None
            c["activatedAt"] = None
            c.pop("expiresAt", None)
        _save(st)
    return check(dev)


def bind(dev, hw=""):
    with _lock:
        st = load()
        if dev:
            st["devices"][dev] = {"last": _iso(_now()), "hw": hw}
            _save(st)


def create_codes(count=1, days=0, note="", customer=""):
    out = []
    with _lock:
        st = load()
        for _ in range(max(1, min(int(count), 500))):
            while True:
                code = f"{secrets.randbelow(1000000):06d}"
                if code not in st["codes"]:
                    break
            st["codes"][code] = {
                "code": code,
                "days": max(0, int(days)),
                "permanent": int(days) <= 0,
                "created": _iso(_now()),
                "note": note,
                "customer": customer,
                "deviceId": None,
                "activatedAt": None,
                "revoked": False,
            }
            out.append(code)
        _save(st)
    return {"ok": True, "codes": out, "days": max(0, int(days)), "permanent": int(days) <= 0}


def list_codes():
    st = load()
    return sorted(st["codes"].values(), key=lambda c: c.get("created", ""), reverse=True)


def revoke(code):
    with _lock:
        st = load()
        if code not in st["codes"]:
            return {"ok": False, "message": "Kode tidak ada."}
        st["codes"][code]["revoked"] = True
        for d, c in list(st["bindings"].items()):
            if c == code:
                st["bindings"].pop(d)
        _save(st)
    return {"ok": True, "message": "Kode dicabut."}


def set_auto(on):
    with _lock:
        st = load()
        st["auto"] = bool(on)
        _save(st)
    return st["auto"]


def stats():
    st = load()
    return {
        "codes": len(st["codes"]),
        "active": len(st["bindings"]),
        "devices": len(st["devices"]),
        "auto": st["auto"],
    }
