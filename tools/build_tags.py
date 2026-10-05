"""Generate tags.html from data/TAGS.yaml and all content models using Jinja2 templates.

    python3 tools/build_tags.py
"""
import html
import pathlib
import re
from collections import defaultdict
from model import load_taxonomy, load_work_sections, load_articles, load_appearances
from page import render_template, slug, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent

vocab_model = load_taxonomy()
facets_meta = vocab_model.facets
kinds_meta = vocab_model.kinds
vocab = vocab_model.vocabulary

index = defaultdict(list)

# 1. Index Work Projects
work_sections = load_work_sections(vocab_model)
for sec in work_sections:
    for item in sec.items:
        date_str = item.date_val
        for t in item.tags:
            index[t].append(("work.html", item.id, item.title, "project", date_str))

# 2. Index Teaching Items
teaching_yaml_path = ROOT / "data" / "teaching.yaml"
if teaching_yaml_path.exists():
    text = teaching_yaml_path.read_text(encoding="utf-8")
    for block in re.split(r"\n(?=\s*- id:|\n\w+:)", text):
        m_id = re.search(r"id:\s*([\w-]+)", block)
        m_title = re.search(r'title:\s*"(.*?)"', block)
        m_tags = re.search(r"tags:\s*\[(.*?)\]", block)
        if m_id and m_title and m_tags:
            pid = m_id.group(1)
            title = m_title.group(1)
            tags = [t.strip() for t in m_tags.group(1).split(",") if t.strip()]
            kind = "course material" if "assets/" in block or "assignment" in pid or "handout" in pid else "teaching"
            for t in tags:
                if t in vocab:
                    index[t].append(("teaching.html", pid, title, kind, "2026"))

# 3. Index Articles
articles = load_articles(vocab_model)
for a in articles:
    for t in a.tags:
        index[t].append(("writing.html", a.id, a.title, "article", a.date))

# 4. Index Appearances
appearances = load_appearances(vocab_model)
for app in appearances:
    full_title = f"{app.org} — {app.title}" if app.org else app.title
    for t in app.tags:
        index[t].append(("speaking.html", app.id, full_title, app.kind, app.date))


# Category ordering from kinds_meta
category_order_map = {}
for k, meta in kinds_meta.items():
    cat = meta.category
    order = meta.order
    if cat not in category_order_map or order < category_order_map[cat]:
        category_order_map[cat] = order

CATEGORY_ORDER = sorted(category_order_map.keys(), key=lambda c: category_order_map[c])


def entries(items):
    groups = defaultdict(list)
    for pg, pid, title, kind, date_val in items:
        cat_meta = kinds_meta.get(kind, None)
        cat = cat_meta.category if cat_meta else kind.title()
        groups[cat].append((pg, pid, title, kind, date_val))

    out = []
    for cat in CATEGORY_ORDER:
        if cat in groups:
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


facets = defaultdict(list)
for tag, facet in vocab.items():
    if tag in index:
        facets[facet].append(tag)

total = sum(len(v) for v in index.values())
facet_order_list = sorted(facets_meta.keys(), key=lambda f: facets_meta[f].order)
present = [f for f in facet_order_list if f in facets] + [f for f in facets if f not in facet_order_list]


def alphabetical_sort(tag):
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
  <h2 id="{f}">{facets_meta.get(f, None).label if f in facets_meta else f.title()}</h2>
  <p class="lede">{facets_meta.get(f, None).note if f in facets_meta else ''} {len(facets[f])} terms.</p>

{chiprow(f)}

{facet_html(f)}

  <p class="totop"><a href="#top">&uarr; Top</a></p>
</div></section>"""
    for f in present
)

subnav_html = "\n".join(f'  <a href="#{f}">{facets_meta.get(f, None).label if f in facets_meta else f.title()}</a>' for f in present)

doc = render_template(
    template_name="tags.html",
    title=f"{AUTHOR} — Index",
    here_page="tags",
    generator_name="build_tags.py",
    source_yaml="TAGS.yaml",
    subnav_html=subnav_html,
    index_len=len(index),
    total_links=total,
    sections_html=sections
)

(ROOT / "tags.html").write_text(doc, encoding="utf-8")
print(f"tags.html: {len(index)} tags across {total} links")
for facet in present:
    print(f"  {facet:12} {len(facets[facet])} tags")
