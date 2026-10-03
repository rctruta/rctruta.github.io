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

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ["work.html", "teaching.html"]
SPEC = ROOT / "data" / "TAGS.yaml"


def parse_tags_yaml(text):
    """Minimal reader for this file's shape — no third-party dependency."""
    vocab, projects, section, facet = {}, {}, None, None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        if indent == 0 and line.endswith(":"):
            section = line[:-1]
            continue
        if section == "vocabulary":
            if indent == 2 and line.endswith(":"):
                facet = line[:-1]
                continue
            if indent == 4:
                term = line.split(":", 1)[0].strip()
                vocab[term] = facet
        elif section == "projects" and indent == 2:
            pid, rest = line.split(":", 1)
            projects[pid.strip()] = [
                t.strip() for t in rest.strip().strip("[]").split(",") if t.strip()
            ]
    return vocab, projects


vocab, projects = parse_tags_yaml(SPEC.read_text())

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
        # the metadata span describes the file, not the work — keep it out of the title
        raw = re.sub(r'<span class="meta">.*?</span>', "", raw, flags=re.S)
        title = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        title = re.sub(r"\s+", " ", title).strip()
        # the kind is in the data; a reader should not have to guess it
        if name == "teaching.html":
            kind = "course material" if "assets/" in (heading.group(1) if heading else "") else "teaching"
        else:
            kind = "project"
        for t in projects[pid]:
            index[t].append((name, pid, title, kind))
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
    wid, title, tags_line = field("id"), field("title"), re.search(r"^  tags: \[(.*)\]\s*$", block, re.M)
    if not title or not tags_line:
        continue
    for tag in (x.strip() for x in tags_line.group(1).split(",")):
        if tag and tag in vocab:
            index[tag].append(("writing.html", wid or "", title, "article"))

# speaking appearances live in appearances.yaml — index them from the source
atext = (ROOT / "data" / "appearances.yaml").read_text()
for block in re.split(r"\n(?=- id:)", atext):
    if not block.lstrip().startswith("- id:"):
        continue
    def afield(k):
        m = re.search(rf"^\s*(?:-\s*)?{k}: (.+?)\s*(?:#.*)?$", block, re.M)
        return m.group(1).strip().strip("'\"") if m else None
    aid, atitle, aorg, tags_line = afield("id"), afield("title"), afield("org"), re.search(r"^  tags: \[(.*)\]\s*$", block, re.M)
    akind = afield("kind") or "appearance"
    if not atitle or not tags_line:
        continue
    full_title = f"{aorg} — {atitle}" if aorg else atitle
    for tag in (x.strip() for x in tags_line.group(1).split(",")):
        if tag and tag in vocab:
            index[tag].append(("speaking.html", aid or "", full_title, akind))

missing = sorted(seen - set(projects))
if missing:
    sys.exit("projects in the pages with no entry in data/TAGS.yaml:\n  " + "\n  ".join(missing))

# ---- the index page --------------------------------------------------------

facets = defaultdict(list)
for tag, facet in vocab.items():
    if tag in index:
        facets[facet].append(tag)


CATEGORY_MAP = {
    "project": "Projects",
    "article": "Writing",
    "talk": "Speaking",
    "podcast": "Speaking",
    "teaching": "Teaching",
    "course material": "Teaching",
}
CATEGORY_ORDER = ["Projects", "Writing", "Speaking", "Teaching"]


def entries(items):
    groups = defaultdict(list)
    for pg, pid, title, kind in items:
        cat = CATEGORY_MAP.get(kind, "Other")
        groups[cat].append((pg, pid, title, kind))

    out = []
    for cat in CATEGORY_ORDER:
        if cat in groups:
            group_items = sorted(groups[cat], key=lambda e: e[2].lower())
            item_html = "\n".join(
                f'      <li><span class="what"><a href="{pg}#{pid}">{html.escape(title)}</a></span></li>'
                for pg, pid, title, kind in group_items
            )
            out.append(
                f'  <div class="tag-subgroup">\n'
                f'    <div class="tag-subheading">{cat}</div>\n'
                f'    <ul class="clean">\n{item_html}\n    </ul>\n'
                f'  </div>'
            )
    return "\n".join(out)


def facet_html(facet):
    out = []
    for tag in sorted(facets[facet], key=str.lower):
        items = index[tag]
        out.append(
            f'  <h3 id="{slug(tag)}">{html.escape(tag)}'
            f' <span class="tag-count">{len(items)}</span></h3>\n'
            f'  <ul class="clean">\n{entries(items)}\n  </ul>'
        )
    return "\n\n".join(out)


total = sum(len(v) for v in index.values())

# One line per facet, read from TAGS.yaml rather than hard-coded, so renaming or
# adding a facet does not touch this file.
FACET_NOTE = {
    "discipline": "What the work is about.",
    "domain": "What the work is about.",
    "practice": "How I work &mdash; with students, with teams, with a reader.",
    "method": "How a claim was established, rather than what it was about.",
    "technology": "What it was built with.",
}
ORDER = ["domain", "discipline", "practice", "method", "technology"]
present = [f for f in ORDER if f in facets] + [f for f in facets if f not in ORDER]


def by_weight(tag):
    """Heaviest first; ties alphabetical so the order is stable between builds."""
    return (-len(index[tag]), tag.lower())


def facet_html(facet):
    out = []
    for tag in sorted(facets[facet], key=by_weight):
        items = index[tag]
        out.append(
            f'  <h3 id="{slug(tag)}">{html.escape(tag)}'
            f' <span class="tag-count">{len(items)}</span></h3>\n'
            f'{entries(items)}\n'
            f'  <p class="toterms"><a href="#terms-{facet}">&uarr; Terms</a></p>'
        )
    return "\n\n".join(out)


def chiprow(facet):
    """The facet's own terms as chips, at the head of its section."""
    chips = "".join(
        f'<a class="chip" href="#{slug(tag)}">{html.escape(tag)}'
        f'<b>{len(index[tag])}</b></a>'
        for tag in sorted(facets[facet], key=by_weight)
    )
    return f'  <div class="chiprow" id="terms-{facet}">{chips}</div>'


sections = "\n".join(
    f"""<section><div class="wrap">
  <h2 id="{f}">{f.title()}</h2>
  <p class="lede">{FACET_NOTE.get(f, "")} {len(facets[f])} terms.</p>

{chiprow(f)}

{facet_html(f)}

  <p class="totop"><a href="#top">&uarr; Top</a></p>
</div></section>"""
    for f in present
)
subnav = "\n".join(f'  <a href="#{f}">{f.title()}</a>' for f in present)

doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ramona C. Truta &mdash; Index</title>
<meta name="description" content="Every tag used on this site, and all the work it points to.">
<link rel="icon" type="image/x-icon" href="assets/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="assets/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png">
<meta property="og:site_name" content="Ramona C. Truta">
<meta property="og:type" content="website">
<meta property="og:title" content="Index &mdash; Ramona C. Truta">
<meta property="og:description" content="Every tag used on this site, and all the work it points to. Categorized taxonomy by discipline, method, and technology.">
<meta property="og:image" content="https://ramonactruta.com/assets/photo.jpg">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Index &mdash; Ramona C. Truta">
<meta name="twitter:description" content="Every tag used on this site, and all the work it points to. Categorized taxonomy by discipline, method, and technology.">
<meta name="twitter:image" content="https://ramonactruta.com/assets/photo.jpg">
<link rel="stylesheet" href="style.css"></head><body>
<!-- Generated by tools/build_tags.py from data/TAGS.yaml. Do not edit by hand. -->
<nav class="topnav"><div class="wrap">
  <a class="brand" href="index.html">Ramona C. Truta</a>
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

<footer><div class="wrap"><span>&copy; 2025&ndash;2026 Ramona C. Truta &middot; <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" rel="license">CC BY-NC-SA 4.0</a> &middot; <a href="contact.html">Contact</a></span></div></footer>
</body></html>
"""

(ROOT / "tags.html").write_text(doc)
print(f"tags.html: {len(index)} tags across {len(projects)} projects, {total} links")
for facet in present:
    print(f"  {facet:12} {len(facets[facet])} tags")
