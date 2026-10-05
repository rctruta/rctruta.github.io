"""Generate index.html from data/home.yaml, config.yaml, work.yaml and teaching.yaml.

    python3 tools/build_index.py

The home page was hand-written, so nothing propagated into it. The link list
and its descriptions now come from config.yaml (the same string each page shows
as its own lede), the social links from config.yaml, the disciplines in the
structured data from the section titles in work.yaml, and the number of
testimonials from teaching.yaml.
"""
import html
import json
import re
import pathlib
from config_loader import load_config
from model import load_taxonomy, load_work_sections, load_home, count_testimonials
from page import render_page_shell, format_inline, AUTHOR, SITE_URL, SITE_IMAGE
from bio import as_html as bio_as_html

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = load_config()
A = CONFIG["site"]["author"]

# path data for the icons, keyed by the config.yaml field holding the address
ICONS = {
    "linkedin": ("LinkedIn", "fill",
                 "M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.13 1.45-2.13 2.94v5.67H9.35V9h3.41v1.56h.05a3.74 3.74 0 0 1 3.37-1.85c3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.07 2.07 0 1 1 0-4.14 2.07 2.07 0 0 1 0 4.14zm1.78 13.02H3.55V9h3.57v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0z"),
    "github": ("GitHub", "fill",
               "M12 .3a12 12 0 0 0-3.79 23.4c.6.11.82-.26.82-.58l-.01-2.04c-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.83 2.81 1.3 3.5.99.11-.78.42-1.31.76-1.61-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.11-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 6.01 0c2.29-1.55 3.3-1.23 3.3-1.23.65 1.66.24 2.88.12 3.18.77.84 1.23 1.91 1.23 3.22 0 4.61-2.8 5.62-5.48 5.92.43.37.81 1.1.81 2.22l-.01 3.29c0 .32.21.7.82.58A12 12 0 0 0 12 .3"),
    "substack": ("Substack", "fill",
                 "M22.539 8.242H1.46V5.406h21.08v2.836zM1.46 10.812V24L12 18.11 22.54 24V10.812H1.46zM22.54 0H1.46v2.836h21.08V0z"),
}
# the two that point inside the site or need a stroke outline
MAIL_ICON = '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 7L2 7"/>'
CAL_ICON = '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>'

vocab = load_taxonomy()
home = load_home()
sections = load_work_sections(vocab)




def address(key: str) -> str:
    url = (A.get(key) or "").strip()
    if not url:
        raise KeyError(f"site.author.{key} is missing from config.yaml but index.html links to it")
    return url


social = []
for key, (label, _, path) in ICONS.items():
    social.append(
        f'    <a href="{address(key)}" target="_blank" rel="noopener" aria-label="{label}" title="{label}">\n'
        f'      <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="{path}"/></svg></a>'
    )
social.append(
    '    <a href="contact.html#form" aria-label="Send a message" title="Send a message">\n'
    f'      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2">{MAIL_ICON}</svg></a>'
)
social.append(
    f'    <a href="{address("calendly")}" target="_blank" rel="noopener" aria-label="Book a call" title="Book a 30-minute call">\n'
    f'      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2">{CAL_ICON}</svg></a>'
)
social_html = "\n".join(social)

# One line per navigation entry, carrying the same description that page shows
# as its own lede.
links_html = "\n".join(
    f'    <li><span class="what"><a href="{nav["href"]}"><strong>{html.escape(nav["label"])}</strong></a> '
    f'&mdash; {html.escape(nav["description"])}</span></li>'
    for nav in CONFIG["navigation"]
)

p = home.praise
praise_html = (
    f'  <blockquote class="praise">\n'
    f'    <p>&ldquo;{format_inline(p.quote)}&rdquo;</p>\n'
    f'    <cite><a href="{p.author_url}" target="_blank" rel="noopener">{html.escape(p.author)}</a>, '
    f'{html.escape(p.source)} &mdash; <em><a href="{p.work_url}" target="_blank" rel="noopener">'
    f'{html.escape(p.work)}</a></em></cite>\n'
    f'  </blockquote>'
)

body_html = f"""<header id="top"><div class="wrap"><div class="hero"><div class="hero-text">
  <h1>{html.escape(AUTHOR)}</h1>
  <p class="sub">{bio_as_html(home.bio)} {format_inline(home.site_note)}</p>
  </div><div class="portrait-col"><img class="portrait" src="assets/photo.jpg" alt="{html.escape(home.portrait_alt)}">
  <div class="social">
{social_html}
  </div>
</div></div></div></header>

<section><div class="wrap">
{praise_html}
  <p class="subtext" style="margin-top: -18px; margin-bottom: 30px; font-size: 15px;"><a href="teaching.html#testimonials">{count_testimonials()} {html.escape(home.testimonials_link)} &rarr;</a></p>

  <ul class="clean">
{links_html}
  </ul>
</div></section>"""

structured_data = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": AUTHOR,
    "url": SITE_URL,
    "image": SITE_IMAGE,
    "sameAs": [address("linkedin"), address("github"), address("substack"), address("orcid")],
    "jobTitle": home.job_title,
    # the disciplines are the work.yaml section titles, so adding a section
    # adds it here too
    "knowsAbout": [s.title for s in sections],
}

extra_head = (
    f'\n<meta name="google-site-verification" content="{html.escape(home.google_site_verification)}">'
    f'\n<script type="application/ld+json">\n{json.dumps(structured_data, indent=2)}\n</script>'
)

doc = render_page_shell(
    title=AUTHOR,
    here_page="index",
    description=home.description,
    subnav_html="",
    body_html=body_html,
    generator_name="build_index.py",
    source_yaml="home.yaml",
    extra_head=extra_head,
)

(ROOT / "index.html").write_text(doc, encoding="utf-8")
print(f"index.html: {len(CONFIG['navigation'])} links, {count_testimonials()} testimonials, "
      f"{len(sections)} disciplines in structured data.")
