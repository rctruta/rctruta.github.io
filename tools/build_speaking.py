"""Generate speaking.html from data/appearances.yaml using Jinja2 templates.

    python3 tools/build_speaking.py
"""
import pathlib
from model import load_taxonomy, load_appearances
from page import render_template, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent

entries = load_appearances(load_taxonomy())
PAGE_NOTE = (ROOT / "data" / "appearances.yaml").read_text(encoding="utf-8")


def note_for(key: str) -> str:
    import re
    m = re.search(rf'^{key}: "(.*)"\s*$', PAGE_NOTE, re.M)
    if not m:
        raise KeyError(f"data/appearances.yaml is missing the page note '{key}'")
    return m.group(1)


talks = [e for e in entries if e.kind == "talk"]
podcasts = [e for e in entries if e.kind == "podcast" and e.url]
shows = sorted({e.org for e in podcasts})

# Guest hosting is work of a different kind from being a guest, and the people
# interviewed are credited by name. Splitting here rather than in the template
# so the test can assert both lists reach the page.
as_host = [e for e in podcasts if e.role == "guest host"]
as_guest = [e for e in podcasts if e.role != "guest host"]

subnav_html = "\n".join([
    '  <a href="#talks">Talks</a>',
    '  <a href="#podcasts">Podcasts</a>',
])
# "As guest host" and "As guest" are subdivisions of Podcasts, not peers of it.
# They stay as headings with their anchors, so a deep link still resolves, but
# a flat sub-nav of four made two levels look like one.

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
