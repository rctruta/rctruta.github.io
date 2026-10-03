"""Automated unit test suite for site tools, data schemas, and pipeline validation.

    python3 tools/test_tools.py

Tests data models (TAGS.yaml, writing.yaml, appearances.yaml), ensures no unknown
tags exist, verifies HTML anchor integrity, and enforces vocabulary contracts.
"""
import html
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def parse_tags_yaml(text):
    vocab, projects, section, facet = {}, {}, None, None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        if indent == 0 and line.endswith(":"):
            section = line[:-1]
            continue
        if section == "vocabulary":
            if indent == 2 and line.endswith(":"):
                facet = line[:-1]
                continue
            if indent == 4:
                term = line.split(":", 1)[0].strip()
                vocab[term] = facet
        elif section == "projects" and indent == 2:
            pid, rest = line.split(":", 1)
            projects[pid.strip()] = [
                t.strip() for t in rest.strip().strip("[]").split(",") if t.strip()
            ]
    return vocab, projects


class TestSitePipeline(unittest.TestCase):
    def setUp(self):
        self.tags_text = (ROOT / "data" / "TAGS.yaml").read_text()
        self.vocab, self.projects = parse_tags_yaml(self.tags_text)
        self.writing_text = (ROOT / "data" / "writing.yaml").read_text()
        self.appearances_text = (ROOT / "data" / "appearances.yaml").read_text()

    def test_vocabulary_terms_exist(self):
        """Verify standard vocabulary terms are present in TAGS.yaml."""
        expected_terms = [
            "Data modeling",
            "Data contracts",
            "Pre-commit gates",
            "Content addressing",
            "Benchmarking",
            "AI security",
            "AI evaluation",
            "Storytelling",
            "Knowledge graphs",
        ]
        for term in expected_terms:
            self.assertIn(term, self.vocab, f"Missing term '{term}' in vocabulary")

    def test_project_tags_are_in_vocabulary(self):
        """Verify every tag assigned to a project is in the controlled vocabulary."""
        unknown = {t: p for p, ts in self.projects.items() for t in ts if t not in self.vocab}
        self.assertEqual(len(unknown), 0, f"Project tags not in vocabulary: {unknown}")

    def test_writing_yaml_integrity(self):
        """Verify writing.yaml has no unfilled placeholders and valid tags."""
        self.assertNotIn("[YOURS]", self.writing_text, "Unfilled [YOURS] placeholder found")
        for m in re.finditer(r"^  tags: \[(.*)\]\s*$", self.writing_text, re.M):
            tags = [t.strip() for t in m.group(1).split(",") if t.strip()]
            for t in tags:
                self.assertIn(t, self.vocab, f"Writing tag '{t}' not in vocabulary")

    def test_appearances_yaml_integrity(self):
        """Verify appearances.yaml uses controlled vocabulary tags."""
        for m in re.finditer(r"^  tags: \[(.*)\]\s*$", self.appearances_text, re.M):
            tags = [t.strip() for t in m.group(1).split(",") if t.strip()]
            for t in tags:
                self.assertIn(t, self.vocab, f"Appearance tag '{t}' not in vocabulary")

    def test_html_proj_anchors_in_tags_yaml(self):
        """Verify every div.proj ID in work.html and teaching.html exists in TAGS.yaml."""
        for page_name in ("work.html", "teaching.html"):
            text = (ROOT / page_name).read_text()
            proj_ids = set(re.findall(r'<div class="proj" id="([^"]+)"', text))
            for pid in proj_ids:
                self.assertIn(pid, self.projects, f"ID '{pid}' in {page_name} not registered in TAGS.yaml")


if __name__ == "__main__":
    unittest.main()
