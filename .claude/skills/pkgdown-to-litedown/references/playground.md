# The litedown webR playground

Every site built by `yihui/actions/litedown-site` includes `playground/index.html`, one
static page taken from the action's template. It's the same file on every package's site;
packages customize it only through data files. Live examples:
https://pkg.yihui.org/litedown/playground/ and https://pkg.yihui.org/lt/playground/.

## How it works (runtime)

1. It loads CodeMirror 5 from jsdelivr, then `https://webr.r-wasm.org/latest/webr.mjs`.
2. It runs `webr::shim_install()`, then installs `commonmark`, `xfun`, `litedown` and
   `codetools` from `https://yihui.r-universe.dev` + `https://repo.r-wasm.org`.
3. It fetches `./setup.R` and runs it once (`evalRVoid`) if the file exists.
4. It fetches `./_default.Rmd`, falling back to `./_default.R`, into the editor.
5. It fetches `./examples.txt`, one filename per line, and fills "Load example…". Choosing
   an option fetches `../examples/<file>`.
6. **Run** (or Ctrl/Cmd+Shift+Enter) writes the editor text to `/tmp/<name>` in webR's
   virtual file system, runs
   `setwd("/tmp"); litedown::fuse(file, output = structure(NA, full = TRUE))`, and
   writes the returned full HTML page into an `<iframe>` with `document.write`.
   Plots are base64-embedded, so they show up.

## What the package author provides (build time)

The action copies these from the **package root**:

| path | effect |
|---|---|
| `playground/setup.R` | Runs once in webR after the base packages are installed. |
| `playground/_default.Rmd` or `_default.R` | Starting editor content (the `.Rmd` is tried first). |
| `examples/*.Rmd`, `examples/*.R` | Rendered on the Examples page **and** listed in `playground/examples.txt`. Files starting with `_` are skipped. |

Typical `setup.R`:

```r
webr::install('mypkg', repos = c('https://myuser.r-universe.dev', 'https://repo.r-wasm.org'))
# optional: extra Suggests the examples need
webr::install(c('ggplot2'), quiet = TRUE)
```

(litedown's own `setup.R` just installs `KernSmooth`. For `lt`, it's
`webr::install('lt', repos = 'https://yihui.r-universe.dev')`.)

A `_default.Rmd` should run in a few seconds and show off the package visually:

````markdown
---
title: Hello mypkg
---

```{r}
library(mypkg)
# the smallest example that produces a nice result
```
````

## Getting the package into webR

webR can only install WASM binaries. Here are the options, most practical first:
1. **r-universe.** Register the GitHub repo in a `<user>.r-universe.dev` universe. It
   builds WASM binaries automatically for pure-R packages, and for most compiled packages
   too. Then use `repos = 'https://<user>.r-universe.dev'`.
2. **CRAN packages** are usually already on `https://repo.r-wasm.org`.
3. Build it yourself with `rwasm` and host the repo with the site. Only do this when 1
   and 2 aren't possible.

To check, open any webR console (e.g. https://webr.r-wasm.org/latest/) and run
`webr::install('mypkg', repos = ...)`, then `library(mypkg)` and the default example.
Dependencies that fail there will fail in the playground too.

## Things that won't work under webR

These are the reasons to skip the playground, or to steer the default example away from
them:
- System commands, Node.js, headless browsers (`system()`, `processx`, `chromote`,
  `webshot`, and `lt::lt_export()` baking/PDF/PNG). Detect this and degrade gracefully,
  as `lt` does with `can_bake()`.
- Arbitrary network access from R. There are CORS limits; `download.file()` from
  most hosts fails.
- Packages with system-library dependencies that have no WASM port.
- Large data or long computations. The first load already has to install packages, so
  keep demos light.
- Output that needs server-side assets. Output that loads JS/CSS from a CDN works well
  (htmlwidgets-free designs like `lt`, which emits a JSON spec + a `<script src=…>`).

## Known limitations to mention to the user

- It always loads webR `latest`, so the version isn't pinned.
- The editor content isn't kept in the URL or in storage, so there's no share link.
- `document.write` into a same-origin iframe isn't sandboxed. That's fine for the user's
  own code.
- The first load takes 10–60 s, depending on dependencies.

If the user wants any of these changed, commit a customized
`playground/index.html` in the package root. The action copies `playground/.` over the
template, so it takes priority. From then on they own that file and won't receive
upstream improvements.
