#!/usr/bin/env python3
"""Check searchable specification CSVs and their manifest metadata (stdlib only)."""

import argparse
import csv
import json
import re
from pathlib import Path


CONCEPT_TABLES = {
    "cli.csv", "constraints.csv", "features.csv", "fixtures.csv",
    "plan-fields.csv", "tech.csv",
}
CONCEPT_ID = re.compile(r"[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)*")
TAG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
CSV_LINE = re.compile(r'(?:[^,"\r\n]*|"(?:[^"\r\n]|"")*")(?:,(?:[^,"\r\n]*|"(?:[^"\r\n]|"")*"))*')


def read_table(path, errors):
    try:
        text = path.read_text(encoding="utf-8")
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.reader(stream, strict=True))
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"{path.name}: cannot read valid UTF-8 CSV: {exc}")
        return None
    if not rows:
        errors.append(f"{path.name}: empty CSV")
        return None
    header = rows[0]
    if not header or len(set(header)) != len(header) or any(not key.strip() for key in header):
        errors.append(f"{path.name}: empty or duplicate column names")
        return None
    if "id" not in header:
        errors.append(f"{path.name}: missing id column")
        return None
    if path.name in CONCEPT_TABLES and "concept" not in header:
        errors.append(f"{path.name}: missing concept column")
    if path.name == "fixtures.csv" and "tags" not in header:
        errors.append(f"{path.name}: missing tags column")
    for number, line in enumerate(text.splitlines(), 1):
        if not CSV_LINE.fullmatch(line):
            errors.append(f"{path.name}:{number}: invalid CSV quoting or multiline record")
    if len(text.splitlines()) != len(rows):
        errors.append(f"{path.name}: each record must occupy one physical line")
    if len(rows) == 1:
        errors.append(f"{path.name}: no data records")
    records = []
    seen = set()
    for number, values in enumerate(rows[1:], 2):
        where = f"{path.name}:{number}"
        if len(values) != len(header):
            errors.append(f"{where}: expected {len(header)} columns, found {len(values)}")
            continue
        if any("\n" in value or "\r" in value for value in values):
            errors.append(f"{where}: multiline cell is not searchable as one record")
        row = dict(zip(header, values))
        identity = row["id"]
        if not identity or identity != identity.strip():
            errors.append(f"{where}: id must be nonempty without surrounding whitespace")
        elif identity in seen:
            errors.append(f"{where}: duplicate id {identity}")
        seen.add(identity)
        if "tags" in row:
            tags = row["tags"].split(",") if row["tags"] else []
            if len(tags) != len(set(tags)) or any(not TAG.fullmatch(tag) for tag in tags):
                errors.append(f"{where}: tags must be unique lowercase comma-separated keywords")
        records.append((number, row))
    return header, records


def unique_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key}")
        result[key] = value
    return result


def validate(examples):
    errors = []
    if not examples.is_dir():
        return [f"{examples}: specification directory does not exist"]
    tables = {}
    for path in sorted(examples.glob("*.csv")):
        table = read_table(path, errors)
        if table is not None:
            tables[path.name] = table
    registry = tables.get("concepts.csv")
    if registry is None:
        errors.append("concepts.csv: canonical concept registry is required")
        return errors
    if registry[0] != ["id", "description", "parent"]:
        errors.append("concepts.csv: columns must be id,description,parent")
        return errors
    concepts = {row["id"]: row for number, row in registry[1]}
    for number, row in registry[1]:
        identity, parent = row["id"], row["parent"]
        where = f"concepts.csv:{number}"
        if not CONCEPT_ID.fullmatch(identity):
            errors.append(f"{where}: invalid hierarchical concept id {identity}")
        if not row["description"].strip():
            errors.append(f"{where}: description must be nonempty")
        expected_parent = identity.rsplit(".", 1)[0] if "." in identity else ""
        if parent != expected_parent:
            errors.append(f"{where}: parent must be {expected_parent!r}")
        if parent and parent not in concepts:
            errors.append(f"{where}: unknown parent {parent}")
    for name, (header, records) in tables.items():
        if "concept" in header:
            for number, row in records:
                if row["concept"] not in concepts:
                    errors.append(f"{name}:{number}: unknown concept {row['concept']!r}")
    fixtures = {row["id"]: row for number, row in tables.get("fixtures.csv", ([], []))[1]}
    for path in sorted(examples.glob("*.astrea-manifest.json")):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_json_keys)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{path.name}: invalid JSON: {exc}")
            continue
        if not isinstance(manifest, dict) or not isinstance(manifest.get("messages"), list):
            errors.append(f"{path.name}: messages must be an array")
            continue
        for index, message in enumerate(manifest["messages"]):
            where = f"{path.name}:messages[{index}]"
            if not isinstance(message, dict):
                errors.append(f"{where}: message must be an object")
                continue
            fixture_id, concept = message.get("fixture_id"), message.get("concept")
            if not isinstance(fixture_id, str) or fixture_id not in fixtures:
                errors.append(f"{where}: unknown fixture_id {fixture_id!r}")
                continue
            if not isinstance(concept, str) or concept not in concepts:
                errors.append(f"{where}: unknown concept {concept!r}")
            fixture = fixtures[fixture_id]
            if concept != fixture.get("concept"):
                errors.append(f"{where}: concept must match fixture {fixture_id}")
            expected_tags = fixture.get("tags", "").split(",") if fixture.get("tags") else []
            if message.get("tags") != expected_tags:
                errors.append(f"{where}: tags must match fixture {fixture_id} as a JSON array")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--examples-dir", type=Path,
        default=Path(__file__).resolve().parents[1] / "doc/design-meta/examples",
    )
    args = parser.parse_args()
    errors = validate(args.examples_dir)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("Specification CSVs, concepts, and manifest metadata are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
