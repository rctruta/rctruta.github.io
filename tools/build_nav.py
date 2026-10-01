"""Write the site navigation into every page from one definition.

    python3 tools/build_nav.py

The nav was duplicated across six pages and three generators, and had already
drifted. This is the only place it is defined. Run it after adding a page.

Generated pages (speaking, writing, tags) are rewritten by their own tools too,
so this runs over whatever is on disk and their templates carry the same list —
if they disagree, this file wins and the generator should be corrected.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

# label -> file. Index is site-wide, so it sits with the sections, not inside one.
NAV = [
    ("Work", "work.html"),
    ("Teaching", "teaching.html"),
    ("Speaking", "speaking.html"),
    ("Writing", "writing.html"),
    ("Index", "tags.html"),
    ("Contact", "contact.html"),
]

PAGES = [
    "index.html", "work.html", "teaching.html", "speaking.html",
    "writing.html", "tags.html", "contact.html",
]


def nav_html(current):
    links = "\n".join(
        f'    <a href="{href}"{" class=\"here\"" if href == current else ""}>{label}</a>'
        for label, href in NAV
    )
    return f"""<nav class="topnav"><div class="wrap">
  <a class="brand" href="index.html">Ramona C. Truta</a>
  <span class="navlinks">
{links}
  </span>
</div></nav>"""


changed = 0
for name in PAGES:
    page = ROOT / name
    if not page.exists():
        print(f"  skipped (missing): {name}")
        continue
    text = page.read_text()
    new = re.sub(
        r'<nav class="topnav">.*?</nav>', nav_html(name), text, count=1, flags=re.S
    )
    if new != text:
        page.write_text(new)
        changed += 1

print(f"nav written into {changed} of {len(PAGES)} pages, {len(NAV)} links")
