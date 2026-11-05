#!/usr/bin/env python3
"""Stage 2: strip foreign/Lovable traces, own og image, self-hosted mesh link."""
import os, re, sys

ROOT = '/root/simdrive-3d'
report = []


def sub_file(rel, pairs, binary=False, regex=False, required=True):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        report.append(f'SKIP (missing) {rel}')
        return
    mode = 'rb' if binary or True else 'r'
    data = open(p, 'rb').read()
    orig = data
    for i, (a, b) in enumerate(pairs):
        A = a if isinstance(a, bytes) else a.encode()
        B = b if isinstance(b, bytes) else b.encode()
        n = len(re.findall(A, data)) if regex else data.count(A)
        if n == 0:
            report.append(f'  ! no-match #{i} in {rel}: {A[:70]!r}')
            continue
        data = re.sub(A, B, data) if regex else data.replace(A, B)
        report.append(f'  ok x{n} {rel}: {A[:60]!r}')
    if data != orig:
        open(p, 'wb').write(data)


# ---- A. telemetry script tag (index.html + 404.html), og image host
telem = re.compile(rb'<script defer src="/__l5e/events\.[0-9a-f]+\.js"[^>]*></script>')
r2 = re.compile(rb'https://pub-bb2e103a32db4e198524a2e9ed8f35b4\.r2\.dev/[^\s"\']+')
for hf in ('index.html', '404.html'):
    p = os.path.join(ROOT, hf)
    d = open(p, 'rb').read()
    d2, n = telem.subn(b'', d)
    d3, n2 = r2.subn(b'/og-simdrive.png', d2)
    if d3 != d:
        open(p, 'wb').write(d3)
    report.append(f'  {hf}: telem removed={n} og-image replaced={n2}')

# ---- B. delete telemetry sdk
ev = os.path.join(ROOT, '__l5e/events.270c78a44fc53e7b.js')
if os.path.exists(ev):
    os.remove(ev)
    report.append('  removed __l5e/events.270c78a44fc53e7b.js')

# ---- C. own domain placeholders in bundles
sub_file('assets/License-CDekcKcc.js',
         [(b'https://simdrivesimulator.lovable.app/aset-premium#katalog', b'/aset-premium#katalog')])
sub_file('assets/admin-D0d9Tnuk.js',
         [(b'https://simdrivesimulator.lovable.app/', b'/', )])
sub_file('assets/routes-C6wagoiJ.js',
         [(b'https://banpaymesh.lovable.app', b'/mesh')])

# ---- D. Lovable editor bridge -> own host
sub_file('assets/index-BNKMB666.js', [
    (b'[`lovableproject.com`,`lovableproject-dev.com`,`lovable.app`,`gpt-eng.com`,`gptengineer.run`]',
     b'[`simdrive3d.local`]'),
    (b'(lovable\\.dev|gptengineer\\.app)', b'(simdrive3d\\.local)'),
    (b'[`https://lovable.dev`,`http://localhost:3000`]', b'[`http://localhost:3000`]'),
    (b'[`https://lovable.dev`]', b'[`http://localhost:3000`]'),
])

# ---- E. permalink/meta text
sub_file('assets/index-BNKMB666.js', [
    (b'simdrivesimulator', b'simdrive3d'),
])

# ---- F. serve.py: drop dead telemetry endpoint
sub_file('serve.py', [(b'\n        if parsed.path == "/__l5e/trackevents":\n'
                       b'            self.send_response(200)\n'
                       b'            self.send_header("Content-Type", "application/json")\n'
                       b'            self.end_headers()\n'
                       b'            self.wfile.write(b"{}")\n'
                       b'            return\n', b'')])

print('\n'.join(report))
