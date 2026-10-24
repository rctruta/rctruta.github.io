import re
import unittest


from . import ROOT


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
