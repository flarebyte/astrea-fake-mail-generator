"""Installed catalog; deliberately independent of checkout documentation."""

import json
from importlib.resources import files

DATA = json.loads(files("astrea").joinpath("data/catalog.json").read_text())
FIXTURES = {row["id"]: row for row in DATA["fixtures"]}
PROFILES = {row["id"]: row for row in DATA["profiles"]}
PARAMETERS = {}
for row in DATA["fixture-parameters"]:
    PARAMETERS.setdefault(row["fixture_id"], {})[row["parameter"]] = row
LIMITS = {
    "max_message_bytes": 5242880,
    "max_batch_bytes": 268435456,
    "max_depth": 64,
    "max_parts": 1000,
    "max_header_bytes": 65536,
}
REGIONS = {
    locale: row for row in DATA["regions"] for locale in row["locales"].split(";")
}


def listing(kind):
    if kind == "fixtures":
        return [FIXTURES[key] for key in sorted(FIXTURES)]
    if kind == "profiles":
        return [PROFILES[key] for key in sorted(PROFILES)]
    if kind == "locales":
        return sorted({row["locale"] for row in FIXTURES.values()})
    if kind == "limits":
        return LIMITS.copy()
    return [
        {"id": "core", "cases": 15, "minimum_messages": 17},
        {"id": "stress", "cases": 16, "minimum_messages": 16},
    ]
