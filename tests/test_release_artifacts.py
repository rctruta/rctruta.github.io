"""Check generated search integrity and the public deployment boundary."""
import json
import pathlib
import shutil
import tempfile
import unittest

from . import ROOT
from contracts import ContractError
from package_site import package_site
from search_contract import validate_search


class TestReleaseArtifacts(unittest.TestCase):
    def test_changed_search_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / 'pagefind'
            shutil.copytree(ROOT / 'pagefind', target)
            (target / 'pagefind.js').write_text('changed')
            with self.assertRaisesRegex(ContractError, 'artifacts'):
                validate_search(target)

    def test_stale_search_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / 'pagefind'
            shutil.copytree(ROOT / 'pagefind', target)
            path = target / 'build-manifest.json'
            data = json.loads(path.read_text())
            data['inputs']['work.html'] = 'stale'
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ContractError, 'inputs'):
                validate_search(target)

    def test_package_contains_only_public_files(self):
        with tempfile.TemporaryDirectory() as directory:
            target = package_site(pathlib.Path(directory) / 'site')
            self.assertTrue((target / 'index.html').is_file())
            self.assertTrue((target / 'pagefind/build-manifest.json').is_file())
            self.assertFalse((target / '.git').exists())
            self.assertFalse((target / 'tools').exists())
            self.assertFalse((target / 'data').exists())

    def test_package_rejects_source_directories(self):
        with self.assertRaises(ContractError):
            package_site(ROOT / 'assets')
