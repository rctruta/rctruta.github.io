"""Write the site navigation into every page from one definition."""
import html
import pathlib
import re
from config_loader import load_config

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = load_config()

NAV = [(item["label"], item["href"], item["description"]) for item in CONFIG["navigation"]]
PAGES = [item["href"] for item in CONFIG["navigation"]] + ["index.html"]
BRAND = CONFIG["site"]["author"].get("name", CONFIG["site"].get("title", "Home"))
SEARCH = html.escape(CONFIG["site"].get("search_label", "Search this site"), quote=True)


def here_class(href, current):
    return ' class="here"' if href == current else ""


def nav_html(current):
    links = "\n".join(
        f'    <a href="{href}"{here_class(href, current)}'
        f' data-tip="{html.escape(tip, quote=True)}">{label}</a>'
        for label, href, tip in NAV
    )
    return f"""<nav class="topnav"><div class="wrap">
  <a class="brand" href="index.html" title="Home" aria-label="Home">{BRAND}</a>
  <span class="navlinks">
{links}
    <button type="button" class="searchbtn" aria-label="{SEARCH}" data-tip="{SEARCH}" data-search-open>
      <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4.2-4.2"/></svg>
    </button>
  </span>
</div></nav>"""

DESCRIPTIONS = {item["href"]: item["description"] for item in CONFIG["navigation"]}


def write_descriptions(text, description):
    """The meta, og and twitter descriptions, all from the one config.yaml line."""
    esc = html.escape(description, quote=True)
    for pattern in (r'(<meta name="description" content=")[^"]*(">)',
                    r'(<meta property="og:description" content=")[^"]*(">)',
                    r'(<meta name="twitter:description" content=")[^"]*(">)'):
        text = re.sub(pattern, lambda m: m.group(1) + esc + m.group(2), text, count=1)
    return text


def drop_lede(text):
    """Remove the lede block. The description is a hover on the nav link now."""
    return re.sub(r"\n?<!-- lede:start -->.*?<!-- lede:end -->\n?", "\n", text, count=1, flags=re.S)


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
    new = drop_lede(new)
    if name in DESCRIPTIONS:                      # index.html has no nav entry of its own
        new = write_descriptions(new, DESCRIPTIONS[name])
    if new != text:
        page.write_text(new)
        changed += 1

print(f"nav + hover + descriptions written into {changed} of {len(PAGES)} pages, {len(NAV)} links")
