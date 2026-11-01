"""Generate speaking.html from data/appearances.yaml using Jinja2 templates."""
import pathlib
from model import load_taxonomy, load_appearances
from contracts import content_document, published
from page import render_template, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent

entries = load_appearances(load_taxonomy())

def note_for(key: str) -> str:
    return content_document('appearances')[key]


talks = [e for e in entries if e.kind == "talk"]
podcasts = [e for e in entries if e.kind == "podcast" and published(e.model_dump())]
shows = sorted({e.org for e in podcasts})

as_host = [e for e in podcasts if e.role == "guest host"]
as_guest = [e for e in podcasts if e.role != "guest host"]

subnav_html = "\n".join([
    '  <a href="#talks">Talks</a>',
    '  <a href="#podcasts">Podcasts</a>',
])

doc = render_template(
    template_name="speaking.html",
    title=f"{AUTHOR} — Speaking",
    here_page="speaking",
    generator_name="build_speaking.py",
    source_yaml="appearances.yaml",
    subnav_html=subnav_html,
    talks=talks,
    podcasts=podcasts,
    as_host=as_host,
    as_guest=as_guest,
    shows=shows,
    guest_host_note=note_for("guest_host_note"),
)

(ROOT / "speaking.html").write_text(doc, encoding="utf-8")
print(f"speaking.html: {len(talks)} talks, {len(podcasts)} episodes "
      f"({len(as_host)} as guest host), {len(shows)} shows")
