# pkgdown feature → litedown equivalent

Use this table when you go through an existing `_pkgdown.yml` and pkgdown setup. The
litedown column describes `yihui/actions/litedown-site` combined with `litedown::fuse_site()`.

## Contents
- Config and layout
- Home page
- Reference
- Articles / vignettes
- News, authors, citation
- Search, theming, extras
- `_litedown.yml` template
- Custom grouped manual page
- Converting vignettes to the litedown engine

## Config and layout

| pkgdown | litedown | notes |
|---|---|---|
| `_pkgdown.yml` | optional `site/_litedown.yml` | Most packages need no config at all. |
| `url:` | nothing | The URL isn't needed to build; keep it in DESCRIPTION `URL:`. |
| `destination: docs` | action input `site-dir` (default `site`) | The site is built in `site/` in CI and pushed to `gh-pages`. Don't commit the output. |
| `navbar:` structure/components | automatic nav: one link per top-level page + subfolders with `index.html` | For a custom menu, set `include_before` in `_litedown.yml` to Markdown links, e.g. `"[Home](/) [Manual](/manual.html) [GitHub](https://github.com/u/p)"`. Leading `/` links are made relative automatically. There are no dropdown menus. |
| `navbar: components: github:` | nothing automatic | Add it to `include_before` (above) or the README badges. |
| `footer:` | `site/_footer.Rmd` (template: "Developed by <authors> · Site built with litedown") | This is rendered to `_footer.md`, which `_litedown.yml` includes through `include_after`. |
| `development: mode:` / dev site | nothing | There's one site, built from the default branch. Use the PR preview artifact for dev checks. |
| `deploy: install_metadata` | nothing | |
| `pkgdown/extra.css`, `extra.js` | `site/extra.css` + `css2: ["extra.css"]` / `js2:` | `css2`/`js2` add to the default assets. `css`/`js` replace them. |
| `pkgdown/favicon/`, `logo:` | nothing built in | Put the logo in README (`man/figures/logo.png`; the index page copies `man/figures` into the site). For a favicon, add a `<link rel="icon">` through the `header_includes` meta variable, or drop it. |

## Home page

| pkgdown | litedown |
|---|---|
| `README.md` / `index.md` / `pkgdown/index.md` | Only `README.md`, and only from `<!-- badges: start -->` onward. A `# pkgname` heading is removed. Merge `index.md` content into README, or write a custom `site/index.Rmd` (start from the action's `index.Rmd`). |
| `README.Rmd` | Not knitted in CI. Knit it locally and commit `README.md`. |
| sidebar (links, license, citation, authors, dev status) | The `pkg_desc()` metadata table (Title, Version, Description, Depends, Imports, Suggests, License, URL, BugReports, Authors) + the citation appendix. |
| `home: title/description` | The page title comes from DESCRIPTION: "`pkg`: `Title`". |
| `home: links:` | Put these in README. |

## Reference

| pkgdown | litedown |
|---|---|
| `reference/index.html` with `reference: - title:/contents:` sections | A single `manual.html` from `pkg_manual()`: every Rd page, numbered sections, a TOC. The package overview (`pkg-package.Rd`) comes first. **Sections/grouping are not supported by default.** |
| one page per topic (`reference/foo.html`) | An anchor per topic: `manual.html#sec:man-<Rd \name>` (e.g. `#sec:man-lt_header`). Use `scripts/make_redirects.py` to keep the old URLs working. |
| examples run and shown with output | The `examples` argument of `pkg_manual()` is a list passed to `xfun::record()` (e.g. `list(dev = 'svg')`); `FALSE` turns running off. The template uses the default. Wrap slow or network code in `\donttest{}` / `\dontrun{}` as usual. |
| downlit autolinking of function names in code | Not available. Rd `\link{}`s still become links within the manual page. |
| `@family` "See also" | Kept (it's part of the Rd). |

If the grouping really matters (large packages with 100+ topics), see "Custom grouped
manual page" below.

## Articles / vignettes

| pkgdown | litedown |
|---|---|
| `vignettes/*.Rmd` (any engine) | `articles.html` lists every vignette `R CMD build` produced (copied from the installed package's `doc/`), with title + source link. **Nothing needs to change.** knitr/rmarkdown vignettes still build in CI because `setup-r-dependencies` installs Suggests and runs `R CMD build`. |
| `vignettes/articles/*.Rmd` (Rbuildignored, pkgdown-only) | **Not picked up.** Move each to `site/<name>.Rmd` (a top-level page with a nav entry), or to `examples/` (a listed example + playground dropdown), or make it a real vignette. Convert any rmarkdown-only syntax (see below). |
| `articles:` index sections / navbar menu | Just a flat list in `articles.html`. Write a custom `site/articles.Rmd` if you need sections. |
| `articles/foo.html` URLs | `doc/foo.html`. Use `scripts/make_redirects.py`. |

## News, authors, citation

| pkgdown | litedown |
|---|---|
| `news/index.html` from `NEWS.md` | `news.html` via `pkg_news(recent = 0)`: full history, one section per version. `inst/NEWS.Rd` works too. |
| `authors.html` | No separate page. Authors show up in the metadata table and the footer. Keep ORCID etc. in `Authors@R`. |
| citation on `authors.html` | Appendix of `index.html` via `pkg_citation()` (reads `inst/CITATION`, or falls back to the auto-generated one). |

## Search, theming, extras

| pkgdown | litedown |
|---|---|
| built-in search (`search.json`) | None. Say so plainly. On a single-page manual, the browser's find works well. |
| Bootstrap 5 / bslib `template: bootstrap: 5`, `bslib:` variables | None. It's a plain article layout from `@xiee/utils` CSS. Change it with `css2` (a small CSS file). Don't try to rebuild a Bootstrap theme. |
| light/dark switch | None by default. You could add `@media (prefers-color-scheme: dark)` rules in custom CSS. |
| code copy buttons, heading anchors, TOC highlighting | Included by default (`@copy-button`, `@heading-anchor`, `@toc-highlight`). |
| math (MathJax / KaTeX) | litedown detects `$…$` math and loads KaTeX by default (configurable through the `js_math` option). |
| `.Rbuildignore`: `^_pkgdown\.yml$ ^docs$ ^pkgdown$` | Replace them with `^site$ ^examples$ ^playground$`, including only the folders that exist. |
| `r-lib/actions/examples/pkgdown.yaml` workflow | `assets/github-pages.yml`. |

## `_litedown.yml` template

The action's default, which you need to keep if you supply your own:

```yaml
site:

output:
  html:
    meta:
      include_after: "_footer.md"
    options:
      number_sections: true
```

A typical customized version:

```yaml
site:
  standalone: ["slides-*.Rmd"]   # pages built without site nav/CSS

output:
  html:
    meta:
      css2: ["extra.css"]
      include_after: "_footer.md"
      # include_before: "[Home](/) [Manual](/manual.html) [Articles](/articles.html) [News](/news.html) [Playground](/playground/)"
    options:
      number_sections: true
```

## Custom grouped manual page

`pkg_manual()` has no grouping option. For grouping, write `site/manual.Rmd` so that it
renders Rd files per section. Keep it simple: a hand-written index of links to the default
anchors is usually enough, and it's robust:

````markdown
---
title: Help pages
---

## Overview {-}

**Building tables:** [lt()](#sec:man-lt), [lt_header()](#sec:man-lt_header), …

**Formatting:** [lt_format()](#sec:man-lt_format), …

`{r} litedown::pkg_manual()`
````

Generate the link lists from the old `_pkgdown.yml` `reference:` sections, mapping each
listed topic to `#sec:man-<topic>`. Selectors like `starts_with("lt_")` need expanding
against `man/*.Rd` \name entries. Let the user know any topics the old config left out;
they will now appear in the manual anyway.

## Converting vignettes to the litedown engine (optional)

You only need this if the user wants to drop knitr/rmarkdown from Suggests. In
DESCRIPTION, set `VignetteBuilder: litedown` and `Suggests: litedown`. Then in each
vignette:

```yaml
---
title: "…"
output: html        # or omit
vignette: >
  %\VignetteEngine{litedown::vignette}
  %\VignetteIndexEntry{…}
  %\VignetteEncoding{UTF-8}
---
```

Syntax differences to fix (litedown has no Pandoc):
- `output: rmarkdown::html_vignette` → drop it.
- Fenced divs (`::: {.note}`) work. Pandoc-only extensions (Lua filters, raw LaTeX
  blocks, `{=html}` raw attributes beyond what commonmark allows) do not, so render
  the page and check.
- `knitr::kable()` still works; `results = 'asis'` is supported.
- Cross-refs: `@fig:label` / `@tab:label` / `@eq:label` (chunk label + `fig.cap`),
  not bookdown's `\@ref()`.
- Citations: litedown supports `[@key]` with a `bibliography:` field, but check the
  output. If it's complicated, keep the knitr engine for that vignette.
- `knitr::opts_chunk$set()` → `litedown::reactor()`.
- htmlwidgets that depend on rmarkdown's dependency injection may not render. Keep those
  vignettes on the rmarkdown engine.

Mixed engines within one package are fine.
