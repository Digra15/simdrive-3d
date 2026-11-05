#!/usr/bin/env python3
"""Rebrand: SimDrive -> SimDrive 3D, palette blue -> orange/red, own fonts."""
import os, re, sys

ROOT = '/root/simdrive-3d'
TEXT_EXT = {'.js', '.css', '.html', '.md', '.py', '.toml', '.json', '.txt', '.gitignore'}
TEXT_NAMES = {'_headers', '_redirects', '.gitignore'}

BIN = False

BRAND = [
    (b'SimDrive 3D V.2', b'SimDrive 3D V.2'),
    (b'SimDrive 3D', b'SimDrive 3D'),
    (b'SimDrive 3D', b'SimDrive 3D'),
    (b'SimDrive 3D', b'SimDrive 3D'),
    (b'C\xe1\xbb\xada h\xc3\xa0ngSimDrive 3D Store', b'C\xe1\xbb\xada h\xc3\xa0ng SimDrive 3D'),
    (b'SimDrive.vehicle', b'SimDrive.vehicle'),
    (b'SimDrive', b'SimDrive'),
    (b'SimDrive', b'SimDrive'),
    (b'SIMDRIVE', b'SIMDRIVE'),
    (b'SIMDRIVE', b'SIMDRIVE'),
    (b'simDrive', b'simDrive'),
    (b'simdrive', b'simdrive'),
    (b'simdrive', b'simdrive'),
    (b'Simdrive', b'Simdrive'),
    # arabic transliteration of the brand
    ('\u0628\u0627\u0646\u062c \u0628\u0627\u064a'.encode(), b'SimDrive'),
]

FONTS_HTML = [
    (b'family=Inter:wght@400;500;600;700;800&amp;family=Space+Grotesk:wght@500;600;700&amp;family=Saira+Condensed:ital,wght@1,800&amp;family=JetBrains+Mono:wght@400;600&amp;display=swap',
     b'family=Inter:wght@400;500;600;700;800&amp;family=Space+Grotesk:wght@500;600;700&amp;family=Saira+Condensed:ital,wght@1,800&amp;family=JetBrains+Mono:wght@400;600&amp;display=swap'),
    (b'family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&family=Saira+Condensed:ital,wght@1,800&family=JetBrains+Mono:wght@400;600&display=swap',
     b'family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&family=Saira+Condensed:ital,wght@1,800&family=JetBrains+Mono:wght@400;600&display=swap'),
]

FONTS_NAMES = [
    (b'Saira Condensed', b'Saira Condensed'),
    (b'Inter', b'Inter'),
    (b'JetBrains Mono', b'JetBrains Mono'),
    (b'Inter', b'Inter'),
    (b'Space Grotesk', b'Space Grotesk'),
]

COLORS = [
    (b'#ff4a17', b'#ff4a17'),
    (b'#ff4a17', b'#ff4a17'),
]

OKLCH = re.compile(rb'oklch\(\s*([0-9.]+%?)\s+([0-9.]+)\s+([0-9.]+)\s*(/[^)]*)?\)')


def shift_hue(data: bytes) -> bytes:
    out = []
    pos = 0
    for m in OKLCH.finditer(data):
        tail = data[max(0, m.start() - 40):m.start()]
        if b'--color-' in tail:
            continue
        try:
            h = float(m.group(3))
        except ValueError:
            continue
        if not (180.0 <= h <= 270.0):
            continue
        nh = 10.0 + (h - 180.0) * (50.0 / 90.0)
        out.append(data[pos:m.start()])
        out.append(b'oklch(' + m.group(1) + b' ' + m.group(2) + b' ' +
                   ('%g' % round(nh, 2)).encode() + (m.group(4) or b'') + b')')
        pos = m.end()
    out.append(data[pos:])
    return b''.join(out)


def is_text(p):
    b = os.path.basename(p)
    if b in TEXT_NAMES:
        return True
    return os.path.splitext(b)[1].lower() in TEXT_EXT


changed = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d != '.git']
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        if not is_text(p):
            continue
        raw = open(p, 'rb').read()
        new = raw
        for a, b in FONTS_HTML + BRAND + FONTS_NAMES + COLORS:
            if a in new:
                new = new.replace(a, b)
        if p.endswith('.css'):
            new = shift_hue(new)
        if new != raw:
            open(p, 'wb').write(new)
            changed.append(os.path.relpath(p, ROOT))

# rename chunks that carried the brand in their filename
for old, new in (('assets/SimDriveAuto-BaLgIatN.js', 'assets/SimDriveAuto-BaLgIatN.js'),
                 ('assets/SimDriveAuto-CXxU36GF.css', 'assets/SimDriveAuto-CXxU36GF.css'),
                 ('__l5e/assets-v1/bf7e02f6-4c6f-40d7-b68c-bdd3d13e0a39/simdrive-original-logo.png',
                  '__l5e/assets-v1/bf7e02f6-4c6f-40d7-b68c-bdd3d13e0a39/simdrive-logo.png'),
                 ('__l5e/assets-v1/0eaa18ff-607f-464b-8180-cae12f682f4a/simdrive-rigging-logo.png',
                  '__l5e/assets-v1/0eaa18ff-607f-464b-8180-cae12f682f4a/simdrive-rigging-logo.png')):
    o, n = os.path.join(ROOT, old), os.path.join(ROOT, new)
    if os.path.exists(o):
        os.rename(o, n)
        changed.append(f'RENAME {old} -> {new}')

print(f'{len(changed)} files changed')
for c in changed:
    print(' ', c)
