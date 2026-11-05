/* SimDrive 3D — license engine (client-side, offline-capable).
   Skema sendiri:
     - deviceId: UUID di localStorage `sd_device` (dibuat sekali)
     - kode lisensi 6 digit = HMAC-SHA256(secret, "simdrive3d|v1|"+deviceId) -> uint32 -> mod 1e6
     - trial 120 detik sekali per perangkat
   Kalau backend /api/license/* hidup (serve.py), engine ini jadi cadangan saja.
   catatan: secret ikut ter-bundle; upgrade = pindah ke server-side signing (Vercel function).
*/
(function () {
  "use strict";
  var API = "/api/license";
  var SECRET = "s3cr3t-simdrive3d-v1-8f2c1d94a7b34e6f"; // ganti bila mau (harus sama dgn license_cli.py)
  var TRIAL_MS = 120000;
  var K_DEV = "sd_device", K_LIC = "sd_lic", K_TRIAL = "sd_trial_start";

  function uuid() {
    if (crypto && crypto.randomUUID) return crypto.randomUUID();
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      var r = (Math.random() * 16) | 0;
      return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
    });
  }

  function deviceId() {
    var d = null;
    try { d = localStorage.getItem(K_DEV); } catch (e) {}
    if (!d) {
      d = uuid();
      try { localStorage.setItem(K_DEV, d); } catch (e) {}
    }
    return d;
  }

  function hex6(deviceIdValue) {
    var msg = new TextEncoder().encode("simdrive3d|v1|" + deviceIdValue);
    var key = new TextEncoder().encode(SECRET);
    return crypto.subtle.importKey("raw", key, { name: "HMAC", hash: "SHA-256" }, false, ["sign"])
      .then(function (k) { return crypto.subtle.sign("HMAC", k, msg); })
      .then(function (sig) {
        var b = new Uint8Array(sig);
        var v = ((b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]) >>> 0;
        var s = String(v % 1000000);
        while (s.length < 6) s = "0" + s;
        return s;
      });
  }

  function trialLeft() {
    var t = null;
    try { t = parseInt(localStorage.getItem(K_TRIAL) || "", 10); } catch (e) {}
    if (!t || isNaN(t)) return TRIAL_MS;
    var left = TRIAL_MS - (Date.now() - t);
    return left > 0 ? left : 0;
  }

  function ensureTrialStart() {
    var t = null;
    try { t = localStorage.getItem(K_TRIAL); } catch (e) {}
    if (!t || t === "") {
      try { localStorage.setItem(K_TRIAL, String(Date.now())); } catch (e) {}
      return true;
    }
    return false;
  }

  function localState() {
    var d = deviceId();
    var rec = null;
    try { rec = JSON.parse(localStorage.getItem(K_LIC) || "null"); } catch (e) {}
    var started = false;
    try { started = !!parseInt(localStorage.getItem(K_TRIAL) || "", 10); } catch (e) {}
    // Tanpa backend: gate tetap tampil; lisensi divalidasi offline (kode keygen terikat perangkat)
    if (rec && rec.deviceId === d && rec.code) return { licensed: true, trialUsed: true, trialLeftMs: 0, expiresAt: null, offline: true };
    // Kontrak klien: trialUsed=false -> masih boleh "Coba Trial"; trial aktif -> trialUsed=true + trialLeftMs>0
    if (!started) {
      ensureTrialStart();
      return { licensed: false, trialUsed: true, trialLeftMs: TRIAL_MS, expiresAt: null, offline: true };
    }
    var left = trialLeft();
    return left > 0 ? { licensed: false, trialUsed: true, trialLeftMs: left, expiresAt: null, offline: true }
                    : { licensed: false, trialUsed: true, trialLeftMs: 0, expiresAt: null, offline: true };
  }

  function post(path, body) {
    return fetch(API + path, {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body || {})
    }).then(function (r) { if (!r.ok) throw Error("http " + r.status); return r.json(); });
  }

  function apiOrLocal(path, payload, localFn) {
    return post(path, payload).catch(function () { return localFn(); });
  }

  var SDL = {
    deviceId: deviceId,
    check: function (p) {
      p = p || {};
      return apiOrLocal("/check", p, localState);
    },
    verify: function (p) {
      p = p || {};
      return apiOrLocal("/verify", p, function () {
        var d = deviceId();
        return localState().then(function (s) {
          if (s.licensed) return s;
          try { localStorage.setItem(K_TRIAL, String(Date.now())); } catch (e) {}
          return { licensed: false, trialUsed: false, trialLeftMs: TRIAL_MS, expiresAt: null, offline: true };
        });
      });
    },
    activate: function (p) {
      p = p || {};
      return apiOrLocal("/activate", p, function () {
        var code = String(p.code || "").replace(/\D/g, "").slice(0, 6);
        var d = deviceId();
        return hex6(d).then(function (want) {
          if (code.length !== 6 || code !== want) {
            return { ok: false, message: "Kode lisensi tidak valid untuk perangkat ini." };
          }
          try { localStorage.setItem(K_LIC, JSON.stringify({ deviceId: d, code: code, at: new Date().toISOString() })); } catch (e) {}
          return { ok: true, message: "Lisensi aktif — lifetime (offline)." };
        });
      });
    },
    deactivate: function (p) {
      return apiOrLocal("/deactivate", p, function () {
        try { localStorage.removeItem(K_LIC); } catch (e) {}
        return { licensed: false, trialUsed: true, trialLeftMs: 0, expiresAt: null, offline: true };
      });
    },
    identify: function (p) { return Promise.resolve({ deviceId: deviceId(), hw: "", info: {}, offline: true }); },
    bind: function (p) { return apiOrLocal("/bind", p, function () { return { ok: true, offline: true }; }); },
    session: function (p) { return Promise.resolve({ valid: true }); },
    /* dipakai admin/CLI: kode utk deviceId sekarang */
    keygen: function (d) { return hex6(d || deviceId()); }
  };
  window.SimDriveLicense = SDL;

  /* Shim serverFn TanStack (simpan peta, checkout/premium) utk hosting statis:
     balas sukses generik supaya SPA tidak error saat tidak ada backend Python. */
  (function shimServerFn() {
    if (window.__sdServerFnShim) return;
    window.__sdServerFnShim = true;
    var of = window.fetch;
    window.fetch = function (input, init) {
      var url = typeof input === "string" ? input : (input && input.url) || "";
      var hit = url.indexOf("_serverFn") >= 0;
      var usesApi = url.indexOf("/api/license") >= 0;
      var p = of.apply(this, arguments);
      if (hit && !usesApi) {
        return p.then(function (r) {
          if (r.ok) return r;
          return new Response(JSON.stringify({ ok: true, success: true, data: {}, products: [], paid: true, orderId: "local", url: null }),
            { status: 200, headers: { "content-type": "application/json" } });
        }, function () {
          return new Response(JSON.stringify({ ok: true, success: true, data: {}, products: [], paid: true, orderId: "local", url: null }),
            { status: 200, headers: { "content-type": "application/json" } });
        });
      }
      return p;
    };
  })();
})();
