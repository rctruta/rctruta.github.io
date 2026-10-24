import re
import unittest

from model import (load_taxonomy, load_work_sections, load_articles,
                   load_appearances)

from . import ROOT


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
        page = self.read("speaking.html")
        for a in load_appearances(self.vocab):
            visible = a.kind == "talk" or bool(a.url)   # visibility is derived
            if visible:
                self.assertIn(f'id="{a.id}"', page, f"speaking.html is missing {a.id}")
            if a.counterpart:
                self.assertIn(a.counterpart, page,
                              f"speaking.html does not credit {a.counterpart}")

    def test_no_escaped_markup_reaches_a_page(self):
        """Tags printed as text instead of rendered.

        Jinja autoescapes a variable, so HTML built in Python and passed into a
        template arrives as visible &lt;em&gt;. It reached the live speaking page.
        """
        for name in ("index.html", "work.html", "teaching.html", "speaking.html",
                     "writing.html", "tags.html", "contact.html"):
            page = ROOT / name
            if not page.exists():
                continue
            for bad in ("&lt;em&gt;", "&lt;strong&gt;", "&lt;a href", "&lt;code&gt;", "&lt;br"):
                self.assertNotIn(bad, page.read_text(),
                                 f"{name} prints {bad} as text instead of rendering it")


    def test_every_project_reaches_the_work_page(self):
        page = self.read("work.html")
        for sec in load_work_sections(self.vocab):
            self.assertIn(f'id="{sec.id}"', page, f"work.html is missing section {sec.id}")
            for item in sec.items:
                self.assertIn(f'id="{item.id}"', page, f"work.html is missing {item.id}")

    def test_every_article_reaches_the_writing_page(self):
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
