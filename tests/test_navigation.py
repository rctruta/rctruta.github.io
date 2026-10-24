import re
import unittest


from . import ROOT


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
