#!/usr/bin/env python3
"""Write redirect stubs so old pkgdown URLs keep working on the litedown site.

Usage: python3 make_redirects.py [PKG_ROOT] [--site-dir site] [--index] [--dry-run]

Creates, under <site-dir>/ (static .html files are left untouched by fuse_site()):
  reference/<Rd file>.html  ->  ../manual.html#sec:man-<\\name>
  articles/<vignette>.html  ->  ../doc/<vignette>.html
With --index, also reference/index.html -> ../manual.html and
articles/index.html -> ../articles.html. Off by default: a subfolder with an
index.html gets its own entry in litedown's auto-generated nav bar.
"""
import argparse
import glob
import html
import os
import re

ap = argparse.ArgumentParser()
ap.add_argument('root', nargs='?', default='.')
ap.add_argument('--site-dir', default='site')
ap.add_argument('--index', action='store_true')
ap.add_argument('--dry-run', action='store_true')
args = ap.parse_args()

root = os.path.abspath(args.root)
site = os.path.join(root, args.site_dir)

STUB = '''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Moved</title>
<link rel="canonical" href="{t}">
<meta http-equiv="refresh" content="0; url={t}">
</head><body><p>This page has moved to <a href="{t}">{t}</a>.</p>
<script>location.replace({js});</script>
</body></html>
'''


def write(rel, target):
    path = os.path.join(site, rel)
    print('%s -> %s' % (os.path.join(args.site_dir, rel), target))
    if args.dry_run:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    js = '"%s"' % target
    with open(path, 'w', encoding='utf-8') as f:
        f.write(STUB.format(t=html.escape(target, quote=True), js=js))


n = 0
for rd in sorted(glob.glob(os.path.join(root, 'man', '*.Rd'))):
    with open(rd, encoding='utf-8', errors='replace') as f:
        text = f.read()
    m = re.search(r'\\name\{([^}]*)\}', text)
    if not m:
        continue
    # pkgdown names topic pages after the Rd file; litedown anchors on \name
    base = os.path.splitext(os.path.basename(rd))[0]
    write('reference/%s.html' % base, '../manual.html#sec:man-%s' % m.group(1).strip())
    n += 1

vigs = []
for ext in ('Rmd', 'md', 'Rnw', 'qmd'):
    vigs += glob.glob(os.path.join(root, 'vignettes', '*.' + ext))
for v in sorted(vigs):
    with open(v, encoding='utf-8', errors='replace') as f:
        if '\\VignetteEngine' not in f.read():
            continue  # pkgdown-only; no doc/ output to point to
    base = os.path.splitext(os.path.basename(v))[0]
    ext = 'pdf' if v.endswith('.Rnw') else 'html'
    write('articles/%s.html' % base, '../doc/%s.%s' % (base, ext))
    n += 1

if args.index:
    write('reference/index.html', '../manual.html')
    write('articles/index.html', '../articles.html')
    n += 2

print('%d stub(s) %s' % (n, 'would be written' if args.dry_run else 'written'))
