"""Shared page skeleton, card renderer, and Jinja2 environment setup."""
import html
import pathlib
import re
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from config_loader import load_config
from model import ProjectItem

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
CONFIG = load_config()

AUTHOR = CONFIG["site"]["author"].get("name", "Author")
SITE_TITLE = CONFIG["site"].get("title", AUTHOR)
SITE_URL = CONFIG["site"].get("url", "")
SITE_IMAGE = CONFIG["site"].get("image", f"{SITE_URL}/assets/photo.jpg")
SUBSTACK_URL = CONFIG["site"]["author"].get("substack", "https://substack.com")
SUBSTACK_RSS = CONFIG["site"]["author"].get("substack_rss", f"{SUBSTACK_URL}/feed")
SEARCH_LABEL = CONFIG["site"].get("search_label", "Search this site")
LICENSE_LABEL = CONFIG["site"].get("copyright_license", "CC BY-NC-SA 4.0")
LICENSE_URL = CONFIG["site"].get("copyright_license_url", "https://creativecommons.org/licenses/by-nc-sa/4.0/")

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def slug(tag: str) -> str:
    """Standard tag slugifier."""
    return re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")


def format_inline(text: str) -> str:
    """Format markdown inline syntax to HTML."""
    if not text:
        return ""
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
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


def when(d: str) -> str:
    if not d:
        return ""
    parts = d.split("-")
    if len(parts) >= 2:
        y, m = parts[0], parts[1]
        return f"{MONTHS[int(m) - 1]} {y}"
    return d


def render_tag_chips(tags: List[str]) -> str:
    """Render tag chips linking to tags.html#slug."""
    cells = "".join(
        f'<a class="tag" href="tags.html#{slug(t)}">{html.escape(t)}</a>' for t in tags
    )
    return f'<div class="tags">{cells}</div>'


def nav_description(here_page: str) -> str:
    """The one-line description config.yaml gives this page."""
    for nav in CONFIG["navigation"]:
        if nav["href"] == f"{here_page}.html":
            return nav["description"]
    raise KeyError(f"no navigation entry in config.yaml for '{here_page}.html'")


# Jinja2 Environment setup
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

env.filters["slug"] = slug
env.filters["format_inline"] = format_inline
env.filters["format_blocks"] = format_blocks
env.filters["when"] = when


def render_template(
    template_name: str,
    title: str,
    here_page: str,
    generator_name: str,
    source_yaml: str,
    subnav_html: str = "",
    description: Optional[str] = None,
    extra_head: str = "",
    **kwargs
) -> str:
    """Render a Jinja2 template with base context."""
    in_nav = any(n["href"] == f"{here_page}.html" for n in CONFIG["navigation"])
    if in_nav:
        if description is not None:
            raise ValueError(f"{here_page}.html is in the navigation; its description belongs in config.yaml")
        description = nav_description(here_page)
    elif description is None:
        raise ValueError(f"{here_page}.html has no navigation entry, so it needs an explicit description")

    template = env.get_template(template_name)
    return template.render(
        title=title,
        description=description,
        here_page=here_page,
        generator_name=generator_name,
        source_yaml=source_yaml,
        subnav_html=subnav_html,
        extra_head=extra_head,
        site=CONFIG["site"],
        config=CONFIG,
        **kwargs
    )
