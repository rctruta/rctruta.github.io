"""Apply data/TAGS.yaml to the pages, and build tags.html from it.

    python3 tools/build_tags.py

A tag is a claim that two pieces of work share something. Until it resolves to
the full list of work carrying it, nobody can check that claim. This writes the
tag rows into the pages from one vocabulary, and builds the index they point at.

Fails loudly on a tag that is not in the vocabulary, and on a project id in the
pages that the vocabulary does not cover. Idempotent.
"""
import html
import pathlib
import re
import sys
from collections import defaultdict
from config_loader import load_config

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = load_config()

AUTHOR = CONFIG["site"]["author"].get("name", "Author")
SITE_TITLE = CONFIG["site"].get("title", AUTHOR)
SITE_URL = CONFIG["site"].get("url", "")
SITE_IMAGE = CONFIG["site"].get("image", f"{SITE_URL}/assets/photo.jpg")
LICENSE_LABEL = CONFIG["site"].get("copyright_license", "CC BY-NC-SA 4.0")
LICENSE_URL = CONFIG["site"].get("copyright_license_url", "https://creativecommons.org/licenses/by-nc-sa/4.0/")

PAGES = ["work.html", "teaching.html"]
SPEC = ROOT / "data" / "TAGS.yaml"


def parse_tags_yaml(text):
    """Parse facets metadata, kinds metadata, vocabulary terms, and project mappings."""
    facets_meta = {}
    kinds_meta = {}
    vocab = {}
    projects = {}
    section = None
    current_item = None
    facet_name = None

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        if indent == 0 and line.endswith(":"):
            section = line[:-1]
            current_item = None
            continue

        if section == "facets":
            if indent == 2 and line.endswith(":"):
                current_item = line[:-1]
                facets_meta[current_item] = {"label": current_item.title(), "note": "", "order": 99}
            elif indent == 4 and current_item and ":" in line:
                k, v = [x.strip() for x in line.split(":", 1)]
                v = v.strip('"\'')
                if k == "order":
                    v = int(v)
                facets_meta[current_item][k] = v

        elif section == "kinds":
            if indent == 2 and line.endswith(":"):
                current_item = line[:-1]
                kinds_meta[current_item] = {"category": current_item.title(), "order": 99}
            elif indent == 4 and current_item and ":" in line:
                k, v = [x.strip() for x in line.split(":", 1)]
                v = v.strip('"\'')
                if k == "order":
                    v = int(v)
                kinds_meta[current_item][k] = v

        elif section == "vocabulary":
            if indent == 2 and line.endswith(":"):
                facet_name = line[:-1]
                continue
            if indent == 4 and facet_name and ":" in line:
                term = line.split(":", 1)[0].strip()
                vocab[term] = facet_name

        elif section == "projects" and indent == 2 and ":" in line:
            pid, rest = line.split(":", 1)
            projects[pid.strip()] = [
                t.strip() for t in rest.strip().strip("[]").split(",") if t.strip()
            ]

    return facets_meta, kinds_meta, vocab, projects


facets_meta, kinds_meta, vocab, projects = parse_tags_yaml(SPEC.read_text())

unknown = {t: p for p, ts in projects.items() for t in ts if t not in vocab}
if unknown:
    sys.exit(
        "tags not in the vocabulary — add them to data/TAGS.yaml first:\n  "
        + "\n  ".join(f"{t}  (on {p})" for t, p in unknown.items())
    )


def slug(tag):
    return re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")


def row(tags):
    cells = "".join(
        f'<a class="tag" href="tags.html#{slug(t)}">{html.escape(t)}</a>' for t in tags
    )
    return f'<div class="tags">{cells}</div>'


# ---- write the tag rows into the pages -------------------------------------

index = defaultdict(list)
seen = set()

for name in PAGES:
    page = ROOT / name
    text = page.read_text()

    def replace(block):
        pid = block.group(1)
        body = block.group(2)
        seen.add(pid)
        if pid not in projects:
            return block.group(0)
        heading = re.search(r"<h3[^>]*>(.*?)</h3>", body, re.S)
        raw = heading.group(1) if heading else pid
        raw = re.sub(r'<span class="meta">.*?</span>', "", raw, flags=re.S)
        title = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        title = re.sub(r"\s+", " ", title).strip()
        if name == "teaching.html":
            kind = "course material" if "assets/" in (heading.group(1) if heading else "") else "teaching"
        else:
            kind = "project"
        m_date = re.search(r"20\d\d", body)
        date_str = m_date.group(0) if m_date else "2026"
        for t in projects[pid]:
            index[t].append((name, pid, title, kind, date_str))
        body = re.sub(r'<div class="tags">.*?</div>', row(projects[pid]), body, flags=re.S)
        return f'<div class="proj" id="{pid}">{body}'

    text = re.sub(
        r'<div class="proj" id="([^"]*)">(.*?)(?=<div class="proj"|</div></section>)',
        replace,
        text,
        flags=re.S,
    )
    page.write_text(text)

# articles live in writing.yaml, not in a page — index them from the source
wtext = (ROOT / "data" / "writing.yaml").read_text()
for block in re.split(r"\n(?=- id:)", wtext):
    if not block.lstrip().startswith("- id:"):
        continue
    def field(k):
        m = re.search(rf"^\s*(?:-\s*)?{k}: (.+?)\s*(?:#.*)?$", block, re.M)
        return m.group(1).strip().strip('"') if m else None
    wid, title, date_val, tags_line = field("id"), field("title"), field("date"), re.search(r"^  tags: \[(.*)\]\s*$", block, re.M)
    if not title or not tags_line:
        continue
    for tag in (x.strip() for x in tags_line.group(1).split(",")):
        if tag and tag in vocab:
            index[tag].append(("writing.html", wid or "", title, "article", date_val or "2026"))

# speaking appearances live in appearances.yaml — index them from the source
atext = (ROOT / "data" / "appearances.yaml").read_text()
for block in re.split(r"\n(?=- id:)", atext):
    if not block.lstrip().startswith("- id:"):
        continue
    def afield(k):
        m = re.search(rf"^\s*(?:-\s*)?{k}: (.+?)\s*(?:#.*)?$", block, re.M)
        return m.group(1).strip().strip("'\"") if m else None
    aid, atitle, aorg, adate, tags_line = afield("id"), afield("title"), afield("org"), afield("date"), re.search(r"^  tags: \[(.*)\]\s*$", block, re.M)
    akind = afield("kind") or "appearance"
    if not atitle or not tags_line:
        continue
    full_title = f"{aorg} — {atitle}" if aorg else atitle
    for tag in (x.strip() for x in tags_line.group(1).split(",")):
        if tag and tag in vocab:
            index[tag].append(("speaking.html", aid or "", full_title, akind, adate or "2026"))

missing = sorted(seen - set(projects))
if missing:
    sys.exit("projects in the pages with no entry in data/TAGS.yaml:\n  " + "\n  ".join(missing))

# ---- the index page --------------------------------------------------------

facets = defaultdict(list)
for tag, facet in vocab.items():
    if tag in index:
        facets[facet].append(tag)


# Build category order dynamically from kinds_meta
category_order_map = {}
for k, meta in kinds_meta.items():
    cat = meta.get("category", k.title())
    order = meta.get("order", 99)
    if cat not in category_order_map or order < category_order_map[cat]:
        category_order_map[cat] = order

CATEGORY_ORDER = sorted(category_order_map.keys(), key=lambda c: category_order_map[c])


def entries(items):
    groups = defaultdict(list)
    for pg, pid, title, kind, date_val in items:
        cat_meta = kinds_meta.get(kind, {})
        cat = cat_meta.get("category", kind.title())
        groups[cat].append((pg, pid, title, kind, date_val))

    out = []
    for cat in CATEGORY_ORDER:
        if cat in groups:
            # Sort items chronologically newest to oldest
            group_items = sorted(groups[cat], key=lambda e: (str(e[4]), e[2].lower()), reverse=True)
            item_html = "\n".join(
                f'      <li><span class="what"><a href="{pg}#{pid}">{html.escape(title)}</a></span></li>'
                for pg, pid, title, kind, date_val in group_items
            )
            out.append(
                f'  <div class="tag-subgroup">\n'
                f'    <div class="tag-subheading">{cat}</div>\n'
                f'    <ol class="tag-list">\n{item_html}\n    </ol>\n'
                f'  </div>'
            )
    return "\n".join(out)



total = sum(len(v) for v in index.values())

# Order facets dynamically from facets_meta
facet_order_list = sorted(facets_meta.keys(), key=lambda f: facets_meta[f].get("order", 99))
present = [f for f in facet_order_list if f in facets] + [f for f in facets if f not in facet_order_list]


def alphabetical_sort(tag):
    """Alphabetical sorting A-Z for index scanning."""
    return tag.lower()


def facet_html(facet):
    out = []
    for tag in sorted(facets[facet], key=alphabetical_sort):
        items = index[tag]
        out.append(
            f'  <h3 id="{slug(tag)}">{html.escape(tag)}'
            f' <span class="tag-count">{len(items)}</span></h3>\n'
            f'{entries(items)}\n'
            f'  <p class="toterms"><a href="#terms-{facet}">&uarr; Terms</a></p>'
        )
    return "\n\n".join(out)


def chiprow(facet):
    chips = "".join(
        f'<a class="chip" href="#{slug(tag)}">{html.escape(tag)}'
        f'<b>{len(index[tag])}</b></a>'
        for tag in sorted(facets[facet], key=alphabetical_sort)
    )
    return f'  <div class="chiprow" id="terms-{facet}">{chips}</div>'


sections = "\n".join(
    f"""<section><div class="wrap">
  <h2 id="{f}">{facets_meta.get(f, {}).get('label', f.title())}</h2>
  <p class="lede">{facets_meta.get(f, {}).get('note', '')} {len(facets[f])} terms.</p>

{chiprow(f)}

{facet_html(f)}

  <p class="totop"><a href="#top">&uarr; Top</a></p>
</div></section>"""
    for f in present
)
subnav = "\n".join(f'  <a href="#{f}">{facets_meta.get(f, {}).get("label", f.title())}</a>' for f in present)


doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(AUTHOR)} &mdash; Index</title>
<meta name="description" content="Every tag used on this site, and all the work it points to.">
<link rel="icon" type="image/x-icon" href="assets/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="assets/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png">
<meta property="og:site_name" content="{html.escape(SITE_TITLE)}">
<meta property="og:type" content="website">
<meta property="og:title" content="Index &mdash; {html.escape(AUTHOR)}">
<meta property="og:description" content="Every tag used on this site, and all the work it points to. Categorized taxonomy by discipline, method, and technology.">
<meta property="og:image" content="{html.escape(SITE_IMAGE)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Index &mdash; {html.escape(AUTHOR)}">
<meta name="twitter:description" content="Every tag used on this site, and all the work it points to. Categorized taxonomy by discipline, method, and technology.">
<meta name="twitter:image" content="{html.escape(SITE_IMAGE)}">
<link rel="stylesheet" href="style.css"></head><body>
<!-- Generated by tools/build_tags.py from data/TAGS.yaml. Do not edit by hand. -->
<nav class="topnav"><div class="wrap">
  <a class="brand" href="index.html">{html.escape(AUTHOR)}</a>
  <span class="navlinks">
    <a href="work.html">Work</a>
    <a href="teaching.html">Teaching</a>
    <a href="speaking.html">Speaking</a>
    <a href="writing.html">Writing</a>
    <a href="tags.html" class="here">Index</a>
    <a href="contact.html">Contact</a>
  </span>
</div></nav>
<nav class="subnav" id="top"><div class="wrap">
{subnav}
</div></nav>

<section><div class="wrap">
  <p class="lede">{len(index)} terms, {total} links to the work carrying them. The number on a
  term is how many pieces of work it points to.</p>
</div></section>

{sections}

<footer><div class="wrap"><span>&copy; 2025&ndash;2026 {html.escape(AUTHOR)} &middot; <a href="{html.escape(LICENSE_URL)}" rel="license">{html.escape(LICENSE_LABEL)}</a> &middot; <a href="contact.html">Contact</a></span></div></footer>
</body></html>
"""

(ROOT / "tags.html").write_text(doc)
print(f"tags.html: {len(index)} tags across {len(projects)} projects, {total} links")
for facet in present:
    print(f"  {facet:12} {len(facets[facet])} tags")
