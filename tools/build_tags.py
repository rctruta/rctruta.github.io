"""Generate tags.html from data/TAGS.yaml and all content models using Jinja2 templates."""
import html
import pathlib
from collections import defaultdict
from model import load_taxonomy
from contracts import index_records, taxonomy_document
from page import render_template, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent

vocab_model = load_taxonomy()
facets_meta = vocab_model.facets
kinds_meta = vocab_model.kinds
vocab = vocab_model.vocabulary

index = defaultdict(list)

taxonomy = taxonomy_document()
for record in index_records():
    for cid in record['tags']:
        label = taxonomy['concepts'][cid]['label']
        index[label].append((record['page'], record['id'], record['title'], record['kind'], record['date']))

category_order_map = {}
for meta in kinds_meta.values():
    cat = meta.category
    order = meta.order
    if cat not in category_order_map or order < category_order_map[cat]:
        category_order_map[cat] = order

CATEGORY_ORDER = sorted(category_order_map.keys(), key=lambda c: category_order_map[c])


def entries(items):
    groups = defaultdict(list)
    for pg, pid, title, kind, date_val in items:
        cat = kinds_meta[kind].category
        groups[cat].append((pg, pid, title, kind, date_val))

    out = []
    for cat in CATEGORY_ORDER:
        if cat in groups:
            group_items = groups[cat]
            if cat in {"Writing", "Speaking"}:
                group_items = sorted(group_items, key=lambda e: e[4], reverse=True)
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
        note = vocab_model.notes.get(tag, "")
        note_html = f'  <p class="scope-note">{html.escape(note)}</p>\n' if note else ""
        syns = vocab_model.synonyms.get(tag, [])
        search_terms = vocab_model.search_terms.get(tag, [])
        syn_html = (f'  <p class="entry-terms">Also called '
                    f'{html.escape(", ".join(syns))}.</p>\n') if syns else ""
        if search_terms:
            syn_html += f'  <p class="entry-terms">Search terms: {html.escape(", ".join(search_terms))}.</p>\n'
        out.append(
            f'  <h3 id="{vocab_model.anchors[tag]}">{html.escape(tag)}'
            f' <span class="tag-count">{len(items)}</span></h3>\n'
            f'{note_html}{syn_html}'
            f'{entries(items)}\n'
            f'  <p class="toterms"><a href="#terms-{facet}">&uarr; Terms</a></p>'
        )
    return "\n\n".join(out)


def chiprow(facet):
    chips = "".join(
        f'<a class="chip" href="#{vocab_model.anchors[tag]}">{html.escape(tag)}'
        f'<b>{len(index[tag])}</b></a>'
        for tag in sorted(facets[facet], key=alphabetical_sort)
    )
    return f'  <div class="chiprow" id="terms-{facet}">{chips}</div>'


sections = "\n".join(
    f"""<section><div class="wrap">
  <h2 id="{f}">{facets_meta[f].label}</h2>
  <p class="lede">{facets_meta[f].note} {len(facets[f])} terms.</p>

{chiprow(f)}

{facet_html(f)}

  <p class="totop"><a href="#top">&uarr; Top</a></p>
</div></section>"""
    for f in present
)

subnav_html = "\n".join(f'  <a href="#{f}">{facets_meta[f].label}</a>' for f in present)

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
