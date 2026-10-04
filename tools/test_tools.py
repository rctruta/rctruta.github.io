"""Automated unit test suite for site tools, config schema, taxonomy data models, and pipeline validation.

    python3 tools/test_tools.py
"""
import html
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


class TestNavigationIntegrity(unittest.TestCase):
    """Two defects that reached the live site and were found by eye, not by test."""

    PAGES = ["index.html", "work.html", "teaching.html", "speaking.html",
             "writing.html", "tags.html", "contact.html"]

    def test_subnav_labels_match_their_headings(self):
        """A sub-nav link must read the same as the heading it points at.

        The nav once said "Philosophy" over a heading reading "Teaching", and
        "AI" over "AI & Agent Evaluation". Two labels for one thing.
        """
        for name in self.PAGES:
            page = ROOT / name
            if not page.exists():
                continue
            text = page.read_text()
            m = re.search(r'<nav class="subnav".*?</nav>', text, re.S)
            if not m:
                continue
            headings = dict(re.findall(r'<h2 id="([a-z0-9-]+)">(.*?)</h2>', text, re.S))
            for anchor, label in re.findall(r'href="#([a-z0-9-]+)">([^<]+)</a>', m.group(0)):
                if anchor in headings:
                    heading = re.sub(r"<[^>]+>", "", headings[anchor]).strip()
                    self.assertEqual(
                        label.strip(), heading,
                        f"{name}: nav says '{label.strip()}', heading says '{heading}'")

    def test_internal_anchors_resolve(self):
        """Every page.html#anchor link must point at an id that exists.

        work.html#tooling sat broken in the home page bio after a section was
        renamed, and nothing caught it.
        """
        broken = []
        for name in self.PAGES:
            page = ROOT / name
            if not page.exists():
                continue
            for target, anchor in re.findall(r'href="([a-z]+\.html)#([a-z0-9-]+)"', page.read_text()):
                tgt = ROOT / target
                if not tgt.exists() or f'id="{anchor}"' not in tgt.read_text():
                    broken.append(f"{name} -> {target}#{anchor}")
        self.assertEqual([], sorted(set(broken)), "broken internal anchors")


class TestDescriptionsPropagate(unittest.TestCase):
    """A hand-written home page stops being true without telling anyone.

    Each page's one-line description is written once, in config.yaml. It is the
    meta description, the hover on that page's nav link, and the line beside the
    link on the home page. These assert the three are the same string.
    """

    def setUp(self):
        self.nav = load_config()["navigation"]
        self.home = (ROOT / "index.html").read_text() if (ROOT / "index.html").exists() else ""

    def test_each_page_shows_its_configured_description(self):
        for nav in self.nav:
            page = ROOT / nav["href"]
            if not page.exists():
                continue
            text = page.read_text()
            meta = re.search(r'<meta name="description" content="(.*?)">', text)
            self.assertEqual(html.unescape(meta.group(1)), nav["description"],
                             f"{nav['href']} meta description differs from config.yaml")

    def test_every_nav_link_carries_its_description_as_a_hover(self):
        for nav in self.nav:
            for name in [n["href"] for n in self.nav] + ["index.html"]:
                page = ROOT / name
                if not page.exists():
                    continue
                tip = re.search(rf'<a href="{re.escape(nav["href"])}"[^>]*data-tip="([^"]*)"', page.read_text())
                self.assertIsNotNone(tip, f"{name}: nav link to {nav['href']} has no hover description")
                self.assertEqual(html.unescape(tip.group(1)), nav["description"],
                                 f"{name}: hover on {nav['href']} differs from config.yaml")

    def test_home_page_lists_every_nav_page_with_the_same_description(self):
        if not self.home:
            self.skipTest("index.html not built")
        for nav in self.nav:
            self.assertIn(html.escape(nav["description"], quote=False).replace("'", "&#x27;"), self.home,
                          f"index.html does not carry the description for {nav['href']}")

    def test_home_page_testimonial_count_matches_the_data(self):
        if not self.home:
            self.skipTest("index.html not built")
        from model import count_testimonials
        shown = re.search(r'href="teaching\.html#testimonials">(\d+) ', self.home)
        self.assertIsNotNone(shown, "index.html does not state a testimonial count")
        self.assertEqual(count_testimonials(), int(shown.group(1)),
                         "index.html states a testimonial count data/teaching.yaml does not support")


class TestContactAddresses(unittest.TestCase):
    """The form endpoint was written in two places. Rotating one lost messages."""

    def setUp(self):
        self.author = load_config()["site"]["author"]
        self.page = (ROOT / "contact.html").read_text() if (ROOT / "contact.html").exists() else ""

    def test_form_posts_to_the_configured_endpoint(self):
        if not self.page:
            self.skipTest("contact.html not built")
        action = re.search(r'<form class="contact-form" action="([^"]+)"', self.page)
        self.assertIsNotNone(action, "contact.html has no contact form")
        self.assertEqual(self.author["contact_form"], action.group(1),
                         "contact.html posts somewhere config.yaml does not name")

    def test_contact_yaml_services_are_vocabulary_terms(self):
        from model import load_contact
        contact = load_contact(load_taxonomy())      # raises on an unknown tag
        self.assertGreater(len(contact.services), 0, "data/contact.yaml must list services")


if __name__ == "__main__":
    unittest.main()

