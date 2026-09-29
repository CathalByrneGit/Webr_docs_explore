---
name: pkgdown-to-litedown
description: Migrate an R package's documentation website from pkgdown to litedown (Yihui Xie's lightweight R Markdown) using the yihui/actions/litedown-site GitHub Action, optionally adding an in-browser webR playground. Use this whenever the user wants to replace, drop, or move away from pkgdown, convert _pkgdown.yml, build a package site "like pkg.yihui.org", set up litedown::fuse_site() for a package, add a webR/litedown playground to package docs, or asks for a lighter/no-pandoc/no-bootstrap package website — even if they only say "switch my package site to litedown" or paste a repo that contains _pkgdown.yml.
---

# pkgdown → litedown package site

Convert an R package that currently builds its site with **pkgdown** into one built by
**litedown** through the reusable action `yihui/actions/litedown-site`. This is the same
setup behind `https://pkg.yihui.org/litedown/` and `https://pkg.yihui.org/lt/`.

The site ends up small and mostly driven by conventions. The action supplies template
pages, which are only used when the package doesn't provide its own:

| page | built from |
|---|---|
| `index.html` | `pkg_desc()` metadata table + `README.md` (from `<!-- badges: start -->` onward) + `pkg_citation()` |
| `manual.html` | `pkg_manual()`: every Rd page on one page, anchors `#sec:man-<name>` |
| `articles.html` | links to vignettes built by `R CMD build` (copied from the installed `doc/`) |
| `news.html` | `pkg_news()` from `NEWS.md` / `inst/NEWS.Rd` |
| `examples.html` + `examples/*.html` | every `.Rmd`/`.R` in the package-root `examples/` folder |
| `playground/` | a webR editor that runs `litedown::fuse()` in the browser |

Pages are dropped automatically when they don't apply (no `vignettes/` → no articles
page, and so on). `code.Rmd` is excluded by default. Nav links are generated from the
top-level pages plus any subfolder that has an `index.html`.

Most of the migration is about deciding what to do with the pkgdown features this model
doesn't have (grouped reference index, per-topic pages, search, Bootstrap themes, navbar
menus, `vignettes/articles/`). Be upfront with the user about those, don't silently drop
them. `references/mapping.md` has the full feature-by-feature table.

## Workflow

### 1. Audit the package

Run the audit script from the package root. It needs only Python; PyYAML is optional.

```bash
python3 <skill-dir>/scripts/audit_pkgdown.py /path/to/pkg
```

It reports:
- what `_pkgdown.yml` uses
- vignette engines and pkgdown-only `vignettes/articles/`
- the state of README/badges
- any `docs/` output folder
- pkgdown workflows
- `.Rbuildignore` entries to change
- a list of items flagged **ACTION** / **DECIDE**

Read the output before changing anything; it drives the remaining steps. If you can't
run Python, do the same checks by hand (the script is short and readable).

### 2. Discuss the trade-offs, then decide

Show the user the **DECIDE** items and get answers before making destructive changes.
These are the usual ones:
- **Reference grouping.** `pkg_manual()` gives one long page in Rd order, not pkgdown's
  sectioned index. That's usually fine. If the grouping really matters, write a custom
  `site/manual.Rmd` (see mapping.md).
- **Old URLs.** Offer redirect stubs so existing links to `reference/foo.html` and
  `articles/bar.html` keep working (step 5).
- **pkgdown-only articles** (`vignettes/articles/*.Rmd`, which are Rbuildignored). They
  won't be picked up. Choose one:
  - move them to `site/<name>.Rmd` as standalone pages (they get rendered by litedown and
    get a nav entry)
  - move them to `examples/` (they then also show up in the playground dropdown)
  - turn them into real vignettes
- **Playground: yes or no.** It's worth adding when the package is pure R, or its
  compiled code builds for WASM (r-universe builds WASM binaries automatically), and its
  output makes sense in a browser. Skip it for packages that need system libraries,
  network/database access, or big data files.
- **Vignette engine.** Existing knitr/rmarkdown vignettes keep working, because the
  articles page just links to whatever `R CMD build` produced. Switching them to
  `litedown::vignette` is optional (see mapping.md).

### 3. Add the site workflow and remove pkgdown

- Copy `assets/github-pages.yml` to `.github/workflows/github-pages.yml`. It builds on
  push to the default branch, uploads a preview artifact on PRs, and deploys to the
  `gh-pages` branch. Adjust the branch name if the default isn't `main`.
- Delete the pkgdown workflow (usually `.github/workflows/pkgdown.yaml`).
- If any vignette uses Quarto (`VignetteBuilder: quarto`), add
  `- uses: quarto-dev/quarto-actions/setup@v2` before the `setup-r-dependencies` step,
  because `R CMD build` needs the Quarto CLI.
- Delete `_pkgdown.yml`. Keep a copy in your head (or in the PR description) of what it
  configured, because you need it for steps 4–5.
- Remove the committed pkgdown output folder, usually `docs/`. This one matters: the
  action treats `docs/_litedown.yml` as a litedown **book** and builds it into `book/`.
  A stale `docs/` is confusing either way.
- Move any assets from `pkgdown/` (for example `extra.css`, favicons) into `site/`, then
  delete `pkgdown/`.
- Update `.Rbuildignore`:
  - remove `^_pkgdown\.yml$`, `^docs$`, `^pkgdown$` (unless `docs/` is kept for a book)
  - add `^site$`, and also `^examples$` and `^playground$` if you create those folders
  - keep `^\.github$`

  These new folders are site sources, not package contents.
- Make sure `README.md` is committed and current. The action reads the `.md` file and
  never knits `README.Rmd`. The home page shows README content from the
  `<!-- badges: start -->` line onward and drops a `# pkgname` title line. If the README
  has no badge markers, the whole file is shown. If pkgdown used a separate
  `index.md`/`pkgdown/index.md` for the home page, merge it into README or write a custom
  `site/index.Rmd`.

### 4. Only add a `site/` folder if you need customization

With no `site/` folder, the action uses its template as-is, and that's the right default.
Create `site/` only for real customizations. A file you put there replaces the template
file with the same name; everything else still comes from the template. Common ones:
- `site/_litedown.yml`: extra CSS/JS through `css2`/`js2` (these add to the defaults;
  `css`/`js` would replace them), or `standalone` patterns. If you create it, include the
  template's contents too (footer include, `number_sections`), because a file you supply
  replaces the template one completely. See mapping.md.
- `site/<page>.Rmd`: an extra top-level page, which gets its own nav entry. Useful for
  migrated pkgdown-only articles.
- `site/manual.Rmd` / `site/index.Rmd`: overrides, only when the defaults really don't
  work.

For extra pages, use litedown syntax, not rmarkdown. The main differences:
- There's no Pandoc: use `::: {.class}` fenced divs, and `@fig:label` / `@tab:label`
  cross-refs with chunk labels.
- Chunk options go in `#|` lines or the chunk header (both are supported).
- There's no `output: rmarkdown::html_vignette`. Drop `output:` or use `output: html`.

### 5. Optional: redirect stubs for old pkgdown URLs

pkgdown sites often have inbound links (CRAN `URL:` field, StackOverflow, papers). This
script writes tiny static HTML files that redirect to the new locations:

```bash
python3 <skill-dir>/scripts/make_redirects.py /path/to/pkg
```

It creates:
- `site/reference/<rd-file>.html` → `../manual.html#sec:man-<name>`
- `site/articles/<vignette>.html` → `../doc/<vignette>.html`

Anchors follow the Rd `\name` exactly (they were checked against the live `lt` site).
Names with unusual characters (operators like `%>%`, `[.foo`) may be slugified
differently, so spot-check those after the first build.

It deliberately does **not** create `reference/index.html` or `articles/index.html`.
litedown adds any subfolder containing an `index.html` to the nav bar, and "Reference"
next to "Manual" would be a confusing duplicate. Pass `--index` if the user wants those
index URLs kept anyway.

### 6. Optional: webR playground

The action always ships `playground/index.html`. To tailor it, add a `playground/` folder
in the **package root** (not in `site/`) with:
- `setup.R`: runs once after webR installs litedown. At minimum it installs the package
  itself, e.g. `webr::install('mypkg', repos = c('https://<user>.r-universe.dev', 'https://repo.r-wasm.org'))`.
  The package has to be available as a WASM binary, and the normal route is r-universe.
- `_default.Rmd` (or `_default.R`): what the editor loads on open. A short, visual,
  fast-running demo of the package works best.

Any `.Rmd`/`.R` files in `examples/` automatically appear in the playground's "Load
example…" dropdown, so one folder feeds both the Examples page and the playground. Read
`references/playground.md` for how the page works, what can't run under webR, and how to
check that the package installs in webR.

### 7. Update links and settings

- **Custom domain** (the pkgdown `url:` isn't `*.github.io`, or there's a `CNAME` on
  gh-pages): create `site/CNAME` containing just the domain. The deploy step replaces the
  whole gh-pages branch, so without this the custom domain stops working.

- DESCRIPTION `URL:`: add or keep the site URL (`https://<user>.github.io/<pkg>/`). The
  URL doesn't change if the site is still served from `gh-pages` on GitHub Pages.
- GitHub **Settings → Pages**: source = "Deploy from a branch", branch = `gh-pages`, `/`
  (root). pkgdown setups often served from `main` `/docs` instead, and that must be
  switched or the site won't update.
- README links to `reference/...` / `articles/...` pages: point them at `manual.html#sec:man-<name>` / `doc/<name>.html`.

### 8. Verify

If R is available locally, do a trial build that mimics the action:

```bash
R CMD build . && R CMD INSTALL <pkg>_*.tar.gz
mkdir -p /tmp/site-test && cd /tmp/site-test
# copy the action template (clone https://github.com/yihui/actions, use litedown-site/*),
# then any site/ overrides, then examples/ and playground/, then:
Rscript -e 'litedown::fuse_site()'
```

Otherwise push to a branch, open a PR, and download the `site-preview` artifact the
workflow uploads. Check each of these:
- the home page (no duplicated title, badges render)
- the manual page (examples render)
- the articles page (every vignette listed)
- the news page
- redirect stubs
- the playground loads, and the default example runs

## What to hand back

End with a short summary for the user covering:
1. the files added, removed and changed
2. which pkgdown features were dropped or replaced (from the DECIDE list), and what was
   chosen
3. the manual steps only they can do: the GitHub Pages setting, publishing the package to
   r-universe if the playground needs it, and updating the CRAN `URL:` field at the next
   release

Don't push or open a PR unless the user asks.
