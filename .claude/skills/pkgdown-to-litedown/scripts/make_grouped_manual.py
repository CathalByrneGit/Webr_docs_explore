#!/usr/bin/env python3
"""Generate site/manual.Rmd: a grouped link index (from _pkgdown.yml `reference:`) above
the full litedown manual.

Usage: python3 make_grouped_manual.py [PKG_ROOT] [--site-dir site] [--dry-run]

Run it BEFORE deleting _pkgdown.yml. Anchors are `#sec:man-<Rd \\name>`, so topics that are
only an \\alias are mapped to their Rd \\name. Selectors starts_with()/ends_with()/contains()/
matches() are expanded against man/*.Rd; `-topic` excludes; internal/other selectors are
reported and skipped. Rd pages the config never mentions are added to a final "Other" group so
nothing disappears from the index (they are in the manual either way).
"""
import argparse
import glob
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit('PyYAML is required: pip install pyyaml')

ap = argparse.ArgumentParser()
ap.add_argument('root', nargs='?', default='.')
ap.add_argument('--site-dir', default='site')
ap.add_argument('--dry-run', action='store_true')
args = ap.parse_args()
root = os.path.abspath(args.root)

cfg_path = next((x for x in [os.path.join(root, '_pkgdown.yml'), os.path.join(root, '_pkgdown.yaml'),
                             os.path.join(root, 'pkgdown', '_pkgdown.yml')] if os.path.exists(x)), None)
if not cfg_path:
    sys.exit('No _pkgdown.yml found (already deleted?). Nothing to group.')
ref = (yaml.safe_load(open(cfg_path, encoding='utf-8')) or {}).get('reference')
if not ref:
    sys.exit('_pkgdown.yml has no `reference:` sections; the default flat manual is fine.')

names, alias_to_name, internal = [], {}, set()
for f in sorted(glob.glob(os.path.join(root, 'man', '*.Rd'))):
    t = open(f, encoding='utf-8', errors='replace').read()
    m = re.search(r'\\name\{([^}]*)\}', t)
    if not m:
        continue
    n = m.group(1)
    names.append(n)
    for a in re.findall(r'\\alias\{([^}]*)\}', t):
        alias_to_name[a] = n
    if re.search(r'\\keyword\{internal\}', t):
        internal.add(n)
visible = [n for n in names if n not in internal]


def expand(item):
    """Return a list of Rd names for one `contents:` entry, or None if unsupported."""
    m = re.fullmatch(r'(starts_with|ends_with|contains|matches)\(["\'](.*)["\']\)', item)
    if m:
        kind, arg = m.groups()
        test = {'starts_with': lambda n: n.startswith(arg), 'ends_with': lambda n: n.endswith(arg),
                'contains': lambda n: arg in n, 'matches': lambda n: re.search(arg, n)}[kind]
        return [n for n in visible if test(n)]
    if re.fullmatch(r'[\w.]+', item):
        n = alias_to_name.get(item, item if item in names else None)
        return [n] if n else []
    return None


warnings, used = [], set()
lines = ['---', 'title: Help pages', '---', '', '```{css, echo = FALSE}', 'h2 {',
         '  text-align: center;', '  margin-top: 2em;', '}', '```', '', '## Reference index {-}', '']
for sec in ref:
    if not isinstance(sec, dict) or not sec.get('contents'):
        continue
    picked = []
    for item in sec['contents']:
        item = str(item)
        neg = item.startswith('-')
        got = expand(item[1:] if neg else item)
        if got is None:
            warnings.append('%s: unsupported selector %r skipped' % (sec.get('title', '?'), item))
        elif neg:
            picked = [n for n in picked if n not in got]
        elif not got:
            warnings.append('%s: %r matches no Rd page (missing man/? run roxygen2::roxygenise())'
                            % (sec.get('title', '?'), item))
        else:
            picked += [n for n in got if n not in picked]
    used.update(picked)
    if picked:
        head = '**%s**' % sec.get('title', sec.get('subtitle', 'Topics'))
        if sec.get('desc'):
            head += ' — ' + re.sub(r'\s+', ' ', str(sec['desc'])).strip()
        lines.append(head + '  ')
        lines.append(', '.join('[%s()](#sec:man-%s)' % (n, n) for n in picked) + '\n')

rest = [n for n in visible if n not in used]
if rest:
    warnings.append('Rd pages not mentioned in _pkgdown.yml (added under "Other"): ' + ', '.join(rest))
    lines.append('**Other**  ')
    lines.append(', '.join('[%s()](#sec:man-%s)' % (n, n) for n in rest) + '\n')
lines += ['## Full manual {-}', '', '`{r} litedown::pkg_manual()`', '']

out = os.path.join(root, args.site_dir, 'manual.Rmd')
if args.dry_run:
    print('\n'.join(lines))
else:
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write('\n'.join(lines))
    print('wrote', os.path.relpath(out, root))
for w in warnings:
    print('WARNING:', w, file=sys.stderr)
