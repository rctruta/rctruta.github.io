import unittest

from model import (load_taxonomy, load_work_sections)

from . import ROOT


class TestRecognition(unittest.TestCase):
    """Recognition must name who, when, and where to check it.

    It was first written into `notes`, which is the field for caveats -- so
    "someone else selected this" rendered in the same box as "what this entry
    does not claim". Recognition without a date and a source link is the shape
    a claim takes when it inflates quietly, so the model requires all four and
    this asserts the data actually carries them.
    """

    def setUp(self):
        self.vocab = load_taxonomy()
        self.items = [i for s in load_work_sections(self.vocab) for i in s.items]
        self.page = (ROOT / "work.html").read_text(encoding="utf-8")

    def test_every_recognition_is_sourced_and_dated(self):
        for item in self.items:
            for r in item.recognition:
                self.assertTrue(r.who.strip(), f"{item.id}: recognition with no `who`")
                self.assertTrue(r.what.strip(), f"{item.id}: recognition with no `what`")
                self.assertRegex(r.date, r"^\d{4}-\d{2}-\d{2}$",
                                 f"{item.id}: recognition date must be YYYY-MM-DD")
                self.assertTrue(r.url.startswith("http"),
                                f"{item.id}: recognition needs an absolute source url")

    def test_a_recognition_badge_is_served_by_the_recognising_party(self):
        """A badge must be an absolute https image URL.

        The point of a badge rather than a typed score is that the source
        serves it, so a relative path or a copy committed into assets/ would
        defeat it -- it would go stale exactly like the number it replaced.
        """
        for item in self.items:
            for r in item.recognition:
                if not r.badge:
                    continue
                self.assertTrue(
                    r.badge.startswith("https://"),
                    f"{item.id}: recognition badge must be an absolute https "
                    f"URL served by {r.who}, got {r.badge!r}")
                self.assertTrue(
                    r.badge_alt.strip(),
                    f"{item.id}: a badge carries the claim as an image, so it "
                    f"needs alt text stating what it says")

    def test_recognition_reaches_the_page(self):
        for item in self.items:
            for r in item.recognition:
                self.assertIn(r.url, self.page,
                              f"{item.id}: recognition from {r.who} is in the data "
                              f"but its source link is not on work.html")

    def test_recognition_is_not_hiding_in_notes(self):
        """The two fields render differently; a caveat box is not a credit."""
        signals = ("selected for", "selected the", "indexed, then claimed",
                   "featured in", "chosen for")
        for item in self.items:
            for n in item.notes:
                blob = f"{n.label or ''} {n.text or ''}".lower()
                for s in signals:
                    self.assertNotIn(s, blob,
                                     f"{item.id}: that reads like recognition, not a "
                                     f"caveat -- move it to `recognition:`")
