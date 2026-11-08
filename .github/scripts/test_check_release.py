"""Offline regression checks for release eligibility and registry failures."""

import importlib.util
import io
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

SPEC = importlib.util.spec_from_file_location(
    "check_release", Path(__file__).with_name("check_release.py")
)
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class ReleaseTests(unittest.TestCase):
    def run_check(
        self,
        version="1.2.3",
        lock_version="1.2.3",
        status=404,
        tag_status=1,
        ref="refs/heads/main",
        tip="abc123",
        expected="1.2.3",
    ):
        def read(path, *args, **kwargs):
            if path.name == "uv.lock":
                return (
                    '[[package]]\nname="example"\n'
                    f'version="{lock_version}"\nsource={{editable="."}}\n'
                )
            return f'[project]\nname="example"\nversion="{version}"\n'

        def registry(*args, **kwargs):
            if status == 200:
                return MagicMock()
            if status == "network":
                raise urllib.error.URLError("offline")
            raise urllib.error.HTTPError(
                "https://pypi.org/pypi/example/1.2.3/json",
                status,
                "test",
                {},
                io.BytesIO(),
            )

        def git(*args):
            if args[0] == "show-ref":
                return MagicMock(returncode=tag_status)
            return MagicMock(returncode=0, stdout=tip + "\n")

        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "output"
            environment = {
                "GITHUB_REF": ref,
                "GITHUB_SHA": "abc123",
                "GITHUB_OUTPUT": str(output),
                "EXPECTED_VERSION": expected,
            }
            with (
                patch.object(Path, "read_text", read),
                patch.dict(os.environ, environment),
                patch.object(CHECK, "git", side_effect=git),
                patch("urllib.request.urlopen", side_effect=registry),
            ):
                CHECK.main()
            return output.read_text()

    def test_new_version(self):
        self.assertEqual(self.run_check(), "version=1.2.3\ntag=v1.2.3\n")

    def test_invalid_version(self):
        for value in ("1.2", "01.2.3", "1.2.3rc1", "1.2.3-beta.1"):
            with (
                self.subTest(value=value),
                self.assertRaisesRegex(SystemExit, "stable"),
            ):
                self.run_check(version=value)

    def test_lock_mismatch(self):
        with self.assertRaisesRegex(SystemExit, "must match"):
            self.run_check(lock_version="1.2.2")

    def test_main_only(self):
        with self.assertRaisesRegex(SystemExit, "restricted to main"):
            self.run_check(ref="refs/heads/feature")
        with self.assertRaisesRegex(SystemExit, "current tip"):
            self.run_check(tip="different")

    def test_approved_version_unchanged(self):
        with self.assertRaisesRegex(SystemExit, "Version changed"):
            self.run_check(expected="1.2.2")

    def test_tags(self):
        for status in (0, 128):
            with self.subTest(status=status), self.assertRaises(SystemExit):
                self.run_check(tag_status=status)

    def test_registry_duplicates(self):
        with self.assertRaisesRegex(SystemExit, "already published"):
            self.run_check(status=200)

    def test_registry_failures(self):
        for status in (403, 429, 503, "network"):
            with (
                self.subTest(status=status),
                self.assertRaisesRegex(SystemExit, "Unable to check PyPI"),
            ):
                self.run_check(status=status)


if __name__ == "__main__":
    unittest.main()
