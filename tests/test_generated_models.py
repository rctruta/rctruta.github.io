"""Verify generated models are used and schema changes invalidate them."""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from . import ROOT
from contracts import read_document
from generated.work_schema import Project
from model import load_employment, load_taxonomy, load_work_sections


class TestGeneratedModels(unittest.TestCase):
    def test_public_loader_uses_generated_model_with_concept_ids(self):
        item = load_work_sections(load_taxonomy())[0].items[0]
        self.assertIsInstance(item, Project)
        self.assertEqual(read_document('work')['sections'][0]['items'][0]['tags'], item.tags)

    def test_generated_fields_reject_missing_unknown_and_wrong_types(self):
        original = read_document('work')['sections'][0]['items'][0]
        variants = [{**original, 'title': 123}, {**original, 'unexpected': True},
                    {key: value for key, value in original.items() if key != 'activity'}]
        for data in variants:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                Project.model_validate(data)

    def test_changed_schema_requires_regeneration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            shutil.copy2(ROOT / 'pyproject.toml', root / 'pyproject.toml')
            shutil.copytree(ROOT / 'schemas', root / 'schemas')
            shutil.copytree(ROOT / 'tools/generated', root / 'tools/generated')
            schema = root / 'schemas/work.schema.json'
            schema.write_text(schema.read_text().replace('"title": "Portfolio Work document"',
                                                        '"title": "Changed Work document"'))
            result = subprocess.run([sys.executable, '-m', 'datamodel_code_generator', '--check'],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertIn('work_schema.py', result.stdout + result.stderr)

    def test_private_employment_uses_yaml_and_generated_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'employment.yaml'
            path.write_text('tagline: >-\n  Data systems\n  and teaching\nroles:\n'
                            '  - role: Engineer\n    start: "2020"\n    end: Present\n'
                            '    work_ids: [example]\n')
            with patch('model.EMPLOYMENT_PATH', path):
                self.assertEqual('Data systems and teaching', load_employment({'example'}).tagline)
                with self.assertRaisesRegex(ValueError, 'unknown work IDs'):
                    load_employment(set())
                path.write_text('roles: []\nroles: []\n')
                with self.assertRaisesRegex(ValueError, 'duplicate mapping key'):
                    load_employment()
