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
            self.assertIn(html.unescape(nav["description"]), html.unescape(self.home),
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


class TestNothingVanishes(unittest.TestCase):
    """Every record in the data must appear on its page.

    A template rewrite dropped the guest-host section, the five interview
    credits and a line of prose kept in the data, and all sixteen tests passed:
    they checked navigation, anchors and descriptions, and nothing checked that
    the content survived. A page can lose a whole section and still be
    well-formed.
    """

    def setUp(self):
        self.vocab = load_taxonomy()

    def read(self, name):
        page = ROOT / name
        if not page.exists():
            self.skipTest(f"{name} not built")
        return page.read_text()

    def test_every_appearance_reaches_the_speaking_page(self):
        from model import load_appearances
        page = self.read("speaking.html")
        for a in load_appearances(self.vocab):
            visible = a.kind == "talk" or bool(a.url)   # visibility is derived
            if visible:
                self.assertIn(f'id="{a.id}"', page, f"speaking.html is missing {a.id}")
            if a.counterpart:
                self.assertIn(a.counterpart, page,
                              f"speaking.html does not credit {a.counterpart}")

    def test_every_project_reaches_the_work_page(self):
        from model import load_work_sections
        page = self.read("work.html")
        for sec in load_work_sections(self.vocab):
            self.assertIn(f'id="{sec.id}"', page, f"work.html is missing section {sec.id}")
            for item in sec.items:
                self.assertIn(f'id="{item.id}"', page, f"work.html is missing {item.id}")

    def test_every_article_reaches_the_writing_page(self):
        from model import load_articles
        page = self.read("writing.html")
        for a in load_articles(self.vocab):
            self.assertIn(a.url, page, f"writing.html is missing {a.id}")

    def test_prose_kept_in_the_data_reaches_its_page(self):
        """A line written in a data file is there to be rendered."""
        import html as _html
        note = re.search(r'^guest_host_note: "(.*)"\s*$',
                         (ROOT / "data" / "appearances.yaml").read_text(), re.M)
        self.assertIsNotNone(note, "appearances.yaml lost guest_host_note")
        page = self.read("speaking.html")
        self.assertIn(_html.escape(note.group(1), quote=False).replace("'", "&#x27;"), page,
                      "speaking.html does not render guest_host_note")


class TestOneBio(unittest.TestCase):
    """The bio is one string. Every rendering of it says the same words.

    It was split into a travelling `bio` and a home-page-only `site_note`, on
    the reasoning that "this site" has no referent off the website. The
    sentence belongs everywhere, so `tools/bio.py` — the command that produces
    text for LinkedIn and the resume — quietly returned a shorter bio than the
    website and GitHub were showing. Three renderings, two of them agreeing.
    """

    def test_all_three_renderings_carry_the_same_words(self):
        from bio import as_plain, as_markdown, as_html
        from model import load_home
        bio = load_home().bio

        def words(s):
            s = re.sub(r"<[^>]+>", "", s)                 # html tags
            s = re.sub(r"\]\([^)]+\)", "]", s)             # markdown targets
            s = re.sub(r"&[a-z]+;|&#x?\w+;", "'", s)       # entities
            return re.findall(r"[a-z]+", s.lower())

        plain, md, htm = words(as_plain(bio)), words(as_markdown(bio)), words(as_html(bio))
        self.assertEqual(plain, md, "plain and markdown bios differ")
        self.assertEqual(plain, htm, "plain and html bios differ")

    def test_the_rendered_pages_carry_the_whole_bio(self):
        from bio import as_plain
        from model import load_home
        tail = as_plain(load_home().bio).split(". ")[-1].strip()
        for name in ("index.html",):
            page = ROOT / name
            if page.exists():
                self.assertIn(tail.rstrip("."), re.sub(r"<[^>]+>", "", page.read_text()).replace("&#x27;", "'"),
                              f"{name} is missing the end of the bio")


if __name__ == "__main__":
    unittest.main()

