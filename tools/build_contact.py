"""Generate contact.html from data/contact.yaml and config.yaml using Jinja2.

    python3 tools/build_contact.py
"""
import pathlib
from config_loader import load_config
from model import load_taxonomy, load_contact
from page import render_template, AUTHOR

ROOT = pathlib.Path(__file__).resolve().parent.parent

contact = load_contact(load_taxonomy())

doc = render_template(
    template_name="contact.html",
    title=f"{AUTHOR} — Contact",
    here_page="contact",
    generator_name="build_contact.py",
    source_yaml="contact.yaml",
    contact=contact
)

(ROOT / "contact.html").write_text(doc, encoding="utf-8")
print(f"contact.html: {len(contact.form.topics)} topics, {len(contact.cards)} cards, "
      f"{len(contact.services)} services generated.")

