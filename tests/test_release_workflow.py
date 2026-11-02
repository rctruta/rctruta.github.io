"""Check release authorization and immutable action references."""
import re
import unittest

import yaml

from . import ROOT


class TestReleaseWorkflow(unittest.TestCase):
    def setUp(self):
        self.workflow = yaml.load((ROOT / '.github/workflows/test.yaml').read_text(), Loader=yaml.BaseLoader)

    def test_deployment_requires_successful_main_build(self):
        deploy = self.workflow['jobs']['deploy']
        self.assertEqual('test', deploy['needs'])
        self.assertEqual("github.event_name == 'push' && github.ref == 'refs/heads/main'", deploy['if'])
        steps = self.workflow['jobs']['test']['steps']
        upload = next(step for step in steps if 'upload-pages-artifact@' in step.get('uses', ''))
        self.assertEqual('dist', upload['with']['path'])
        self.assertLess(
            next(i for i, step in enumerate(steps) if step.get('name') == 'Refuse stale committed output'),
            steps.index(upload),
        )

    def test_action_references_are_immutable(self):
        for job in self.workflow['jobs'].values():
            for step in job['steps']:
                if 'uses' in step:
                    self.assertTrue(re.fullmatch(r'actions/[a-z-]+@[0-9a-f]{40}', step['uses']))
