"""Zero-dependency configuration loader for config.yaml."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"config.yaml not found at {CONFIG_PATH}")
    text = CONFIG_PATH.read_text(encoding="utf-8")

    config = {
        "site": {},
        "navigation": [],
        "data": {}
    }

    # Extract site metadata
    for key in ("title", "tagline", "description", "url", "image", "copyright_license", "copyright_license_url", "search_label"):
        m = re.search(rf"^\s*{key}:\s*[\"']?([^\"'\n]+)[\"']?", text, re.M)
        if m:
            config["site"][key] = m.group(1).strip()

    # Extract author details
    config["site"]["author"] = {}
    for key in ("name", "contact_form", "substack", "substack_rss", "github",
                "linkedin", "orcid", "orcid_id", "calendly"):
        m = re.search(rf"^\s*{key}:\s*[\"']?([^\"'\n]+)[\"']?", text, re.M)
        if m:
            config["site"]["author"][key] = m.group(1).strip()

    # The controlled vocabulary's filename. No default: a fallback here would
    # mean deleting the data block from config.yaml still builds, silently,
    # against a filename nobody chose.
    m = re.search(r"^\s*controlled_vocabulary:\s*[\"']?([^\"'\n]+)[\"']?", text, re.M)
    if not m:
        raise ValueError("config.yaml is missing data.controlled_vocabulary")
    config["data"]["controlled_vocabulary"] = m.group(1).strip()

    # Extract navigation list. Each entry carries the one-line description that
    # becomes the page's meta description, the lede at the top of that page, and
    # the line beside it on the home page — so the three cannot drift apart.
    # A missing field raises; a silently dropped nav entry is how a page
    # disappears from the site without anyone noticing.
    nav_text = re.search(r"^navigation:\n(.*?)(?=^\w)", text, re.M | re.S)
    nav_text = nav_text.group(1) if nav_text else ""
    for entry in re.split(r"\n(?=  - id:)", nav_text):
        if "- id:" not in entry:
            continue
        fields = {}
        for key in ("id", "label", "description", "href", "enabled"):
            m = re.search(rf"^\s*(?:- )?{key}:\s*[\"']?(.*?)[\"']?\s*$", entry, re.M)
            if m is None:
                nav_id = re.search(r"- id:\s*(\w+)", entry)
                raise ValueError(
                    f"config.yaml navigation entry '{nav_id.group(1) if nav_id else entry.strip()[:40]}' "
                    f"is missing '{key}'")
            fields[key] = m.group(1)
        if fields["enabled"].lower() == "true":
            config["navigation"].append({
                "id": fields["id"],
                "label": fields["label"],
                "description": fields["description"],
                "href": fields["href"],
                "enabled": True
            })

    return config
