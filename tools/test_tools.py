"""Automated unit test suite for site tools, config schema, taxonomy data models, and pipeline validation.

    python3 tools/test_tools.py
"""
import pathlib
import re
import unittest
from config_loader import load_config
from model import load_taxonomy, load_work_sections, load_articles, load_appearances

ROOT = pathlib.Path(__file__).resolve().parent.parent


class TestSitePipeline(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.vocab_model = load_taxonomy()
        self.vocab = self.vocab_model.vocabulary
        self.facets_meta = self.vocab_model.facets
        self.kinds_meta = self.vocab_model.kinds

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

    def test_work_yaml_integrity(self):
        """Verify data/work.yaml loads and all tags pass vocabulary validation."""
        sections = load_work_sections(self.vocab_model)
        self.assertGreater(len(sections), 0, "data/work.yaml must have sections")
        total_items = sum(len(s.items) for s in sections)
        self.assertGreater(total_items, 0, "data/work.yaml must have work items")

    def test_writing_yaml_integrity(self):
        """Verify data/writing.yaml loads into Article models and all tags pass vocabulary validation."""
        articles = load_articles(self.vocab_model)
        self.assertGreater(len(articles), 0, "data/writing.yaml must have articles")

    def test_appearances_yaml_integrity(self):
        """Verify data/appearances.yaml loads into Appearance models and all tags pass vocabulary validation."""
        appearances = load_appearances(self.vocab_model)
        self.assertGreater(len(appearances), 0, "data/appearances.yaml must have appearances")

    def test_teaching_yaml_integrity(self):
        """Verify data/teaching.yaml exists and contains valid tags."""
        teaching_path = ROOT / "data" / "teaching.yaml"
        self.assertTrue(teaching_path.exists(), "data/teaching.yaml must exist")
        text = teaching_path.read_text(encoding="utf-8")
        for m in re.finditer(r"tags: \[(.*?)\]", text):
            tags = [t.strip() for t in m.group(1).split(",") if t.strip()]
            for t in tags:
                self.assertIn(t, self.vocab, f"Teaching tag '{t}' not in vocabulary")

    def test_tags_html_list_structure(self):
        """Verify tags.html uses ordered lists (<ol class="tag-list">) for items."""
        if (ROOT / "tags.html").exists():
            tags_html = (ROOT / "tags.html").read_text(encoding="utf-8")
            self.assertIn('<ol class="tag-list">', tags_html, "tags.html must use <ol class=\"tag-list\"> for items")


if __name__ == "__main__":
    unittest.main()
