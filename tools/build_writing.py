"""Generate writing.html from data/writing.yaml using Jinja2 templates.

    python3 tools/build_writing.py
"""
import pathlib
from model import load_taxonomy, load_articles
from page import render_template, AUTHOR, SUBSTACK_RSS

ROOT = pathlib.Path(__file__).resolve().parent.parent

vocab = load_taxonomy()
articles = load_articles(vocab)
years = sorted({a.date[:4] for a in articles}, reverse=True)

subnav_html = "\n".join(f'  <a href="#y{y}">{y}</a>' for y in years)
extra_head = f'\n<link rel="alternate" type="application/rss+xml" title="{AUTHOR} &mdash; Substack Feed" href="{SUBSTACK_RSS}">'

doc = render_template(
    template_name="writing.html",
    title=f"{AUTHOR} — Writing",
    here_page="writing",
    generator_name="build_writing.py",
    source_yaml="writing.yaml",
    subnav_html=subnav_html,
    extra_head=extra_head,
    articles=articles,
    years=years
)

(ROOT / "writing.html").write_text(doc, encoding="utf-8")
print(f"writing.html: {len(articles)} pieces, {years[-1]}-{years[0]}")
