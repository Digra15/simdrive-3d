/* Client-side mock for TanStack Start serverFns (/ _serverFn/<hash>).
   Replaces serve.py's Python mock so the SPA works on pure static hosting
   (GitHub Pages / Netlify static / Cloudflare Pages static).
   Mirrors serve.py behaviour 1:1: trial valid 120s, any 6-digit code activates. */
(function () {
  "use strict";
  var TRIAL = JSON.stringify({
    t: { i: 6, s: "{}", c: 2, e: 1, a: "", f: 1, b: 0, o: 0 },
    f: 127,
    m: []
  });
  var ACTIVATE_OK = JSON.stringify({ ok: true, message: "Lisensi berhasil diaktifkan" });
  var ACTIVATE_BAD = JSON.stringify({ ok: false, message: "Kode lisensi tidak valid" });

  var MAP = {
    "7a469d2260b69be33667b773b6cf0b17f5b3172b09e9e53d31b7c179d228239f": TRIAL, // check
    "5f9688103a94c2b709cbdbc756d787f674ee2878a65f2f3430016c0786ed1639": TRIAL, // verify
    "ddd70843e0985a45c37b01bfe84b1f703ef93bfffdcaccc52a4545ff9fe3d012": "ACTIVATE",
    "f6c2d91ec64a2386829008c4e4dbb5535db43181e96f0f0508554643530294c4": TRIAL, // deactivate
    "512c1ed33d8f9f2d8c0e27abffde2948fcecbc1c65e3a63765e465504995672e": "{}",    // device_identify
    "94066eae80d63dbc8098ba48c5ff92c2db6c6556d13b73057a4cc8197674a626": "{}",    // device_bind
    "3165138a4c311591f80a31d2569667280f9204b28349b37af60ab0c83cac680d": JSON.stringify({ valid: true })
  };

  function json(body) {
    return new Response(body, {
      status: 200,
      headers: { "content-type": "application/json", "x-tss-raw": "true" }
    });
  }

  function urlOf(input) {
    if (typeof input === "string") return input;
    if (input && input.url) return input.url;
    return String(input);
  }

  function bodyText(init, input) {
    try {
      if (init && typeof init.body === "string") return init.body;
      if (input && typeof input.text === "function") return input.text();
    } catch (e) {}
    return Promise.resolve("");
  }

  var orig = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function (input, init) {
    var url = urlOf(input) || "";
    var path = url.replace(/^https?:\/\/[^/]+/, "").split("?")[0];

    if (path.indexOf("/_serverFn/") === 0 || url.indexOf("/_serverFn/") !== -1) {
      var id = path.slice(path.lastIndexOf("/_serverFn/") + 11);
      var hit = MAP[id];
      if (hit === undefined) return Promise.resolve(json("{}"));
      if (hit !== "ACTIVATE") return Promise.resolve(json(hit));
      return Promise.resolve(bodyText(init, input)).then(function (raw) {
        var code = "";
        try {
          var obj = JSON.parse(raw || "{}");
          var data = obj && obj.data;
          if (data && typeof data === "object") code = String(data.code || "").trim();
          else if (typeof data === "string") code = data.trim();
        } catch (e) {}
        if (/^\d{6}$/.test(code)) return json(ACTIVATE_OK);
        return json(ACTIVATE_BAD);
      });
    }

    if (path === "/simdrive-3d/__l5e/trackevents" || path.slice(-15) === "/trackevents") {
      return Promise.resolve(json("{}"));
    }

    return orig ? orig(input, init) : Promise.reject(new Error("no fetch"));
  };
})();
