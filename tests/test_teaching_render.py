"""Check that validated Teaching data survives template rendering."""
import html
import unittest

from contracts import ROOT, content_document


class TestTeachingRender(unittest.TestCase):
    def test_content_and_optional_sections_follow_source(self):
        source = content_document("teaching")
        page = html.unescape((ROOT / "teaching.html").read_text())

        for material in source["materials"]:
            self.assertIn(f'id="{material["id"]}"', page)
        for degree in source["education"]["degrees"]:
            self.assertIn(degree["degree"], page)

        testimonials = source["testimonials"]
        expected_quotes = 1 + sum(len(group["items"]) for group in testimonials.values())
        self.assertEqual(expected_quotes, page.count('class="praise"'))

        self.assertEqual(
            bool(source["education"].get("honours")),
            "<h3>Honours</h3>" in page,
        )
        service = source.get("service") or {}
        show_service = any(service.get(key) for key in (
            "reviewing", "outreach", "outreach_note", "volunteering", "affiliations"
        ))
        self.assertEqual(show_service, 'id="service"' in page)
        self.assertEqual(show_service, 'href="#service"' in page)
