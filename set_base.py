#!/usr/bin/env python3
"""Rewrite absolute asset paths for subpath hosting + inject client-side
license mock. Usage: python3 set_base.py [--base /simdrive-3d]  (default: /simdrive-3d)
Run on a CLEAN checkout. To revert for root hosting: --base '' on the rewritten tree
(WARN: not idempotent per-file; rerun from clean clone instead)."""
import os, re, sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "/simdrive-3d"
ROOT = os.path.dirname(os.path.abspath(__file__))
PREF = "`" + BASE

def patch_js(path):
    s = open(path, encoding="utf-8").read()
    orig = s
    s = s.replace('`/assets/', PREF + '/assets/')
    s = s.replace('"/assets/', '"' + BASE + '/assets/')
    s = s.replace('`/__l5e/', PREF + '/__l5e/')
    s = s.replace('"/__l5e/', '"' + BASE + '/__l5e/')
    if s != orig:
        open(path, "w", encoding="utf-8").write(s)
        return True
    return False

def patch_html(path):
    s = open(path, encoding="utf-8").read()
    orig = s
    s = s.replace('"/__l5e/', '"' + BASE + '/__l5e/')
    s = s.replace('"/assets/', '"' + BASE + '/assets/')
    s = s.replace('"/apple-touch-icon.png"', '"' + BASE + '/apple-touch-icon.png"')
    if '<script src="' and "mock-license.js" not in s:
        s = s.replace('<meta charset="utf-8"/>',
                      '<meta charset="utf-8"/><script src="' + BASE + '/mock-license.js"></script>', 1)
        if "mock-license.js" not in s:  # fallback: inject after <head>
            s = s.replace("<head>", '<head><script src="' + BASE + '/mock-license.js"></script>', 1)
    if s != orig:
        open(path, "w", encoding="utf-8").write(s)
        return True
    return False

n = 0
for base_dir, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
    for f in files:
        p = os.path.join(base_dir, f)
        if f.endswith((".js", ".mjs")):
            n += patch_js(p)
        elif f.endswith(".html"):
            n += patch_html(p)
print(f"patched {n} files (base={BASE})")
