#!/usr/bin/env python3
"""Inventory an R package's pkgdown setup before migrating to litedown.

Usage: python3 audit_pkgdown.py [PKG_ROOT]

Prints what exists and a checklist of ACTION (must do) / DECIDE (ask the user)
items. Read-only: it never modifies the package.
"""
import glob
import os
import re
import sys

root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
actions, decisions = [], []


def p(*parts):
    return os.path.join(root, *parts)


def read(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return None


def dcf_field(text, field):
    m = re.search(r'^%s:\s*(.*(?:\n[ \t]+.*)*)' % re.escape(field), text or '', re.M)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else None


def section(title):
    print('\n## ' + title)


desc = read(p('DESCRIPTION'))
if desc is None:
    sys.exit('No DESCRIPTION in %s; pass the package root.' % root)
pkg = dcf_field(desc, 'Package')
print('# pkgdown audit: %s (%s)' % (pkg, root))

# --- DESCRIPTION -----------------------------------------------------------
section('DESCRIPTION')
url = dcf_field(desc, 'URL')
vb = dcf_field(desc, 'VignetteBuilder')
print('URL:', url)
print('VignetteBuilder:', vb)
if not url:
    actions.append('Add the site URL to DESCRIPTION URL:')

# --- _pkgdown.yml ----------------------------------------------------------
section('_pkgdown.yml')
cfg_path = next((x for x in [p('_pkgdown.yml'), p('_pkgdown.yaml'), p('pkgdown', '_pkgdown.yml')]
                 if os.path.exists(x)), None)
cfg = None
if not cfg_path:
    print('not found (maybe pkgdown uses defaults)')
else:
    raw = read(cfg_path)
    print('file:', os.path.relpath(cfg_path, root))
    try:
        import yaml
        cfg = yaml.safe_load(raw) or {}
    except Exception as e:  # PyYAML missing or invalid YAML
        print('(could not parse YAML: %s) raw contents follow:\n%s' % (e, raw))
    if isinstance(cfg, dict):
        print('top-level keys:', ', '.join(cfg.keys()) or '(none)')
        if cfg.get('url'):
            print('url:', cfg['url'])
            host = re.sub(r'^https?://([^/]+).*$', r'\1', str(cfg['url']))
            if not host.endswith('github.io'):
                actions.append('Custom domain %s: create site/CNAME containing "%s" (the gh-pages '
                               'deploy replaces everything, including the old CNAME)' % (host, host))
        ref = cfg.get('reference')
        if ref:
            titles = [s.get('title') for s in ref if isinstance(s, dict) and s.get('title')]
            print('reference sections (%d):' % len(titles), '; '.join(map(str, titles)))
            decisions.append('Reference has %d grouped sections; pkg_manual() is one flat page. '
                             'Accept, or write site/manual.Rmd with a grouped link index '
                             '(references/mapping.md).' % len(titles))
        if cfg.get('articles'):
            decisions.append('_pkgdown.yml groups articles; articles.html is a flat list. '
                             'Accept or write site/articles.Rmd.')
        if cfg.get('navbar'):
            decisions.append('Custom navbar configured; litedown auto-generates nav from pages. '
                             'Reproduce via include_before only if it matters.')
        tmpl = cfg.get('template') or {}
        if isinstance(tmpl, dict) and (tmpl.get('bslib') or tmpl.get('bootswatch') or tmpl.get('theme')):
            decisions.append('Bootstrap/bslib theming is used; litedown has no themes. '
                             'Offer a small css2 stylesheet or accept the default look.')
        if cfg.get('home'):
            print('home:', cfg['home'])
        if cfg.get('development'):
            print('development:', cfg['development'])
    actions.append('Delete %s (keep its content in mind for the migration)'
                   % os.path.relpath(cfg_path, root))

if os.path.isdir(p('pkgdown')):
    files = [os.path.relpath(f, root) for f in glob.glob(p('pkgdown', '**', '*'), recursive=True)
             if os.path.isfile(f)]
    print('pkgdown/ assets:', ', '.join(files) or '(empty)')
    actions.append('Move useful pkgdown/ assets (extra.css etc.) to site/ and delete pkgdown/')
    if any(os.path.basename(f) in ('index.md', 'index.Rmd') for f in files):
        decisions.append('pkgdown/index.md overrides the README home page; merge into README '
                         'or write site/index.Rmd')

# --- output dir ------------------------------------------------------------
section('Output folder')
docs = p('docs')
if os.path.isdir(docs):
    is_pkgdown = os.path.exists(p('docs', 'pkgdown.yml')) or os.path.isdir(p('docs', 'reference'))
    is_book = os.path.exists(p('docs', '_litedown.yml'))
    print('docs/ exists; pkgdown output: %s; litedown book: %s' % (is_pkgdown, is_book))
    if is_pkgdown:
        actions.append('Remove committed pkgdown output docs/ (the action treats docs/_litedown.yml '
                       'as a book; stale output only confuses things)')
else:
    print('no docs/')

# --- README ----------------------------------------------------------------
section('README')
readme = read(p('README.md'))
if os.path.exists(p('README.Rmd')):
    print('README.Rmd present (not knitted in CI; README.md must be committed and current)')
if readme is None:
    actions.append('No README.md: the home page will show only metadata. Create README.md')
else:
    has_badges = '<!-- badges: start -->' in readme
    print('README.md: %d lines; badge markers: %s' % (readme.count('\n'), has_badges))
    if not has_badges:
        decisions.append('README.md has no <!-- badges: start --> marker, so the whole README '
                         '(including any title/intro above the badges) appears on the home page')
if os.path.exists(p('index.md')) or os.path.exists(p('index.Rmd')):
    decisions.append('Root index.md/Rmd (pkgdown home override) exists; merge into README or '
                     'site/index.Rmd')
if os.path.exists(p('man', 'figures', 'logo.png')) or glob.glob(p('man', 'figures', 'logo.*')):
    print('logo found in man/figures (pkgdown shows it automatically; litedown does not)')
    decisions.append('Logo: reference it from README.md (man/figures is copied to the site)')

# --- man pages -------------------------------------------------------------
section('Rd pages')
rds = sorted(glob.glob(p('man', '*.Rd')))
print('%d Rd files' % len(rds))
slow = [os.path.basename(f) for f in rds if re.search(r'\\dontrun|\\donttest', read(f) or '')]
if slow:
    print('with \\dontrun/\\donttest:', len(slow))

# --- vignettes -------------------------------------------------------------
section('Vignettes')
vigs = sorted(glob.glob(p('vignettes', '*.Rmd')) + glob.glob(p('vignettes', '*.md'))
              + glob.glob(p('vignettes', '*.qmd')) + glob.glob(p('vignettes', '*.Rnw')))
for v in vigs:
    t = read(v) or ''
    eng = re.search(r'%\\VignetteEngine\{([^}]*)\}', t)
    out = re.search(r'^output:\s*(.*)$', t, re.M)
    print('- %s  engine=%s  output=%s' % (os.path.relpath(v, root),
                                          eng.group(1) if eng else 'NONE',
                                          out.group(1).strip() if out else '-'))
    if not eng:
        decisions.append('%s has no VignetteEngine; it is pkgdown-only and will not be listed'
                         % os.path.relpath(v, root))
if any(v.endswith('.qmd') for v in vigs):
    actions.append('Quarto vignettes: add `- uses: quarto-dev/quarto-actions/setup@v2` before '
                   'setup-r-dependencies in the site workflow')
arts = sorted(glob.glob(p('vignettes', 'articles', '*.*md')))
if arts:
    print('pkgdown-only articles (vignettes/articles):', ', '.join(os.path.basename(a) for a in arts))
    decisions.append('%d pkgdown-only article(s) in vignettes/articles/ will NOT appear. Move to '
                     'site/<name>.Rmd, examples/, or make them vignettes' % len(arts))
if not vigs and not arts:
    print('none')

# --- news, examples, playground -------------------------------------------
section('Other site sources')
for f in ['NEWS.md', 'inst/NEWS.Rd', 'inst/CITATION']:
    print('%-14s %s' % (f, 'yes' if os.path.exists(p(f)) else 'no'))
for d in ['site', 'examples', 'playground']:
    print('%-14s %s' % (d + '/', 'yes' if os.path.isdir(p(d)) else 'no'))
if os.path.exists(p('src')):
    print('src/ present: compiled code; check that a WASM build exists before offering the playground')
decisions.append('Add a webR playground? (playground/setup.R + _default.Rmd; needs a WASM '
                 'build, e.g. via r-universe)')

# --- workflows -------------------------------------------------------------
section('GitHub workflows')
for w in sorted(glob.glob(p('.github', 'workflows', '*.y*ml'))):
    t = read(w) or ''
    tags = [k for k in ['pkgdown', 'litedown', 'gh-pages', 'JamesIves'] if k in t]
    print('- %s %s' % (os.path.relpath(w, root), tags))
    if 'pkgdown' in t:
        actions.append('Replace/delete %s with assets/github-pages.yml' % os.path.relpath(w, root))
if not glob.glob(p('.github', 'workflows', '*.y*ml')):
    print('none')
actions.append('Check GitHub Settings -> Pages: deploy from branch gh-pages / (root)')

# --- .Rbuildignore ---------------------------------------------------------
section('.Rbuildignore')
rbi = (read(p('.Rbuildignore')) or '').splitlines()
print('\n'.join(rbi) or '(empty)')
stale = [l for l in rbi if re.search(r'pkgdown|\^docs\$', l)]
if stale:
    actions.append('.Rbuildignore: remove %s' % ', '.join(stale))
for d in ['site', 'examples', 'playground']:
    pat = '^%s$' % d
    if pat not in rbi:
        actions.append('.Rbuildignore: add %s if you create %s/' % (pat, d))

# --- summary ---------------------------------------------------------------
print('\n## ACTION')
for a in actions:
    print('- [ ] ' + a)
print('\n## DECIDE (ask the user)')
for d in decisions:
    print('- ' + d)
