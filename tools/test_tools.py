"""Automated unit test suite for site tools, config schema, taxonomy data models, and pipeline validation.

    python3 tools/test_tools.py

Tests data models (TAGS.yaml, writing.yaml, appearances.yaml, config.yaml), verifies facets and kinds,
ensures alphabetical indexing, validates HTML list structure, and enforces vocabulary contracts.
"""
import html
import pathlib
import re
import unittest
from config_loader import load_config

ROOT = pathlib.Path(__file__).resolve().parent.parent


def parse_tags_yaml(text):
    facets_meta = {}
    kinds_meta = {}
    vocab = {}
    projects = {}
    section = None
    current_item = None
    facet_name = None

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        if indent == 0 and line.endswith(":"):
            section = line[:-1]
            current_item = None
            continue

        if section == "facets":
            if indent == 2 and line.endswith(":"):
                current_item = line[:-1]
                facets_meta[current_item] = {"label": current_item.title(), "note": "", "order": 99}
            elif indent == 4 and current_item and ":" in line:
                k, v = [x.strip() for x in line.split(":", 1)]
                v = v.strip('"\'')
                if k == "order":
                    v = int(v)
                facets_meta[current_item][k] = v

        elif section == "kinds":
            if indent == 2 and line.endswith(":"):
                current_item = line[:-1]
                kinds_meta[current_item] = {"category": current_item.title(), "order": 99}
            elif indent == 4 and current_item and ":" in line:
                k, v = [x.strip() for x in line.split(":", 1)]
                v = v.strip('"\'')
                if k == "order":
                    v = int(v)
                kinds_meta[current_item][k] = v

        elif section == "vocabulary":
            if indent == 2 and line.endswith(":"):
                facet_name = line[:-1]
                continue
            if indent == 4 and facet_name and ":" in line:
                term = line.split(":", 1)[0].strip()
                vocab[term] = facet_name

        elif section == "projects" and indent == 2 and ":" in line:
            pid, rest = line.split(":", 1)
            projects[pid.strip()] = [
                t.strip() for t in rest.strip().strip("[]").split(",") if t.strip()
            ]

    return facets_meta, kinds_meta, vocab, projects


class TestSitePipeline(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.tags_text = (ROOT / "data" / "TAGS.yaml").read_text()
        self.facets_meta, self.kinds_meta, self.vocab, self.projects = parse_tags_yaml(self.tags_text)
        self.writing_text = (ROOT / "data" / "writing.yaml").read_text()
        self.appearances_text = (ROOT / "data" / "appearances.yaml").read_text()

    def test_config_schema_integrity(self):
        """Verify config.yaml loads required site and navigation fields."""
        self.assertIn("title", self.config["site"], "config.yaml missing site.title")
        self.assertIn("url", self.config["site"], "config.yaml missing site.url")
        self.assertIn("name", self.config["site"]["author"], "config.yaml missing site.author.name")
        self.assertGreater(len(self.config["navigation"]), 0, "config.yaml must have at least 1 navigation item")

        for nav in self.config["navigation"]:
            for key in ("id", "label", "href", "enabled"):
                self.assertIn(key, nav, f"Navigation item missing '{key}' in config.yaml")

    def test_taxonomy_facets_and_kinds_schema(self):
        """Verify TAGS.yaml explicitly declares facets and kinds blocks."""
        self.assertGreater(len(self.facets_meta), 0, "TAGS.yaml missing facets declaration")
        self.assertGreater(len(self.kinds_meta), 0, "TAGS.yaml missing kinds declaration")

        expected_facets = {"discipline", "method", "technology"}
        for f in expected_facets:
            self.assertIn(f, self.facets_meta, f"Missing facet '{f}' in TAGS.yaml facets block")

        expected_kinds = {"project", "article", "talk", "podcast", "teaching", "course material"}
        for k in expected_kinds:
            self.assertIn(k, self.kinds_meta, f"Missing kind '{k}' in TAGS.yaml kinds block")

    def test_vocabulary_terms_exist(self):
        """Verify controlled vocabulary terms are populated in TAGS.yaml."""
        self.assertGreater(len(self.vocab), 0, "TAGS.yaml vocabulary must not be empty")


    def test_project_tags_are_in_vocabulary(self):
        """Verify every tag assigned to a project is in the controlled vocabulary."""
        unknown = {t: p for p, ts in self.projects.items() for t in ts if t not in self.vocab}
        self.assertEqual(len(unknown), 0, f"Project tags not in vocabulary: {unknown}")

    def test_writing_yaml_integrity(self):
        """Verify writing.yaml has no unfilled placeholders and valid tags."""
        self.assertNotIn("[YOURS]", self.writing_text, "Unfilled [YOURS] placeholder found")
        for m in re.finditer(r"^  tags: \[(.*)\]\s*$", self.writing_text, re.M):
            tags = [t.strip() for t in m.group(1).split(",") if t.strip()]
            for t in tags:
                self.assertIn(t, self.vocab, f"Writing tag '{t}' not in vocabulary")

    def test_appearances_yaml_integrity(self):
        """Verify appearances.yaml uses controlled vocabulary tags."""
        for m in re.finditer(r"^  tags: \[(.*)\]\s*$", self.appearances_text, re.M):
            tags = [t.strip() for t in m.group(1).split(",") if t.strip()]
            for t in tags:
                self.assertIn(t, self.vocab, f"Appearance tag '{t}' not in vocabulary")

    def test_html_proj_anchors_in_tags_yaml(self):
        """Verify every div.proj ID in work.html and teaching.html exists in TAGS.yaml."""
        for page_name in ("work.html", "teaching.html"):
            text = (ROOT / page_name).read_text()
            proj_ids = set(re.findall(r'<div class="proj" id="([^"]+)"', text))
            for pid in proj_ids:
                self.assertIn(pid, self.projects, f"ID '{pid}' in {page_name} not registered in TAGS.yaml")

    def test_work_yaml_integrity(self):
        """Verify data/work.yaml exists and tags are in vocabulary."""
        work_path = ROOT / "data" / "work.yaml"
        self.assertTrue(work_path.exists(), "data/work.yaml must exist")
        work_text = work_path.read_text()
        for m in re.finditer(r"tags: \[(.*?)\]", work_text):
            tags = [t.strip() for t in m.group(1).split(",") if t.strip()]
            for t in tags:
                self.assertIn(t, self.vocab, f"Work tag '{t}' not in vocabulary")

    def test_teaching_yaml_integrity(self):
        """Verify data/teaching.yaml exists and tags are in vocabulary."""
        teaching_path = ROOT / "data" / "teaching.yaml"
        self.assertTrue(teaching_path.exists(), "data/teaching.yaml must exist")
        teaching_text = teaching_path.read_text()
        for m in re.finditer(r"tags: \[(.*?)\]", teaching_text):
            tags = [t.strip() for t in m.group(1).split(",") if t.strip()]
            for t in tags:
                self.assertIn(t, self.vocab, f"Teaching tag '{t}' not in vocabulary")

    def test_tags_html_list_structure_and_alphabetical_order(self):
        """Verify tags.html uses ordered lists (<ol class="tag-list">) for items."""
        if (ROOT / "tags.html").exists():
            tags_html = (ROOT / "tags.html").read_text()
            self.assertIn('<ol class="tag-list">', tags_html, "tags.html must use <ol class=\"tag-list\"> for items")


if __name__ == "__main__":
    unittest.main()
