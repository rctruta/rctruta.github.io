"""Render the configured bio as plain text, Markdown or HTML."""
import html
import re
import sys
from config_loader import load_config
from model import load_taxonomy, load_work_sections, load_home
from page import format_inline

SITE_URL = load_config()["site"].get("url", "").rstrip("/")


def _targets():
    vocab = load_taxonomy()
    sections = {s.id: s.title for s in load_work_sections(vocab)}
    return vocab, sections


def _resolve(text, link, drop_links=False):
    """Replace every (tag:…) and (work:…) reference, raising on an unknown one."""
    vocab, sections = _targets()

    def tag_ref(m):
        term = m.group(2)
        if term not in vocab.vocabulary:
            raise ValueError(f"bio links to tag '{term}', which is not in data/TAGS.yaml")
        return m.group(1) if drop_links else link(m.group(1), f"tags.html#{vocab.anchors[term]}", term)

    def work_ref(m):
        sec = m.group(2)
        if sec not in sections:
            raise ValueError(f"bio links to work section '{sec}', which is not in data/work.yaml")
        return m.group(1) if drop_links else link(m.group(1), f"work.html#{sec}", sections[sec])

    text = re.sub(r"\[([^\]]+)\]\(tag:([^)]+)\)", tag_ref, text)
    text = re.sub(r"\[([^\]]+)\]\(work:([^)]+)\)", work_ref, text)
    return text


def as_html(bio: str) -> str:
    """For this site: relative links, canonical name on hover."""
    def link(text, href, canonical):
        return f'<a href="{href}" title="{html.escape(canonical, quote=True)}">{text}</a>'
    return format_inline(_resolve(bio, link))


def as_markdown(bio: str) -> str:
    """For GitHub and anywhere else off-site: absolute links."""
    def link(text, href, canonical):
        return f"[{text}]({SITE_URL}/{href})"
    text = _resolve(bio, link)
    return re.sub(r"\]\((?!https?://)([a-z_]+\.html[^)]*)\)", rf"]({SITE_URL}/\1)", text)


def as_plain(bio: str) -> str:
    """For LinkedIn, Substack and the resume: the words, no links."""
    text = _resolve(bio, None, drop_links=True)
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)


if __name__ == "__main__":
    bio = load_home().bio
    mode = sys.argv[1] if len(sys.argv) > 1 else "--plain"
    print({"--plain": as_plain, "--markdown": as_markdown, "--html": as_html}[mode](bio))
