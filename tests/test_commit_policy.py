"""Exercise the installed commit-msg hook without creating commits."""
import pathlib
import subprocess
import tempfile
import unittest

from . import ROOT


class TestCommitPolicy(unittest.TestCase):
    def check_message(self, message):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'message.txt'
            path.write_text(message)
            return subprocess.run(
                [str(ROOT / '.githooks/commit-msg'), str(path)],
                cwd=ROOT, capture_output=True, text=True,
            )

    def test_conventional_messages_pass(self):
        for message in (
            'fix: validate local links\n',
            'feat(contracts)!: use stable concept IDs\n\n'
            'BREAKING CHANGE: tags reference concept IDs.\n',
        ):
            with self.subTest(message=message):
                result = self.check_message(message)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_nonconventional_messages_fail(self):
        for message in ('Update website\n', 'unknown: update website\n', 'fix: \n', '', '  \n'):
            with self.subTest(message=message):
                result = self.check_message(message)
                self.assertNotEqual(0, result.returncode)
