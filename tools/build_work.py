"""Generate work.html from data/work.yaml using Jinja2 templates.

    python3 tools/build_work.py
"""
import html
import pathlib
from model import load_taxonomy, load_work_sections
from page import render_template, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent

vocab = load_taxonomy()
sections = load_work_sections(vocab)

subnav_links = [f'  <a href="#{sec.id}">{html.escape(sec.title.split("&")[0].strip())}</a>' for sec in sections]
subnav_html = "\n".join(subnav_links)

doc = render_template(
    template_name="work.html",
    title=f"{AUTHOR} — Work",
    here_page="work",
    generator_name="build_work.py",
    source_yaml="work.yaml",
    subnav_html=subnav_html,
    sections=sections
)

(ROOT / "work.html").write_text(doc, encoding="utf-8")
print(f"work.html: {len(sections)} sections across {sum(len(s.items) for s in sections)} projects generated.")
