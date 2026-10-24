import html
import re
import unittest

from config_loader import load_config

from . import ROOT


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
