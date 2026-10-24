import re
import unittest

from model import (load_taxonomy, load_appearances)

from . import ROOT


class TestDocsMatchTheVocabulary(unittest.TestCase):
    """The document that says how the vocabulary is applied must not contradict it.

    The kinds table was typed into APPLICATION-RULES.md and also declared in
    TAGS.yaml. They agreed by luck; nothing checked them.
    """

    def test_org_authority_list_matches_the_appearances(self):
        """An authority file that can disagree with its own records is not one.

        The org list was hand-maintained so one show spelled two ways would not
        split every count grouping by `org`. Nothing checked it: removing a talk
        on 2026-10-16 left its org behind pointing at nothing, and three orgs
        that were in use had never been added.
        """
        doc = ROOT / "data" / "APPLICATION-RULES.md"
        if not doc.exists():
            self.skipTest("APPLICATION-RULES.md not present")
        text = doc.read_text()
        if "<!-- orgs:start -->" not in text:
            self.skipTest("org list not generated in this copy")
        listed = set(re.findall(r"^- `([^`]+)`$",
                                text.split("<!-- orgs:start -->")[1]
                                    .split("<!-- orgs:end -->")[0], re.M))
        vocab = load_taxonomy()
        used = {a.org for a in load_appearances(vocab) if a.org}
        self.assertEqual(used, listed,
                         "the org authority list disagrees with "
                         "appearances.yaml; run python3 tools/build_rules_doc.py")

    def test_kinds_table_matches_the_controlled_vocabulary(self):
        doc = ROOT / "data" / "APPLICATION-RULES.md"
        if not doc.exists():
            self.skipTest("APPLICATION-RULES.md not present")
        text = doc.read_text()
        kinds = load_taxonomy().kinds
        in_doc = dict(re.findall(r"^\| `([^`]+)` \| `([^`]+)` \|", text, re.M))
        self.assertEqual({k: m.category for k, m in kinds.items()}, in_doc,
                         "the kinds table disagrees with the controlled vocabulary; "
                         "run python3 tools/build_rules_doc.py")
