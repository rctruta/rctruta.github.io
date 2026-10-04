"""Generate work.html from data/work.yaml.

    python3 tools/build_work.py
"""
import html
import pathlib
from model import load_taxonomy, load_work_sections
from page import render_project_card, render_page_shell, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent

vocab = load_taxonomy()
sections = load_work_sections(vocab)

subnav_links = []
sections_html = []

for sec in sections:
    subnav_links.append(f'  <a href="#{sec.id}">{html.escape(sec.title.split("&")[0].strip())}</a>')
    cards_html = "\n".join(render_project_card(item) for item in sec.items)

    sections_html.append(
        f'<section><div class="wrap">\n'
        f'  <h2 id="{sec.id}">{html.escape(sec.title)}</h2>\n'
        f'  <p class="sub small cat-note">{html.escape(sec.summary)}</p>\n'
        f'{cards_html}\n'
        f'  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        f'</div></section>'
    )

subnav_html = "\n".join(subnav_links)
body_html = "\n".join(sections_html)

title = f"{AUTHOR} — Work"
description = "Database benchmarking, AI security, agent evaluation, system integrity, and retrieval accuracy. Every claim with the experiment attached."

doc = render_page_shell(
    title=title,
    description=description,
    here_page="work",
    subnav_html=subnav_html,
    body_html=body_html,
    generator_name="build_work.py",
    source_yaml="work.yaml"
)

(ROOT / "work.html").write_text(doc, encoding="utf-8")
print(f"work.html: {len(sections)} sections across {sum(len(s.items) for s in sections)} projects generated.")
