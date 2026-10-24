import html
import unittest

from model import (load_taxonomy)

from . import ROOT


class TestVocabularyReachesThePage(unittest.TestCase):
    """A definition nobody can read is not a definition.

    Scope notes were written for 22 terms in TAGS.yaml and parsed away: the
    loader kept the term and dropped the text after the colon, so none of them
    reached tags.html. The synonym ring has the same failure mode — an entry
    term only does its job once it is indexed on a page.
    """

    def setUp(self):
        self.vocab = load_taxonomy()
        self.page = (ROOT / "tags.html").read_text(encoding="utf-8")

    def test_every_scope_note_reaches_the_index(self):
        missing = [t for t, note in self.vocab.notes.items()
                   if t in self.vocab.vocabulary and html.escape(note) not in self.page]
        self.assertEqual([], missing,
                         f"scope notes written but not rendered: {missing}")

    def test_every_entry_term_reaches_the_index(self):
        missing = [syn for term, syns in self.vocab.synonyms.items()
                   for syn in syns if html.escape(syn) not in self.page]
        self.assertEqual([], missing,
                         f"entry terms that no search will ever find: {missing}")

    def test_no_entry_term_is_also_a_descriptor(self):
        """An entry term is never tagged with, so it must not look taggable."""
        clash = [s for s in self.vocab.entry_terms() if s in self.vocab.vocabulary]
        self.assertEqual([], clash, f"both descriptor and entry term: {clash}")

    def test_every_ring_points_at_a_term_that_has_work(self):
        """An entry term makes existing work findable; it never claims new work."""
        orphans = [t for t in self.vocab.synonyms if t not in self.vocab.vocabulary]
        self.assertEqual([], orphans,
                         f"synonym ring points at non-terms: {orphans}")


if __name__ == "__main__":
    unittest.main()
