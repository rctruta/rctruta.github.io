"""Shared page skeleton, card renderer, and HTML component generator."""
import html
import pathlib
import re
from typing import List, Optional
from config_loader import load_config
from model import ProjectItem, Article

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = load_config()

AUTHOR = CONFIG["site"]["author"].get("name", "Author")
SITE_TITLE = CONFIG["site"].get("title", AUTHOR)
SITE_URL = CONFIG["site"].get("url", "")
SITE_IMAGE = CONFIG["site"].get("image", f"{SITE_URL}/assets/photo.jpg")
SUBSTACK_URL = CONFIG["site"]["author"].get("substack", "https://substack.com")
SUBSTACK_RSS = CONFIG["site"]["author"].get("substack_rss", f"{SUBSTACK_URL}/feed")
LICENSE_LABEL = CONFIG["site"].get("copyright_license", "CC BY-NC-SA 4.0")
LICENSE_URL = CONFIG["site"].get("copyright_license_url", "https://creativecommons.org/licenses/by-nc-sa/4.0/")


def slug(tag: str) -> str:
    """Standard tag slugifier."""
    return re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")


def format_inline(text: str) -> str:
    """Format markdown inline syntax to HTML."""
    if not text:
        return ""
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Only a link that leaves the site opens in a new tab.
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    text = re.sub(r"\[([^\]]+)\]\((?!https?://)([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = (text.replace("—", "&mdash;").replace("“", "&ldquo;").replace("”", "&rdquo;")
                .replace("‘", "&lsquo;").replace("’", "&rsquo;").replace("'", "&rsquo;"))
    return text


def format_blocks(text: str) -> str:
    """Format multiline markdown blocks into HTML paragraphs and unordered lists."""
    if not text:
        return ""
    blocks = [b.strip() for b in text.strip().split("\n\n") if b.strip()]
    html_blocks = []
    for b in blocks:
        if b.startswith("<p") or b.startswith("<figure") or b.startswith("<div"):
            html_blocks.append(b)
        elif all(line.strip().startswith("- ") for line in b.splitlines()):
            items = "".join(f"<li>{format_inline(line.strip()[2:])}</li>" for line in b.splitlines() if line.strip())
            html_blocks.append(f"<ul>\n{items}\n</ul>")
        else:
            html_blocks.append(f"<p>{format_inline(b)}</p>")
    return "\n\n".join(html_blocks)


def render_tag_chips(tags: List[str]) -> str:
    """Render tag chips linking to tags.html#slug."""
    cells = "".join(
        f'<a class="tag" href="tags.html#{slug(t)}">{html.escape(t)}</a>' for t in tags
    )
    return f'<div class="tags">{cells}</div>'


def render_project_card(item: ProjectItem) -> str:
    """Render div.proj card for a ProjectItem."""
    tag_row = render_tag_chips(item.tags)

    figures_html = ""
    if item.figures:
        fig_list = []
        for fig in item.figures:
            fig_list.append(
                f'    <figure>\n'
                f'      <img src="{fig.src}" alt="{html.escape(fig.alt)}">\n'
                f'      <figcaption>{fig.caption}</figcaption>\n'
                f'    </figure>'
            )
        figures_html = "\n" + "\n".join(fig_list)

    links_html = ""
    if item.links:
        lnk_list = "".join(
            f'\n      <a href="{lnk.url}" target="_blank" rel="noopener">{html.escape(lnk.text)}</a>'
            for lnk in item.links
        )
        links_html = f'\n\n    <div class="links">{lnk_list}\n    </div>'

    notes_html = ""
    if item.notes:
        nt_list = []
        for nt in item.notes:
            if nt.label and nt.url:
                nt_list.append(
                    f'    <div class="note"><strong><a href="{nt.url}" target="_blank" rel="noopener">'
                    f'{html.escape(nt.label)}</a></strong> {nt.text or ""}</div>'
                )
            elif nt.text:
                nt_list.append(f'    <div class="note">{format_inline(nt.text)}</div>')
        if nt_list:
            notes_html = "\n\n" + "\n".join(nt_list)

    title_html = html.escape(item.title)
    if item.url:
        meta_span = f' <span class="meta">{html.escape(item.meta)}</span>' if item.meta else ""
        title_html = f'<a href="{item.url}">{title_html}</a>{meta_span}'

    desc_formatted = format_blocks(item.description) if item.description else ""

    return (
        f'  <div class="proj" id="{item.id}">\n'
        f'    <h3>{title_html}</h3>\n'
        f'    {desc_formatted}{figures_html}\n\n'
        f'    {tag_row}{links_html}{notes_html}\n'
        f'  </div>'
    )


def nav_description(here_page: str) -> str:
    """The one-line description config.yaml gives this page.

    It is written once, in config.yaml, and used three times: the meta
    description, the lede at the top of the page, and the line beside the page
    on the home page. A page not listed in the navigation has no description,
    and that is a build failure rather than a blank lede.
    """
    for nav in CONFIG["navigation"]:
        if nav["href"] == f"{here_page}.html":
            return nav["description"]
    raise KeyError(f"no navigation entry in config.yaml for '{here_page}.html'")


def render_topnav(here_page: str = "") -> str:
    """Render top navigation bar based on config.yaml."""
    nav_links = []
    for nav in CONFIG["navigation"]:
        is_here = ' class="here"' if nav["href"] == f"{here_page}.html" or (here_page == "tags" and nav["href"] == "tags.html") else ""
        tip = html.escape(nav["description"], quote=True)
        nav_links.append(f'    <a href="{nav["href"]}"{is_here} data-tip="{tip}">{html.escape(nav["label"])}</a>')

    nav_links_str = "\n".join(nav_links)
    return (
        f'<nav class="topnav"><div class="wrap">\n'
        f'  <a class="brand" href="index.html" title="Home" aria-label="Home">{html.escape(AUTHOR)}</a>\n'
        f'  <span class="navlinks">\n'
        f'{nav_links_str}\n'
        f'    <button type="button" class="searchbtn" aria-label="Search this site" title="Search this site (⌘K)" data-search-open>\n'
        f'      <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor"\n'
        f'           stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4.2-4.2"/></svg>\n'
        f'    </button>\n'
        f'  </span>\n'
        f'</div></nav>'
    )


def render_page_shell(
    title: str,
    here_page: str,
    subnav_html: str,
    body_html: str,
    generator_name: str,
    source_yaml: str,
    description: Optional[str] = None,
    extra_head: str = ""
) -> str:
    """Render complete HTML page document shell.

    `description` is only for a page with no navigation entry of its own (the
    home page). A page in the nav takes its description from config.yaml, so
    there is no second place for it to be written.
    """
    in_nav = any(n["href"] == f"{here_page}.html" for n in CONFIG["navigation"])
    if in_nav:
        if description is not None:
            raise ValueError(f"{here_page}.html is in the navigation; its description belongs in config.yaml")
        description = nav_description(here_page)
    elif description is None:
        raise ValueError(f"{here_page}.html has no navigation entry, so it needs an explicit description")
    topnav = render_topnav(here_page)
    subnav_block = f'<nav class="subnav" id="top"><div class="wrap">\n{subnav_html}\n</div></nav>' if subnav_html else ""

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="icon" type="image/x-icon" href="assets/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="assets/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png">
<meta property="og:site_name" content="{html.escape(SITE_TITLE)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:image" content="{html.escape(SITE_IMAGE)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(description)}">
<meta name="twitter:image" content="{html.escape(SITE_IMAGE)}">{extra_head}
<link rel="stylesheet" href="style.css"></head><body>
<!-- Generated by tools/{generator_name} from data/{source_yaml}. Do not edit by hand. -->
{topnav}
{subnav_block}

{body_html}

<footer><div class="wrap"><span>&copy; 2025&ndash;2026 {html.escape(AUTHOR)} &middot; <a href="{html.escape(LICENSE_URL)}" rel="license">{html.escape(LICENSE_LABEL)}</a> &middot; <a href="contact.html">Contact</a></span></div></footer>
</body></html>
"""
