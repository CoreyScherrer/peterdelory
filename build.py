#!/usr/bin/env python3
"""
build.py — static-site generator for the Peter de Lory website.

Dev-time only, Python 3 stdlib only. Stamps the locked header/footer, per-page
<head>, and Schema.org JSON-LD into every page, then writes pure static HTML to
public/. Survey and Catalogue are both generated from data/career.json so the
two views never drift. Fails the build if the name "de Lory" is mis-capitalized.

Usage:  python3 build.py
"""

import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUB = ROOT / "public"
PARTIALS = ROOT / "partials"
TEMPLATES = ROOT / "templates"
CONTENT = ROOT / "content"
DATA = ROOT / "data"

DECADE_LABEL = {
    1960: "1960s", 1970: "1970s", 1980: "1980s", 1990: "1990s",
    2000: "2000s", 2010: "2010s", 2020: "2020s",
}
TYPE_LABEL = {
    "series": "Series", "solo": "Solo show", "group": "Group show",
    "publication": "Publication", "collection": "Collection", "award": "Award",
    "residency": "Residency", "commission": "Commission", "teaching": "Teaching",
}


def read(p):
    return Path(p).read_text(encoding="utf-8")


def load_json(p):
    return json.loads(read(p))


def fill(tpl, mapping):
    """Replace {{key}} tokens present in `mapping`. Unknown tokens (e.g. the
    generated-region markers GENERATED/PULLQUOTE/META) are left intact so later
    explicit .replace() calls can fill them."""
    def sub(m):
        key = m.group(1)
        return str(mapping[key]) if key in mapping else m.group(0)
    return re.sub(r"\{\{(\w+)\}\}", sub, tpl)


# ── Header / footer (rendered once; identical on every page) ────────────────
def render_nav(nav_items):
    out = []
    for i, item in enumerate(nav_items):
        if i:
            out.append('    <span class="pipe">|</span>')
        out.append('    <a href="{href}">{label}</a>'.format(
            href=html.escape(item["href"]), label=html.escape(item["label"])))
    return "\n".join(out)


def build_header(site):
    return read(PARTIALS / "header.html").replace("{{nav}}", render_nav(site["nav"]))


# ── JSON-LD ─────────────────────────────────────────────────────────────────
def jsonld_person():
    return read(PARTIALS / "jsonld-person.html").strip()


def jsonld_visualartwork(page, data, site):
    if not data:
        return ""
    obj = {
        "@context": "https://schema.org",
        "@type": "VisualArtwork",
        "name": data.get("title", page.get("title", "")),
        "creator": {"@type": "Person", "name": "Peter de Lory"},
        "url": site["base_url"] + page["url"],
        "artform": "Photography",
    }
    if data.get("period"):
        obj["dateCreated"] = data["period"]
    meta = data.get("meta") or {}
    if meta.get("medium"):
        obj["artMedium"] = meta["medium"]
    return '<script type="application/ld+json">\n%s\n</script>' % json.dumps(obj, indent=2)


def render_jsonld(kinds, page, data, site):
    blocks = []
    for kind in kinds:
        if kind == "person":
            blocks.append(jsonld_person())
        elif kind == "visualartwork":
            blocks.append(jsonld_visualartwork(page, data, site))
    return "\n".join(b for b in blocks if b)


# ── <head> ──────────────────────────────────────────────────────────────────
def asset_version():
    """Short content hash of site.css — used as a ?v= cache-buster so a CSS
    change forces browsers to fetch the new file instead of a stale cache."""
    import hashlib
    css = (PUB / "assets" / "site.css").read_bytes()
    return hashlib.sha1(css).hexdigest()[:8]


def build_head(page, data, site, asset_ver):
    canonical = site["base_url"] + page["url"]
    og_image = site["base_url"] + ((data or {}).get("og_image") or site["og_default"])
    # Site-wide noindex while the site is being refined; flip site.noindex to
    # false (in content/pages.json) to make it indexable.
    robots_meta = ('<meta name="robots" content="noindex, nofollow">\n'
                   if site.get("noindex") else "")
    return fill(read(PARTIALS / "head.html"), {
        "title": html.escape(page["title"]),
        "description": html.escape(page["description"]),
        "canonical": canonical,
        "og_type": page.get("og_type", "website"),
        "og_image": og_image,
        "asset_ver": asset_ver,
        "robots_meta": robots_meta,
    })


# ── Images ──────────────────────────────────────────────────────────────────
# Google Drive thumbnail URLs do NOT hotlink as <img> (they return an HTML
# login/error page), so we treat them as "not yet available" and render the
# clean black placeholder band instead. The Drive IDs stay in the content JSON
# for the later real-image swap. Any non-Drive http(s) URL or local /assets path
# is emitted as a real <img>.
def img_available(url):
    if not url:
        return False
    return "drive.google.com" not in url


def hero_block(data, classname="series-hero", pos_default="50% 70%"):
    """Full-bleed hero. Real <img> if an image is available, else a clean band.
    Supports optional hero_scale (int percent) for zoom-in framing set by the
    editor; default/100 produces byte-identical output to the un-zoomed form."""
    url = data.get("hero")
    if img_available(url):
        pos = data.get("hero_pos", pos_default)
        style = "object-position:%s" % pos
        scale = data.get("hero_scale")
        if scale and int(scale) != 100:
            style += ";transform:scale(%.3f);transform-origin:%s" % (int(scale) / 100.0, pos)
        return '<img src="{src}" alt="{alt}" style="{style}">'.format(
            src=html.escape(url), alt=html.escape(data.get("hero_alt", "")), style=style)
    return ""  # empty hero band (CSS gives it the black background)


def thumb_block(url, alt, pos):
    if img_available(url):
        return ('<div class="series-thumb"><img loading="lazy" src="{src}" '
                'alt="{alt}" style="object-position:{pos}"></div>').format(
            src=html.escape(url), alt=html.escape(alt), pos=pos)
    return '<div class="series-thumb"></div>'


# ── Page-type body builders ─────────────────────────────────────────────────
def body_home(tpl, data):
    rows = []
    for s in data["series_grid"]:
        href = s.get("href") or ("/%s/" % s["slug"])
        thumb = thumb_block(s.get("thumb"), s["title"], s.get("thumb_pos", "50% 50%"))
        rows.append(
            '      <a class="series-item" href="{href}">\n        {thumb}\n'
            '        <div class="series-info">\n'
            '          <p class="series-title">{title}</p>\n'
            '          <p class="series-subtitle">{sub}</p>\n'
            '        </div>\n      </a>'.format(
                href=html.escape(href), thumb=thumb,
                title=html.escape(s["title"]), sub=html.escape(s.get("subtitle", ""))))
    out = fill(tpl, {
        "hero_quote": html.escape(data.get("hero_quote", "")),
        "hero_attr": html.escape(data.get("hero_attr", "")),
    })
    out = out.replace("{{HERO}}", hero_block(data, "hero", "50% 28%"))
    return out.replace("{{GENERATED}}", "\n".join(rows))


def body_series(tpl, data):
    # Pull quote (optional)
    if data.get("pullQuote"):
        cite = ('<cite>%s</cite>' % html.escape(data["quoteAttr"])) if data.get("quoteAttr") else ""
        pq = ('      <blockquote class="series-pull-quote">%s%s</blockquote>'
              % (html.escape(data["pullQuote"]), cite))
    else:
        pq = ""
    # Meta rail (optional; skip empty)
    meta = data.get("meta") or {}
    rows = []
    for label, value in meta.items():
        if not value:
            continue
        rows.append('      <div class="meta-row"><span>%s</span><span>%s</span></div>'
                    % (html.escape(label.capitalize()), html.escape(str(value))))
    meta_block = ('    <aside class="series-meta">\n%s\n    </aside>' % "\n".join(rows)) if rows else ""

    out = fill(tpl, {
        "title": html.escape(data["title"]),
        "period": html.escape(data.get("period", "")),
        "body": data.get("body", ""),  # trusted authored HTML w/ entity links
    })
    out = out.replace("{{HERO}}", hero_block(data, "series-hero", "50% 70%"))
    out = out.replace("{{PULLQUOTE}}", pq).replace("{{META}}", meta_block)
    return out


def body_prose(tpl, data):
    return tpl.replace("{{body}}", data["body"])


def body_notable(tpl, data):
    entries = []
    for e in data["entries"]:
        if img_available(e.get("img")):
            img = ('  <div class="notable-img-placeholder"><img loading="lazy" '
                   'src="{src}" alt="{alt}" style="object-position:{pos}"></div>').format(
                src=html.escape(e["img"]), alt=html.escape(e.get("img_alt", "")),
                pos=e.get("img_pos", "50% 50%"))
        else:
            img = '  <div class="notable-img-placeholder"></div>'
        entries.append(
            '<div class="notable-entry">\n%s\n  <h2>%s</h2>\n%s\n</div>'
            % (img, html.escape(e["h2"]), e["body"]))
    out = fill(tpl, {"h1": html.escape(data["h1"]), "intro": html.escape(data["intro"])})
    return out.replace("{{GENERATED}}", "\n".join(entries))


# ── Survey + Catalogue (from data/career.json) ──────────────────────────────
def link_target(e):
    if e.get("slug"):
        # commission slugs live under /commissions/<slug>/
        comm = {"champion", "railwork-sound-transit", "citywork",
                "seattle-water-dept", "a-pathway"}
        return "/commissions/%s/" % e["slug"] if e["slug"] in comm else "/%s/" % e["slug"]
    if e.get("url"):
        return e["url"]
    return "/catalogue/"


def decade_of(year):
    return (year // 10) * 10


def body_survey(tpl, career):
    entries = sorted(career, key=lambda e: (e["year"], e["title"]))
    parts = []
    cur = None
    for e in entries:
        d = decade_of(e["year"])
        if d != cur:
            cur = d
            parts.append('  <h2 class="survey-decade">%s</h2>'
                         % DECADE_LABEL.get(d, "%ds" % d))
        yr = e.get("yearRange") or str(e["year"])
        venue = " · ".join(x for x in [e.get("venue"), e.get("location")] if x)
        parts.append(
            '  <a class="survey-entry" href="{href}">'
            '<span class="year">{yr}</span>'
            '<span class="title">{title}{venue}</span>'
            '<span class="type">{type}</span></a>'.format(
                href=html.escape(link_target(e)), yr=html.escape(yr),
                title=html.escape(e["title"]),
                venue=(' <span style="color:#aaa">— %s</span>' % html.escape(venue)) if venue else "",
                type=html.escape(TYPE_LABEL.get(e["type"], e["type"]))))
    return tpl.replace("{{GENERATED}}", "\n".join(parts))


def body_catalogue(tpl, career):
    listable = [e for e in career if e.get("catalogueGroups")]
    listable.sort(key=lambda e: (e["year"], e["title"]))
    parts = []
    cur = None
    for e in listable:
        d = decade_of(e["year"])
        if d != cur:
            cur = d
            parts.append('    <div class="cat-decade">%s</div>'
                         % DECADE_LABEL.get(d, "%ds" % d))
        groups = " ".join(e["catalogueGroups"])
        yr = e.get("yearRange") or str(e["year"])
        venue = " · ".join(x for x in [e.get("venue"), e.get("location")] if x)
        title = html.escape(e["title"])
        href = link_target(e)
        title_html = ('<a href="%s">%s</a>' % (html.escape(href), title)) \
            if (e.get("slug") or e.get("url")) else title
        thumb = e.get("thumb")
        thumb_html = ('<img class="cat-thumb" loading="lazy" src="%s" alt="">'
                      % html.escape(thumb)) if thumb else '<span class="cat-thumb"></span>'
        parts.append(
            '    <article class="cat-row" data-groups="{groups}" data-year="{year}">\n'
            '      {thumb}\n'
            '      <span class="cat-year">{yr}</span>\n'
            '      <div class="cat-body">\n'
            '        <div class="cat-title">{title}</div>\n'
            '        <div class="cat-venue">{venue}</div>\n'
            '      </div>\n    </article>'.format(
                groups=html.escape(groups), year=e["year"], thumb=thumb_html,
                yr=html.escape(yr), title=title_html, venue=html.escape(venue)))
    return tpl.replace("{{GENERATED}}", "\n".join(parts))


# ── Assemble + write a page ─────────────────────────────────────────────────
def assemble(head, jsonld, header, body, footer):
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        + head.rstrip() + "\n"
        + (jsonld + "\n" if jsonld else "")
        + "</head>\n<body>\n"
        + header.rstrip() + "\n"
        + body.rstrip() + "\n"
        + footer.rstrip() + "\n"
        + "</body>\n</html>\n"
    )


# ── Name capitalization scan ────────────────────────────────────────────────
BANNED = re.compile(r"De ?Lory|DELORY|de lory")
ALLOW = re.compile(r"peter@peterdelory\.com|peterdeloryphotographer")


def scan_capitalization(targets):
    bad = []
    for path in targets:
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for m in BANNED.finditer(line):
                # Skip if the match sits inside an allowed token.
                ctx = line[max(0, m.start() - 25): m.end() + 25]
                if ALLOW.search(ctx):
                    continue
                bad.append("%s:%d  %s" % (path.relative_to(ROOT), n, line.strip()[:90]))
    return bad


# ── sitemap / robots ────────────────────────────────────────────────────────
def write_sitemap(site, pages):
    today = date.today().isoformat()
    urls = "\n".join(
        "  <url><loc>%s%s</loc><lastmod>%s</lastmod></url>"
        % (site["base_url"], p["url"], today) for p in pages)
    (PUB / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls + "\n</urlset>\n", encoding="utf-8")
    if site.get("noindex"):
        # Keep the whole site out of search engines while it's being refined.
        robots = "User-agent: *\nDisallow: /\n"
    else:
        robots = "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % site["base_url"]
    (PUB / "robots.txt").write_text(robots, encoding="utf-8")


def write_404(header, footer):
    body = ('<main id="main" class="prose-section">\n'
            '  <h1>Not found</h1>\n'
            '  <p>That page doesn\'t exist. <a href="/">Return to the work</a>.</p>\n'
            '</main>')
    head = ('<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, '
            'initial-scale=1.0">\n<title>Not found — Peter de Lory</title>\n'
            '<meta name="robots" content="noindex">\n'
            '<link rel="stylesheet" href="/assets/site.css">')
    (PUB / "404.html").write_text(
        assemble(head, "", header, body, footer), encoding="utf-8")


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    manifest = load_json(CONTENT / "pages.json")
    site = manifest["site"]
    career = load_json(DATA / "career.json")

    header = build_header(site)
    footer = read(PARTIALS / "footer.html")
    asset_ver = asset_version()

    written = 0
    for page in manifest["pages"]:
        tpl = read(TEMPLATES / page["template"])
        data = load_json(ROOT / page["data"]) if page.get("data") else {}

        name = page["template"]
        if name == "home.html":
            body = body_home(tpl, data)
        elif name in ("series.html", "commission-sub.html"):
            body = body_series(tpl, data)
        elif name == "survey.html":
            body = body_survey(tpl, career)
        elif name == "catalogue.html":
            body = body_catalogue(tpl, career)
        elif name == "notable.html":
            body = body_notable(tpl, data)
        else:  # about, commissions-index, contact = prose
            body = body_prose(tpl, data)

        head = build_head(page, data, site, asset_ver)
        jsonld = render_jsonld(page.get("jsonld", []), page, data, site)

        out_path = PUB / page["out"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(assemble(head, jsonld, header, body, footer), encoding="utf-8")
        written += 1

    write_sitemap(site, manifest["pages"])
    write_404(header, footer)

    # Capitalization gate — scan generated HTML + authored sources.
    targets = list(PUB.rglob("*.html")) + list(CONTENT.rglob("*.json")) \
        + list(DATA.rglob("*.json")) + list(PARTIALS.glob("*.html"))
    bad = scan_capitalization(targets)
    if bad:
        print("BUILD FAILED — name capitalization violations:", file=sys.stderr)
        for b in bad:
            print("  " + b, file=sys.stderr)
        sys.exit(1)

    print("Wrote %d pages + sitemap.xml + robots.txt + 404.html" % written)
    print("Name scan: clean.")


if __name__ == "__main__":
    main()
