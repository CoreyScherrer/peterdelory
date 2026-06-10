# Peter de Lory — Photographer Website

Static site for photographer **Peter de Lory** (50+ years of work; Smithsonian
collections; *Aperture* frontispiece under Minor White, 1973; NEA Fellowship;
public art at Sea-Tac, Sound Transit, Seattle Public Utilities).

A **commercial artist brand engine**: beautiful for curators/collectors,
structured for SEO (entity links + Schema.org), built to convert interest into
acquisitions.

## ⚠️ Name capitalization — the one hard rule

The artist's name is **Peter de Lory**. The **"de" is always lowercase**, everywhere:
HTML, titles, JSON-LD, meta, Open Graph, alt text, comments, filenames.

- ✅ `Peter de Lory`
- ❌ `Peter De Lory` / `DeLory` / sentence-starting `De Lory ...`

`build.py` runs a scan that **fails the build** on any banned form
(the lowercase email `peter@peterdelory.com` and domain
`peterdeloryphotographer.com` are whitelisted).

## How it works

Plain static HTML/CSS/JS. No SSG, no runtime framework. A **dev-time** Python 3
generator (`build.py`, stdlib only) stamps the locked header/footer, per-page
`<head>`, and Schema.org JSON-LD into every page from:

- `content/pages.json` — the page manifest (meta + template + data per page)
- `content/series/*.json`, `content/commissions/*.json`, `content/notable.json`
- `data/career.json` — the single career record that **both** Survey and
  Catalogue generate from (so the two views never drift)
- `partials/` (header, footer, head, Person JSON-LD) and `templates/`

Output is written to **`public/`** — the only thing served by nginx. The
generated HTML is committed (fully static; header inline for SEO + no-JS robustness).

## Build & preview

```sh
python3 build.py            # regenerates everything under public/
cd public && python3 -m http.server 8080
# open http://localhost:8080/
```

## Layout

```
build.py          partials/   templates/   content/   data/   deploy/
public/           # ← nginx webroot (generated, committed)
  assets/site.css assets/nav.js assets/catalogue.js assets/img/
```

## Deploy (separate step — see deploy/)

Standalone nginx static site, domain **peterdeloryphotographer.com**, webroot
`/var/www/peterdeloryphotographer/www/public`, mirroring the existing
`coreyiscorey.com` static-site pattern. Draft nginx conf, deploy script, and
notes live in `deploy/`.

## Backup

This repo is also backed up to the Google Drive folder **"Peter De Lory"**
(alongside the project brief, work inventory, and publication scans).
