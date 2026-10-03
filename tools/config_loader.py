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
        "features": {}
    }

    # Extract site metadata
    for key in ("title", "tagline", "description", "url", "image", "copyright_license", "copyright_license_url"):
        m = re.search(rf"^\s*{key}:\s*[\"']?([^\"'\n]+)[\"']?", text, re.M)
        if m:
            config["site"][key] = m.group(1).strip()

    # Extract author details
    config["site"]["author"] = {}
    for key in ("name", "contact_form", "substack", "substack_rss", "github"):
        m = re.search(rf"^\s*{key}:\s*[\"']?([^\"'\n]+)[\"']?", text, re.M)
        if m:
            config["site"]["author"][key] = m.group(1).strip()

    # Extract feature flags
    for key in ("pagefind_search", "privacy_checker", "taxonomy_checker"):
        m = re.search(rf"^\s*{key}:\s*(true|false)", text, re.M)
        if m:
            config["features"][key] = (m.group(1).lower() == "true")

    # Extract navigation list
    nav_blocks = re.findall(
        r"-\s*id:\s*(\w+)\s*\n\s*label:\s*[\"']?([^\"'\n]+)[\"']?\s*\n\s*href:\s*[\"']?([^\"'\n]+)[\"']?\s*\n\s*enabled:\s*(true|false)",
        text
    )
    for nav_id, label, href, enabled in nav_blocks:
        if enabled.lower() == "true":
            config["navigation"].append({
                "id": nav_id,
                "label": label,
                "href": href,
                "enabled": True
            })

    return config
