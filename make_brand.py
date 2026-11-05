#!/usr/bin/env python3
"""Generate SimDrive 3D brand marks (own palette: orange/red + amber)."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = '/root/simdrive-3d'
ORANGE = (255, 74, 23)
AMBER = (255, 179, 0)
INK = (20, 10, 6)
INK2 = (34, 16, 9)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(w, h, c1, c2, diag=True):
    im = Image.new('RGB', (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            t = ((x / w) + (y / h)) / 2 if diag else x / w
            px[x, y] = lerp(c1, c2, min(1.0, max(0.0, t)))
    return im


def fit(draw, text, font_path, box_w, box_h, start=200):
    for s in range(start, 8, -2):
        f = ImageFont.truetype(font_path, s)
        l, t, r, b = draw.textbbox((0, 0), text, font=f)
        if (r - l) <= box_w and (b - t) <= box_h:
            return f, l, t, r, b
    f = ImageFont.truetype(font_path, 12)
    l, t, r, b = draw.textbbox((0, 0), text, font=f)
    return f, l, t, r, b


def badge(size, radius_frac=0.22, with_ring=True):
    """rounded-square gradient badge with white SD monogram + speed chevrons."""
    S = size
    bg = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1],
                                          radius=int(S * radius_frac), fill=255)
    grad = gradient(S, S, ORANGE, AMBER).convert('RGBA')
    bg.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(bg)

    # speed chevrons (left edge)
    cw = int(S * 0.055)
    for i in range(3):
        x = int(S * (0.10 + i * 0.075))
        d.line([(x, int(S * 0.16)), (x + cw, int(S * 0.5)), (x, int(S * 0.84))],
               fill=(255, 255, 255, 40 + i * 45), width=max(2, int(S * 0.012)),
               joint='curve')

    f, l, t, r, b = fit(d, 'SD', FB, int(S * 0.60), int(S * 0.52), start=int(S))
    d.text((S / 2 - (l + r) / 2, S / 2 - (t + b) / 2 - int(S * 0.03)),
           'SD', font=f, fill=(255, 255, 255, 255))

    if with_ring:
        d.rounded_rectangle([int(S * 0.035), int(S * 0.035), S - int(S * 0.035), S - int(S * 0.035)],
                            radius=int(S * (radius_frac - 0.02)),
                            outline=(255, 255, 255, 90), width=max(2, int(S * 0.008)))
    return bg


def hero(w, h, title, sub, path, transparent=False):
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0) if transparent else INK + (255,))
    if not transparent:
        g = gradient(w, h, INK, INK2).convert('RGBA')
        base.paste(g, (0, 0))
    bsize = int(h * 0.62)
    b = badge(bsize)
    base.paste(b, (int(w * 0.07), (h - bsize) // 2), b)
    d = ImageDraw.Draw(base)
    tx0 = int(w * 0.07) + bsize + int(w * 0.045)
    f1, l1, t1, r1, b1 = fit(d, title, FB, int(w - tx0 - w * 0.05), int(h * 0.34), start=int(h * 0.5))
    d.text((tx0, h * 0.30 - (b1 - t1) / 2 - t1), title, font=f1, fill=(255, 255, 255))
    f2, l2, t2, r2, b2 = fit(d, sub, FB, int(w - tx0 - w * 0.05), int(h * 0.13), start=int(h * 0.24))
    d.text((tx0, h * 0.66 - (b2 - t2) / 2 - t2), sub, font=f2, fill=AMBER)
    base.save(path)
    print('wrote', path, base.size)


def mark(path, size, transparent=False, glyph='SD'):
    im = badge(size, with_ring=True)
    if not transparent:
        flat = Image.new('RGB', (size, size), INK)
        flat.paste(im, (0, 0), im)
        im = flat
    im.save(path)
    print('wrote', path, im.size, im.mode)


hero(1254, 1254, 'SimDrive 3D', 'SIMULATOR  KENDARAAN  &  EDITOR  PETA',
     f'{ROOT}/__l5e/assets-v1/bf7e02f6-4c6f-40d7-b68c-bdd3d13e0a39/simdrive-logo.png')
hero(816, 816, 'SimDrive Rigging', 'FORGE  3D  ·  ASET  &  RIG',
     f'{ROOT}/__l5e/assets-v1/0eaa18ff-607f-464b-8180-cae12f682f4a/simdrive-rigging-logo.png',
     transparent=True)
mark(f'{ROOT}/favicon.png', 64)
mark(f'{ROOT}/apple-touch-icon.png', 180)
