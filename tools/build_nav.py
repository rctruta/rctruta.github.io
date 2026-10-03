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
from config_loader import load_config

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = load_config()

NAV = [(item["label"], item["href"]) for item in CONFIG["navigation"]]
PAGES = [item["href"] for item in CONFIG["navigation"]] + ["index.html"]
BRAND = CONFIG["site"]["author"].get("name", CONFIG["site"].get("title", "Home"))


def nav_html(current):
    links = "\n".join(
        f'    <a href="{href}"{" class=\"here\"" if href == current else ""}>{label}</a>'
        for label, href in NAV
    )
    return f"""<nav class="topnav"><div class="wrap">
  <a class="brand" href="index.html">{BRAND}</a>
  <span class="navlinks">
{links}
    <button type="button" class="searchbtn" aria-label="Search this site" title="Search this site (⌘K)" data-search-open>
      <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4.2-4.2"/></svg>
    </button>
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
