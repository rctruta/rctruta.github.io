"""Generate speaking.html from data/appearances.yaml.

    python3 tools/build_speaking.py

This was the one generator written in Node, from before the site was rebuilt
around data/ and tools/. It carried its own YAML parser, its own HTML escaper,
its own page shell and its own hardcoded navigation, so it sat outside every
guarantee the other pages have — build_nav.py had to repair its nav and its
meta descriptions on every build. It also read `url`, `counterpart` and `note`,
three fields the pydantic model did not have, so anything else reading the data
through the model could not see them.

Visibility is derived, not stored: a talk always renders, a podcast renders
once it has a `url`. There is no status field to go stale.
"""
import html
import pathlib
from model import load_taxonomy, load_appearances
from page import render_page_shell, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

entries = load_appearances(load_taxonomy())
PAGE_NOTE = (ROOT / "data" / "appearances.yaml").read_text()


def note_for(key: str) -> str:
    """A line of her prose that belongs to the page, kept with the data."""
    import re
    m = re.search(rf'^{key}: "(.*)"\s*$', PAGE_NOTE, re.M)
    if not m:
        raise KeyError(f"data/appearances.yaml is missing the page note '{key}'")
    return m.group(1)


def when(d: str) -> str:
    y, m, day = (int(x) for x in d.split("-"))
    return f"{MONTHS[m - 1]} {day}, {y}"


def title_html(e):
    if e.url:
        return f'<a href="{html.escape(e.url)}" target="_blank" rel="noopener">{html.escape(e.title)}</a>'
    return f"<em>{html.escape(e.title)}</em>"


def row(e, trailing=""):
    where = f", {html.escape(e.location)}" if e.location and e.location != "virtual" else ""
    return (f'    <li id="{html.escape(e.id)}"><span class="when">{when(e.date)}</span>'
            f'<span class="what"><strong>{html.escape(e.org)}</strong>{where}'
            f' &mdash; {title_html(e)}{trailing}</span></li>')


def listing(rows):
    return '<ul class="clean">\n' + "\n".join(rows) + "\n  </ul>"


talks = [e for e in entries if e.kind == "talk"]
pods = [e for e in entries if e.kind == "podcast" and e.url]
as_host = [e for e in pods if e.role == "guest host"]
as_guest = [e for e in pods if e.role != "guest host"]
shows = len({e.org for e in pods})

host_note = lambda e: f" <em>(interviewing {html.escape(e.counterpart)})</em>" if e.counterpart else ""
co_note = lambda e: " <em>(co-host)</em>" if e.role == "co-host" else ""

body_html = f"""<section id="talks"><div class="wrap"><h2>Talks</h2>{listing([row(e) for e in talks])}
  <p class="totop"><a href="#top">&uarr; Top</a></p>
</div></section>
<section id="podcasts"><div class="wrap"><h2>Podcasts</h2>
  <p class="lede">{len(pods)} episodes across {shows} shows.</p>
  <h3 id="guest-host">As guest host</h3>
  <p class="lede">{html.escape(note_for("guest_host_note"))}</p>
  {listing([row(e, host_note(e)) for e in as_host])}
  <h3 id="as-guest">As guest</h3>{listing([row(e, co_note(e)) for e in as_guest])}
  <p class="totop"><a href="#top">&uarr; Top</a></p>
</div></section>"""

subnav_html = "\n".join([
    '  <a href="#talks">Talks</a>',
    '  <a href="#podcasts">Podcasts</a>',
    '  <a href="#guest-host">As guest host</a>',
    '  <a href="#as-guest">As guest</a>',
])

doc = render_page_shell(
    title=f"{AUTHOR} — Speaking",
    here_page="speaking",
    subnav_html=subnav_html,
    body_html=body_html,
    generator_name="build_speaking.py",
    source_yaml="appearances.yaml",
)

(ROOT / "speaking.html").write_text(doc, encoding="utf-8")
print(f"speaking.html: {len(talks)} talks, {len(pods)} episodes, {shows} shows")
