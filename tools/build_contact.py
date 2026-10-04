"""Generate contact.html from data/contact.yaml and config.yaml.

    python3 tools/build_contact.py

The words are in data/contact.yaml; every address (form endpoint, calendar,
Substack, ORCID) is in config.yaml and appears here exactly once. Before this
generator the Formspree endpoint was written in two places, so rotating it in
config.yaml left the live form posting to the old one.
"""
import html
import pathlib
from config_loader import load_config
from model import load_taxonomy, load_contact
from page import render_page_shell, slug, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent
AUTHOR_CFG = load_config()["site"]["author"]


def address(key: str) -> str:
    """A link from config.yaml. Absent or empty is a build failure, not a dead button."""
    url = AUTHOR_CFG.get(key, "").strip()
    if not url:
        raise KeyError(f"site.author.{key} is missing from config.yaml; contact.yaml refers to it")
    return url


contact = load_contact(load_taxonomy())

options = "\n".join(
    f'                <option value="{html.escape(t, quote=True)}"{" selected" if i == 0 else ""}>'
    f'{html.escape(t)}</option>'
    for i, t in enumerate(contact.form.topics)
)

cards_html = "\n\n".join(
    f'      <div class="contact-card">\n'
    f'        <div>\n'
    f'          <h3>{html.escape(c.heading)}</h3>\n'
    f'          <p style="margin-top: 6px;">{html.escape(c.text)}</p>\n'
    f'        </div>\n'
    f'        <div>\n'
    f'          <a class="btn solid" href="{address(c.link)}" target="_blank" rel="noopener">'
    f'{html.escape(c.button)} &rarr;</a>\n'
    f'        </div>\n'
    f'      </div>'
    for c in contact.cards
)

services_html = "\n".join(
    f'      <li><a href="tags.html#{slug(s.tag)}">{html.escape(s.label)}</a>'
    f'{"" if s.continues else " &mdash;"} {html.escape(s.note)}</li>'
    for s in contact.services
)

body_html = f"""<section><div class="wrap">
  <h2>Contact</h2>

  <p class="lede">{html.escape(contact.lede)}</p>

  <div class="contact-grid">
    <div class="form-col">
      <div class="contact-card">
        <div>
          <h3 id="form">{html.escape(contact.form.heading)}</h3>
          <p class="subtext" style="margin-top: 6px; margin-bottom: 16px;">{html.escape(contact.form.intro)}</p>

          <form class="contact-form" action="{address("contact_form")}" method="POST">
            <div class="field-row">
              <div class="field">
                <label for="name">Your Name <span class="req">*</span></label>
                <input type="text" id="name" name="name" placeholder="Ada Lovelace" required>
              </div>
              <div class="field">
                <label for="email">Your Email <span class="req">*</span></label>
                <input type="email" id="email" name="email" placeholder="ada@example.com" required>
              </div>
            </div>

            <div class="field">
              <label for="topic">What is this regarding?</label>
              <select id="topic" name="topic">
{options}
              </select>
            </div>

            <div class="field">
              <label for="message">Message <span class="req">*</span></label>
              <textarea id="message" name="message" rows="4" placeholder="Tell me a bit about what you are working on..." required></textarea>
            </div>

            <div style="margin-top: 4px;">
              <button type="submit" class="btn solid btn-large">{html.escape(contact.form.button)} &rarr;</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div class="sidebar-col">
{cards_html}
    </div>
  </div>

  <div class="contact-card" style="margin-top: 32px;">
    <h3>What I do</h3>
    <ul class="courses" style="margin-top: 8px;">
{services_html}
    </ul>
  </div>

  <p style="margin-top: 24px;"><a href="teaching.html#education">Education and credentials &rarr;</a> &middot; <a href="{address("orcid")}" target="_blank" rel="noopener">ORCID {html.escape(address("orcid_id"))} &nearr;</a></p>
</div></section>"""

doc = render_page_shell(
    title=f"{AUTHOR} — Contact",
    description=contact.description,
    here_page="contact",
    subnav_html="",
    body_html=body_html,
    generator_name="build_contact.py",
    source_yaml="contact.yaml",
)

(ROOT / "contact.html").write_text(doc, encoding="utf-8")
print(f"contact.html: {len(contact.form.topics)} topics, {len(contact.cards)} cards, "
      f"{len(contact.services)} services generated.")
