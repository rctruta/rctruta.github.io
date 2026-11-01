"""Verify the commit guard inspects the index, even when worktree bytes differ."""
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from . import ROOT


class TestStagedPrivacy(unittest.TestCase):
    def test_staged_contact_is_rejected_after_worktree_change_or_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / 'tools').mkdir()
            shutil.copy2(ROOT / 'tools/check_private.py', root / 'tools/check_private.py')
            subprocess.run(['git', 'init', '--quiet'], cwd=root, check=True)
            page = root / 'page.md'
            page.write_text('private' + chr(64) + 'invalid.test\n')
            subprocess.run(['git', 'add', 'page.md'], cwd=root, check=True)
            for state in ('replaced', 'removed'):
                with self.subTest(state=state):
                    if state == 'replaced':
                        page.write_text('No contact data in working tree.\n')
                    else:
                        page.unlink()
                    result = subprocess.run(
                        ['python3', 'tools/check_private.py'], cwd=root,
                        capture_output=True, text=True,
                    )
                    self.assertEqual(1, result.returncode)
                    self.assertIn('BLOCKED', result.stdout)
