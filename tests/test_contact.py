import re
import unittest

from config_loader import load_config
from model import (load_taxonomy)

from . import ROOT


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
