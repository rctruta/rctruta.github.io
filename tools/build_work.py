"""Generate work.html from data/work.yaml using Jinja2 templates."""
import pathlib
import re
from model import load_taxonomy, load_upstream_issues, load_work_sections
from page import render_template, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent

vocab = load_taxonomy()
sections = load_work_sections(vocab)
upstream_issues = load_upstream_issues()
work_short_titles = {item.id: item.short_title for sec in sections for item in sec.items}
section_tips = {
    sec.id: re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", sec.summary).strip()
    for sec in sections
}

doc = render_template(
    template_name="work.html",
    title=f"{AUTHOR} — Work",
    here_page="work",
    generator_name="build_work.py",
    source_yaml="work.yaml",
    subnav_html=None,
    sections=sections,
    upstream_issues=upstream_issues,
    work_short_titles=work_short_titles,
    section_tips=section_tips
)

(ROOT / "work.html").write_text(doc, encoding="utf-8")
print(
    f"work.html: {len(sections)} sections across {sum(len(s.items) for s in sections)} projects"
    f" and {len(upstream_issues)} upstream issues generated."
)
