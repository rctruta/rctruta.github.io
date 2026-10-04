"""Generate writing.html from data/writing.yaml.

    python3 tools/build_writing.py
"""
import html
import pathlib
from model import load_taxonomy, load_articles
from page import render_tag_chips, render_page_shell, AUTHOR, SUBSTACK_URL, SUBSTACK_RSS

ROOT = pathlib.Path(__file__).resolve().parent.parent

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def when(d: str) -> str:
    y, m, _ = d.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


vocab = load_taxonomy()
articles = load_articles(vocab)


def render_article_card(a) -> str:
    tags_html = render_tag_chips(a.tags)
    return (
        f'  <div class="proj" id="{a.id}">\n'
        f'    <h3><a href="{a.url}" target="_blank" rel="noopener">{html.escape(a.title)}</a>\n'
        f'    <span class="meta">{html.escape(a.platform)} &middot; {when(a.date)}</span></h3>\n'
        f'    <p>{html.escape(a.argues)}</p>\n'
        f'    {tags_html}\n'
        f'  </div>'
    )


years = sorted({a.date[:4] for a in articles}, reverse=True)
body_parts = [
    f'  <p class="lede">{len(articles)} pieces. Each one makes a claim I would defend, and links to the work behind it where there is work behind it.</p>'
]

for y in years:
    body_parts.append(f'  <h2 id="y{y}">{y}</h2>')
    body_parts.extend(render_article_card(a) for a in articles if a.date.startswith(y))
    body_parts.append('  <p class="totop"><a href="#top">&uarr; Top</a></p>')

body_parts.append(
    f'  <div class="contact-card" style="margin-top: 36px;">\n'
    f'    <div>\n'
    f'      <h3>Subscribe to my Substack</h3>\n'
    f'      <p style="margin-top: 6px;">Read full essays and research notes on database performance, benchmarking, and AI evaluation on Substack.</p>\n'
    f'    </div>\n'
    f'    <div>\n'
    f'      <a class="btn solid" href="{html.escape(SUBSTACK_URL)}" target="_blank" rel="noopener">Subscribe on Substack &rarr;</a>\n'
    f'    </div>\n'
    f'  </div>'
)

subnav_html = "\n".join(f'  <a href="#y{y}">{y}</a>' for y in years)
body_html = (
    f'<section><div class="wrap">\n'
    f'{chr(10).join(body_parts)}\n'
    f'</div></section>'
)

extra_head = f'\n<link rel="alternate" type="application/rss+xml" title="{html.escape(AUTHOR)} &mdash; Substack Feed" href="{html.escape(SUBSTACK_RSS)}">'

title = f"{AUTHOR} — Writing"
description = "Essays on data modeling, AI evaluation, security and the people using these systems. Each piece published with its repository."

doc = render_page_shell(
    title=title,
    description=description,
    here_page="writing",
    subnav_html=subnav_html,
    body_html=body_html,
    generator_name="build_writing.py",
    source_yaml="writing.yaml",
    extra_head=extra_head
)

(ROOT / "writing.html").write_text(doc, encoding="utf-8")
print(f"writing.html: {len(articles)} pieces, {years[-1]}-{years[0]}")
