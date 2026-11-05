# SimDrive 3D (mirror / clone)

Static mirror of `simdrive3d.local` — Vite + React + TanStack Router
SPA dengan Three.js / react-three-fiber + Rapier physics, ~114 MB asset.

## Isi
- `index.html` — SPA shell (analytics dihapus)
- `assets/` — 121 JS/CSS bundle chunk (semua dynamic import chunk disertakan)
- `__l5e/assets-v1/` — 57 model GLB, 31 texture WebP, 15 audio MP3, video WebM, poster
- `_redirects`, `404.html`, `netlify.toml`, `_headers` — konfigurasi SPA fallback

## Jalankan lokal
`serve.py` = static server + **mock license RPC** (stdlib, tanpa dependency).
```bash
python3 serve.py          # -> http://127.0.0.1:8099/
PORT=9000 REPO_DIR=. python3 serve.py
```
Mock menjawab 7 endpoint TanStack Start `POST /_serverFn/<hash>` dengan trial valid
(`licensed:false, trialLeftMs:120000`) dan kode aktivasi 6 digit apa pun -> sukses.

## Yang TIDAK jalan (backend dimatikan)
- License / activation (server RPC TanStack Start -> hilang)
  - `license.functions`: check, verify, activate, deactivate, device bind, session validate
  - (di-deploy statis, ini dijawab oleh `serve.py`; di hosting statis murni akan gagal cek lisensi)
- Supabase project `zigiqhsversmbhcywewo.supabase.co` (auth + data)
- AI vision (`ai-vision-C3wi5Vem.js`) — butuh API key
- HuggingFace spaces browser (`browser-CaiyJVWW.js`)

Semua fitur 3D/simulator berjalan offline karena model & texture sudah di-mirror lokal.

## Deploy

### Cloudflare Pages (rekomendasi)
Gratis, bandwidth unlimited, file limit 25 MB (terbesar di sini 6.3 MB).
```
npx wrangler pages deploy . --project-name simdrive-simulator
```

### Netlify
```
npx netlify-cli deploy --prod --dir .
```

### GitHub Pages
Repo < 1 GB (di sini 114 MB). Push lalu aktifkan Pages dari root branch.
`404.html` dipakai untuk SPA fallback.
