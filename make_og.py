#!/usr/bin/env python3
"""Owner-branded OpenGraph card for SimDrive 3D."""
from PIL import Image, ImageDraw, ImageFont
from make_brand import badge, gradient, fit, INK, INK2, ORANGE, AMBER, FB

W, H = 1200, 630
im = Image.new('RGB', (W, H), INK)
im.paste(gradient(W, H, INK, (48, 20, 10), diag=True), (0, 0))
d = ImageDraw.Draw(im)

# accent bar + glow
d.rectangle([0, 0, W, 8], fill=ORANGE)
d.rectangle([0, H - 8, W, H], fill=AMBER)

b = badge(150)
im.paste(b, (80, 92), b)

f1, l1, t1, r1, b1 = fit(d, 'SimDrive 3D', FB, 900, 90, start=140)
d.text((80, 275), 'SimDrive 3D', font=f1, fill=(255, 255, 255))

f2, l2, t2, r2, b2 = fit(d, 'Simulator Kendaraan & Editor Peta 3D', FB, 1000, 46, start=80)
d.text((82, 385), 'Simulator Kendaraan & Editor Peta 3D', font=f2, fill=(255, 190, 120))

f3, l3, t3, r3, b3 = fit(d, 'TRUK  ·  TRAKTOR  ·  PESAWAT  ·  PETA 3D', FB, 900, 26, start=44)
d.text((82, 470), 'TRUK  ·  TRAKTOR  ·  PESAWAT  ·  PETA 3D', font=f3, fill=(160, 150, 145))

im.save('/root/simdrive-3d/og-simdrive.png')
print('og-simdrive.png', im.size)