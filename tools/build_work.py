"""Generate work.html from data/work.yaml using Jinja2 templates."""
import pathlib
from model import load_taxonomy, load_work_sections
from page import render_template, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent

vocab = load_taxonomy()
sections = load_work_sections(vocab)

doc = render_template(
    template_name="work.html",
    title=f"{AUTHOR} — Work",
    here_page="work",
    generator_name="build_work.py",
    source_yaml="work.yaml",
    subnav_html=None,
    sections=sections
)

(ROOT / "work.html").write_text(doc, encoding="utf-8")
print(f"work.html: {len(sections)} sections across {sum(len(s.items) for s in sections)} projects generated.")
