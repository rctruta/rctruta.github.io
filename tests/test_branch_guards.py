"""Exercise Git hooks in isolated repositories."""
import os
import pathlib
import subprocess
import tempfile
import unittest

from . import ROOT


class TestBranchGuards(unittest.TestCase):
    def test_commits_require_a_work_branch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            subprocess.run(['git', 'init', '--quiet', '-b', 'main'], cwd=root, check=True)
            binary = root / 'bin'
            binary.mkdir()
            runner = binary / 'pre-commit'
            runner.write_text('#!/bin/sh\nexit 0\n')
            runner.chmod(0o755)
            env = {**os.environ, 'PATH': str(binary) + os.pathsep + os.environ['PATH']}
            hook = str(ROOT / '.githooks/pre-commit')
            result = subprocess.run([hook], cwd=root, env=env, capture_output=True)
            self.assertNotEqual(0, result.returncode)
            subprocess.run(['git', 'switch', '--quiet', '-c', 'fix/example'], cwd=root, check=True)
            result = subprocess.run([hook], cwd=root, env=env, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)

    def test_pushes_to_main_are_rejected(self):
        for branch, expected in [('main', 1), ('fix/example', 0)]:
            with self.subTest(branch=branch):
                result = subprocess.run(
                    [str(ROOT / '.githooks/pre-push')],
                    input=f'refs/heads/fix/example abc refs/heads/{branch} def\n',
                    capture_output=True, text=True,
                )
                self.assertEqual(expected, result.returncode)
