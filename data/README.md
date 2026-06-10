# data/career.json — the single career record

One JSON array. Every entry is one career fact. **Both** the Survey page
(chronological text index) and the Catalogue page (filterable listings) are
generated from this file by `build.py`, so the two views can never drift.

Transcribed from the Work Inventory MD (Google Drive). When the inventory
changes, edit here and re-run `python3 build.py`.

## Entry schema

| field            | type      | meaning |
|------------------|-----------|---------|
| `id`             | string    | stable unique key |
| `type`           | string    | `series` \| `solo` \| `group` \| `publication` \| `collection` \| `award` \| `residency` \| `commission` \| `teaching` |
| `year`           | int       | **required** — the single sort + decade-bucket key |
| `yearRange`      | string?   | display string (e.g. `"1988–2004"`); falls back to `year` |
| `title`          | string    | display title |
| `venue`          | string?   | gallery / publisher / institution |
| `location`       | string?   | city, region |
| `slug`           | string?   | non-null ⇒ rendered as an internal link `/<slug>/` |
| `url`            | string?   | external link (collections / publications) |
| `note`           | string?   | short descriptor line |
| `catalogueGroups`| string[]  | which Catalogue filter chips this entry matches: `solo` `group` `collection` `publication` `award`. Empty ⇒ appears in Survey only, not Catalogue. |

## How the two pages are generated

- **Survey** — all entries, sorted by `year`, grouped under decade markers; every
  row is a block-level `<a>` (links to `/slug/`, else `url`, else `/catalogue/`).
- **Catalogue** — only entries with a non-empty `catalogueGroups`; earliest-first
  with decade markers and thumbnails. `catalogue.js` filters/sorts client-side
  from `data-groups` / `data-year` attributes already in the static HTML.

## Known gaps (carried from the inventory — confirm with Peter)

- Sun Valley residency: 1974–1979 (interview) vs 1976–1981 (CV).
- Dates for several series are approximate placeholders (Peopled Landscape, Big
  Rock Candy Mountain, The Rock, Half Memory, Somewhere Along the Way, Balance,
  Still Lifes, Western Neon Signs, Pacific Heights Mansions).
- The River and Flora commissions: no confirmed client/date — omitted until known.
