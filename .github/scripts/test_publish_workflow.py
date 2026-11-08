"""Security policy: external publishing workflow actions must be immutable."""

import re
import unittest
from pathlib import Path


class PublishingPolicyTests(unittest.TestCase):
    def test_every_external_action_uses_a_full_commit_sha(self):
        workflow = Path(__file__).parents[1] / "workflows/publish.yaml"
        actions = re.findall(r"^\s*- uses:\s+(\S+)", workflow.read_text(), re.MULTILINE)
        self.assertTrue(actions)
        for action in actions:
            with self.subTest(action=action):
                self.assertRegex(action, r"^[\w-]+/[\w.-]+@[a-f0-9]{40}$")


if __name__ == "__main__":
    unittest.main()
