"""Generate work.html from data/work.yaml.

    python3 tools/build_work.py

Section headers match the data modeling categories, with items carrying tags,
descriptions, figures, external links, and reproducible benchmarks.
"""
import html
import pathlib
import re
import sys
from config_loader import load_config

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = load_config()
SPEC = ROOT / "data" / "work.yaml"

AUTHOR = CONFIG["site"]["author"].get("name", "Author")
SITE_TITLE = CONFIG["site"].get("title", AUTHOR)
SITE_URL = CONFIG["site"].get("url", "")
SITE_IMAGE = CONFIG["site"].get("image", f"{SITE_URL}/assets/photo.jpg")
LICENSE_LABEL = CONFIG["site"].get("copyright_license", "CC BY-NC-SA 4.0")
LICENSE_URL = CONFIG["site"].get("copyright_license_url", "https://creativecommons.org/licenses/by-nc-sa/4.0/")


def slug(tag):
    return re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")


def format_inline(text):
    """Format basic markdown inline elements to HTML."""
    if not text:
        return ""
    # Convert code backticks
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Convert markdown links [label](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    # Convert bold **text**
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # Convert italic *text*
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    return text


def format_blocks(text):
    """Format multiline description into paragraphs and lists."""
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
            formatted = format_inline(b)
            html_blocks.append(f"<p>{formatted}</p>")
    return "\n\n".join(html_blocks)


def parse_work_yaml(text):
    """Parse work.yaml sections and items using zero-dependency parsing."""
    sections = []
    current_sec = None
    current_item = None
    in_figures = False
    in_links = False
    in_notes = False

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        raw_indent = len(line) - len(line.lstrip())
        trimmed = line.strip()

        if not trimmed or trimmed.startswith("#"):
            i += 1
            continue

        if raw_indent == 2 and trimmed.startswith("- id:"):
            current_sec = {"id": trimmed.split(":", 1)[1].strip(), "title": "", "summary": "", "nav": "", "items": []}
            sections.append(current_sec)
            current_item = None
            in_figures = in_links = in_notes = False

        elif raw_indent == 4 and current_sec and not current_item:
            if trimmed.startswith("title:"):
                current_sec["title"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif trimmed.startswith("summary:"):
                current_sec["summary"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif trimmed.startswith("nav:"):
                current_sec["nav"] = trimmed.split(":", 1)[1].strip().strip('"')

        elif raw_indent == 6 and trimmed.startswith("- id:"):
            current_item = {
                "id": trimmed.split(":", 1)[1].strip(),
                "title": "",
                "activity": "built",
                "tags": [],
                "description": "",
                "figures": [],
                "links": [],
                "notes": []
            }
            current_sec["items"].append(current_item)
            in_figures = in_links = in_notes = False

        elif raw_indent == 8 and current_item:
            if trimmed.startswith("title:"):
                current_item["title"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif trimmed.startswith("activity:"):
                current_item["activity"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif trimmed.startswith("tags:"):
                tag_str = trimmed.split(":", 1)[1].strip().strip("[]")
                current_item["tags"] = [t.strip() for t in tag_str.split(",") if t.strip()]
            elif trimmed.startswith("description: |"):
                # Collect multiline description
                desc_lines = []
                i += 1
                while i < len(lines):
                    next_line = lines[i]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_line.strip() and next_indent <= 8 and not next_line.lstrip().startswith("#"):
                        i -= 1
                        break
                    desc_lines.append(next_line[10:] if len(next_line) >= 10 else next_line.lstrip())
                    i += 1
                current_item["description"] = "\n".join(desc_lines).strip()
            elif trimmed.startswith("figures:"):
                in_figures = True
                in_links = in_notes = False
            elif trimmed.startswith("links:"):
                in_links = True
                in_figures = in_notes = False
            elif trimmed.startswith("notes:"):
                in_notes = True
                in_figures = in_links = False

        elif raw_indent == 10 and current_item:
            if in_figures and trimmed.startswith("- src:"):
                fig = {"src": trimmed.split(":", 1)[1].strip().strip('"'), "alt": "", "caption": ""}
                current_item["figures"].append(fig)
            elif in_links and trimmed.startswith("- text:"):
                lnk = {"text": trimmed.split(":", 1)[1].strip().strip('"'), "url": ""}
                current_item["links"].append(lnk)
            elif in_notes and trimmed.startswith("-"):
                nt = {}
                if ":" in trimmed:
                    k, v = trimmed[1:].split(":", 1)
                    nt[k.strip()] = v.strip().strip('"')
                current_item["notes"].append(nt)

        elif raw_indent == 12 and current_item:
            if in_figures and current_item["figures"]:
                fig = current_item["figures"][-1]
                if trimmed.startswith("alt:"):
                    fig["alt"] = trimmed.split(":", 1)[1].strip().strip('"')
                elif trimmed.startswith("caption:"):
                    fig["caption"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif in_links and current_item["links"]:
                lnk = current_item["links"][-1]
                if trimmed.startswith("url:"):
                    lnk["url"] = trimmed.split(":", 1)[1].strip().strip('"')
            elif in_notes and current_item["notes"]:
                nt = current_item["notes"][-1]
                if ":" in trimmed:
                    k, v = trimmed.split(":", 1)
                    nt[k.strip()] = v.strip().strip('"')

        i += 1

    return sections


spec_text = SPEC.read_text(encoding="utf-8")
sections = parse_work_yaml(spec_text)

# Validate tags against TAGS.yaml
vocab = set(re.findall(r"^    ([A-Z][^:]*):", (ROOT / "data" / "TAGS.yaml").read_text(), re.M))
all_tags = [t for sec in sections for item in sec["items"] for t in item["tags"]]
unknown = {t for t in all_tags if t not in vocab}
if unknown:
    sys.exit("tags not in data/TAGS.yaml: " + ", ".join(sorted(unknown)))


# Build HTML output
subnav_links = []
sections_html = []

for sec in sections:
    # the nav label is declared, not guessed. Chopping the title at "&" turned
    # "AI & Agent Evaluation" into "AI".
    label = sec.get("nav") or sec["title"]
    subnav_links.append(f'  <a href="#{sec["id"]}">{html.escape(label)}</a>')
    items_html = []
    for item in sec["items"]:
        tags_html = "".join(
            f'<a class="tag" href="tags.html#{slug(t)}">{html.escape(t)}</a>' for t in item["tags"]
        )
        tag_row = f'<div class="tags">{tags_html}</div>'

        figures_html = ""
        if item["figures"]:
            fig_list = []
            for fig in item["figures"]:
                fig_list.append(
                    f'    <figure>\n'
                    f'      <img src="{fig["src"]}" alt="{html.escape(fig["alt"])}">\n'
                    f'      <figcaption>{fig["caption"]}</figcaption>\n'
                    f'    </figure>'
                )
            figures_html = "\n" + "\n".join(fig_list)

        links_html = ""
        if item["links"]:
            lnk_list = "".join(
                f'\n      <a href="{lnk["url"]}" target="_blank" rel="noopener">{html.escape(lnk["text"])}</a>'
                for lnk in item["links"]
            )
            links_html = f'\n\n    <div class="links">{lnk_list}\n    </div>'

        notes_html = ""
        if item["notes"]:
            nt_list = []
            for nt in item["notes"]:
                if "label" in nt and "url" in nt:
                    nt_list.append(
                        f'    <div class="note"><strong><a href="{nt["url"]}" target="_blank" rel="noopener">'
                        f'{html.escape(nt["label"])}</a></strong> {nt.get("text", "")}</div>'
                    )
                elif "text" in nt:
                    nt_list.append(f'    <div class="note">{format_inline(nt["text"])}</div>')
            if nt_list:
                notes_html = "\n\n" + "\n".join(nt_list)

        desc_formatted = format_blocks(item["description"])

        items_html.append(
            f'  <div class="proj" id="{item["id"]}">\n'
            f'    <h3>{html.escape(item["title"])}</h3>\n\n'
            f'    {desc_formatted}{figures_html}\n\n'
            f'    {tag_row}{links_html}{notes_html}\n'
            f'  </div>'
        )

    sections_html.append(
        f'<section><div class="wrap">\n'
        f'  <h2 id="{sec["id"]}">{html.escape(sec["title"])}</h2>\n'
        f'  <p class="sub small cat-note">{html.escape(sec["summary"])}</p>\n'
        f'{chr(10).join(items_html)}\n'
        f'  <p class="totop"><a href="#top">&uarr; Top</a></p>\n'
        f'</div></section>'
    )

subnav = "\n".join(subnav_links)
body = "\n".join(sections_html)

doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(AUTHOR)} &mdash; Work</title>
<meta name="description" content="Independent researcher measuring how database and AI agent systems behave.">
<link rel="icon" type="image/x-icon" href="assets/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="assets/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png">
<meta property="og:site_name" content="{html.escape(SITE_TITLE)}">
<meta property="og:type" content="website">
<meta property="og:title" content="Work &mdash; {html.escape(AUTHOR)}">
<meta property="og:description" content="Database benchmarking, AI security, agent evaluation, system integrity, and retrieval accuracy. Every claim with the experiment attached.">
<meta property="og:image" content="{html.escape(SITE_IMAGE)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Work &mdash; {html.escape(AUTHOR)}">
<meta name="twitter:description" content="Database benchmarking, AI security, agent evaluation, system integrity, and retrieval accuracy. Every claim with the experiment attached.">
<meta name="twitter:image" content="{html.escape(SITE_IMAGE)}">
<link rel="stylesheet" href="style.css"></head><body>
<!-- Generated by tools/build_work.py from data/work.yaml. Do not edit by hand. -->
<nav class="topnav"><div class="wrap">
  <a class="brand" href="index.html">{html.escape(AUTHOR)}</a>
  <span class="navlinks">
    <a href="work.html" class="here">Work</a>
    <a href="teaching.html">Teaching</a>
    <a href="speaking.html">Speaking</a>
    <a href="writing.html">Writing</a>
    <a href="contact.html">Contact</a>
  </span>
</div></nav>
<nav class="subnav" id="top"><div class="wrap">
{subnav}
</div></nav>

{body}

<footer><div class="wrap"><span>&copy; 2025&ndash;2026 {html.escape(AUTHOR)} &middot; <a href="{html.escape(LICENSE_URL)}" rel="license">{html.escape(LICENSE_LABEL)}</a> &middot; <a href="contact.html">Contact</a></span></div></footer>
</body></html>
"""

(ROOT / "work.html").write_text(doc, encoding="utf-8")
print(f"work.html: {len(sections)} sections across {sum(len(s['items']) for s in sections)} projects generated.")
