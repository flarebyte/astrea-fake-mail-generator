"""Regression tests for concept links and searchable CSV integrity."""

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/validate-specs.py"
SPEC = importlib.util.spec_from_file_location("validate_specs", SCRIPT)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ValidateSpecsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.examples = Path(self.temporary.name)
        self.write_csv("concepts.csv", [
            ["id", "description", "parent"],
            ["fixture", "Test cases", ""],
            ["fixture.content", "Text bodies", "fixture"],
        ])
        self.write_csv("fixtures.csv", [
            ["id", "concept", "tags"],
            ["fixture.test", "fixture.content", "plain-text,ascii"],
        ])
        self.message = {
            "fixture_id": "fixture.test", "concept": "fixture.content",
            "tags": ["plain-text", "ascii"],
        }
        self.write_manifest()

    def write_csv(self, name, rows):
        with (self.examples / name).open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream, lineterminator="\n").writerows(rows)

    def write_manifest(self):
        (self.examples / "example.astrea-manifest.json").write_text(
            json.dumps({"messages": [self.message]}), encoding="utf-8",
        )

    def errors(self):
        return VALIDATOR.validate(self.examples)

    def assert_error(self, substring):
        self.assertTrue(any(substring in error for error in self.errors()), self.errors())

    def test_valid_quoted_tags_and_manifest(self):
        self.assertEqual(self.errors(), [])
        self.assertIn('"plain-text,ascii"', (self.examples / "fixtures.csv").read_text())

    def test_optional_tags_can_be_empty(self):
        self.write_csv("fixtures.csv", [["id", "concept", "tags"], ["fixture.test", "fixture.content", ""]])
        self.message["tags"] = []
        self.write_manifest()
        self.assertEqual(self.errors(), [])

    def test_missing_registry(self):
        (self.examples / "concepts.csv").unlink()
        self.assert_error("canonical concept registry is required")

    def test_unknown_concept(self):
        self.write_csv("fixtures.csv", [["id", "concept", "tags"], ["fixture.test", "fixture.unknown", ""]])
        self.assert_error("unknown concept")

    def test_duplicate_record_id(self):
        self.write_csv("extra.csv", [["id"], ["row.same"], ["row.same"]])
        self.assert_error("duplicate id row.same")

    def test_duplicate_concept_id(self):
        with (self.examples / "concepts.csv").open("a") as stream:
            stream.write("fixture.content,Duplicate,fixture\n")
        self.assert_error("duplicate id fixture.content")

    def test_unknown_parent(self):
        self.write_csv("concepts.csv", [["id", "description", "parent"], ["fixture.content", "Bodies", "fixture"]])
        self.assert_error("unknown parent fixture")

    def test_cyclic_or_nonhierarchical_parents(self):
        self.write_csv("concepts.csv", [
            ["id", "description", "parent"],
            ["fixture", "Cases", "fixture.content"],
            ["fixture.content", "Bodies", "fixture"],
        ])
        self.assert_error("parent must be")

    def test_invalid_concept_id(self):
        self.write_csv("concepts.csv", [["id", "description", "parent"], ["Fixture-Content", "Bodies", ""]])
        self.assert_error("invalid hierarchical concept id")

    def test_duplicate_columns(self):
        self.write_csv("extra.csv", [["id", "id"], ["one", "two"]])
        self.assert_error("duplicate column names")

    def test_missing_columns(self):
        (self.examples / "fixtures.csv").write_text("id,concept,tags\nfixture.test,fixture.content\n")
        self.assert_error("expected 3 columns, found 2")

    def test_unquoted_tag_list_creates_extra_column(self):
        (self.examples / "fixtures.csv").write_text("id,concept,tags\nfixture.test,fixture.content,plain-text,ascii\n")
        self.assert_error("expected 3 columns, found 4")

    def test_unescaped_quote_in_unquoted_field(self):
        (self.examples / "extra.csv").write_text('id,text\nrow.one,unescaped"quote\n')
        self.assert_error("invalid CSV quoting")

    def test_unterminated_quote(self):
        (self.examples / "fixtures.csv").write_text('id,concept,tags\nfixture.test,fixture.content,"plain-text,ascii\n')
        self.assert_error("cannot read valid UTF-8 CSV")

    def test_multiline_record(self):
        self.write_csv("extra.csv", [["id", "text"], ["row.one", "two\nlines"]])
        self.assert_error("one physical line")

    def test_empty_and_duplicate_tags(self):
        for tags in ["ascii,ascii", "ascii,", "ascii, plain-text"]:
            with self.subTest(tags=tags):
                self.write_csv("fixtures.csv", [["id", "concept", "tags"], ["fixture.test", "fixture.content", tags]])
                self.assert_error("tags must be unique lowercase")

    def test_required_concept_column(self):
        self.write_csv("features.csv", [["id"], ["feature.one"]])
        self.assert_error("missing concept column")

    def test_manifest_known_but_wrong_concept(self):
        self.message["concept"] = "fixture"
        self.write_manifest()
        self.assert_error("concept must match fixture")

    def test_manifest_wrong_tags(self):
        self.message["tags"] = "plain-text,ascii"
        self.write_manifest()
        self.assert_error("tags must match fixture")

    def test_manifest_invalid_types(self):
        self.message["concept"] = []
        self.write_manifest()
        self.assert_error("unknown concept")

    def test_manifest_unknown_fixture(self):
        self.message["fixture_id"] = "fixture.missing"
        self.write_manifest()
        self.assert_error("unknown fixture_id")

    def test_manifest_duplicate_json_keys(self):
        (self.examples / "example.astrea-manifest.json").write_text('{"messages": [], "messages": []}')
        self.assert_error("duplicate JSON key messages")

    def test_repository_specs(self):
        self.assertEqual(VALIDATOR.validate(SCRIPT.parents[1] / "doc/design-meta/examples"), [])


if __name__ == "__main__":
    unittest.main()
