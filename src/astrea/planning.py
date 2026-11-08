"""Strict configuration and deterministic, side-effect-free planning."""

import copy
import hashlib
import json
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from jsonschema import Draft202012Validator, validators

from .catalog import FIXTURES, LIMITS, PARAMETERS, PROFILES
from .errors import AstreaError
from .jsonio import load, read_bytes
from .models import Case

STRICT_VALIDATOR = validators.extend(
    Draft202012Validator,
    type_checker=Draft202012Validator.TYPE_CHECKER.redefine(
        "integer", lambda checker, value: type(value) is int
    ),
)


def check_schema(value, schema):
    errors = sorted(
        STRICT_VALIDATOR(schema).iter_errors(value), key=lambda e: str(list(e.path))
    )
    if errors:
        error = errors[0]
        raise AstreaError(
            "E_CONFIG",
            "Invalid field type, value, or unknown field",
            ".".join(map(str, error.absolute_path)) or "plan",
        )


def template(pack="core"):
    return {
        "seed": 0,
        "include_stress": pack == "stress",
        "limits": LIMITS.copy(),
        "selection": {
            "packs": [pack],
            "fixtures": [],
            "locales": [],
            "client_profile": None,
            "provider_profile": None,
        },
        "fixture_parameters": {},
        "domains": ["example.test", "newletter.test", "blue.test"],
        "periods": [
            {
                "id": "january-2025",
                "title": "January 2025",
                "start": "2025-01-01",
                "end": "2025-01-31",
                "count": 100,
            }
        ],
    }


def domains(values):
    if not isinstance(values, list) or not 1 <= len(values) <= 1000:
        raise AstreaError("E_CONFIG", "Provide between 1 and 1000 domains", "domains")
    normalized = []
    for value in values:
        if not isinstance(value, str):
            raise AstreaError("E_CONFIG", "Domain must be a string", "domains")
        value = value.strip().lower()
        labels = value.split(".")
        if (
            len(value) > 253
            or len(labels) < 2
            or labels[-1] != "test"
            or any(
                not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", p)
                for p in labels
            )
            or value in normalized
        ):
            raise AstreaError(
                "E_CONFIG", "Invalid or duplicate .test domain", "domains"
            )
        normalized.append(value)
    return normalized


def normalize(value, base=Path(".")):
    schema = json.loads(
        Path(__file__).with_name("data").joinpath("plan.schema.json").read_text()
    )
    check_schema(value, schema)
    plan = copy.deepcopy(value)
    if "domain_file" in plan:
        source = Path(plan.pop("domain_file"))
        if not source.name.endswith(".astrea-domains.txt"):
            raise AstreaError(
                "E_CONFIG", "Expected .astrea-domains.txt suffix", "domain_file"
            )
        try:
            values = read_bytes(base / source, 65536).decode("utf-8").splitlines()
        except UnicodeError as exc:
            raise AstreaError(
                "E_CONFIG", "Domain file must be UTF-8", "domain_file"
            ) from exc
        plan["domains"] = [v for v in values if v.strip()]
    plan["domains"] = domains(plan["domains"])
    previous_end = None
    seen = set()
    total = 0
    for period in plan["periods"]:
        try:
            start, end = (date.fromisoformat(period[key]) for key in ("start", "end"))
        except ValueError as exc:
            raise AstreaError("E_CONFIG", "Invalid calendar date", "periods") from exc
        if (
            end < start
            or (previous_end is not None and start <= previous_end)
            or period["id"] in seen
            or not period["title"].strip()
        ):
            raise AstreaError(
                "E_CONFIG",
                "Periods must have unique IDs and ordered nonoverlapping dates",
                "periods",
            )
        previous_end = end
        seen.add(period["id"])
        total += period["count"]
    if total > 10000:
        raise AstreaError("E_LIMIT", "Too many messages", "periods", 10000)
    for field in ("packs", "fixtures", "locales"):
        plan["selection"][field] = sorted(set(plan["selection"][field]))
    return plan


def cases(plan):
    selection = plan["selection"]
    packs = set(selection["packs"])
    if not packs or not packs <= {"core", "stress"}:
        raise AstreaError(
            "E_SELECTION", "Unsupported or empty pack selection", "selection.packs"
        )
    explicit, locales = set(selection["fixtures"]), set(selection["locales"])
    available = {key: row for key, row in FIXTURES.items() if row["pack"] in packs}
    if not explicit <= available.keys():
        raise AstreaError(
            "E_SELECTION", "Fixture unavailable in selected packs", "selection.fixtures"
        )
    selected = {
        key: row for key, row in available.items() if not explicit or key in explicit
    }
    if (
        explicit
        and locales
        and any(row["locale"] not in locales for row in selected.values())
    ):
        raise AstreaError(
            "E_SELECTION",
            "Explicit fixture has no selected locale",
            "selection.locales",
        )
    selected = {
        key: row
        for key, row in selected.items()
        if not locales or row["locale"] in locales
    }
    if not selected or not locales <= {row["locale"] for row in selected.values()}:
        raise AstreaError(
            "E_SELECTION",
            "No matching fixtures for requested locales",
            "selection.locales",
        )
    if (
        any(row["pack"] == "stress" for row in selected.values())
        and not plan["include_stress"]
    ):
        raise AstreaError(
            "E_SELECTION", "Stress selection requires include_stress", "include_stress"
        )
    if not plan["fixture_parameters"].keys() <= selected.keys():
        raise AstreaError(
            "E_CONFIG",
            "Parameters reference an unselected fixture",
            "fixture_parameters",
        )
    result = []
    for key, row in sorted(selected.items()):
        client = selection["client_profile"] or row["client_profile"]
        provider = selection["provider_profile"] or row["provider_profile"]
        if (
            client not in PROFILES
            or provider not in PROFILES
            or PROFILES[client]["kind"] != "client"
            or PROFILES[provider]["kind"] != "provider"
            or provider not in PROFILES[client]["valid_pairings"].split(";")
        ):
            raise AstreaError(
                "E_PROFILE_PAIR", "Unsupported client/provider combination", key
            )
        supplied = plan["fixture_parameters"].get(key, {})
        specs = PARAMETERS.get(key, {})
        if not supplied.keys() <= specs.keys():
            raise AstreaError("E_CONFIG", "Unsupported fixture parameter", key)
        variants = [{}]
        for name, spec in specs.items():
            if spec["type"] == "integer":
                value = supplied.get(name, int(spec["default"]))
                low, high = map(int, spec["allowed"].split(".."))
                ceiling = plan["limits"][
                    "max_depth" if name == "depth" else "max_parts"
                ]
                if type(value) is not int or not low <= value <= min(high, ceiling):
                    raise AstreaError(
                        "E_LIMIT",
                        "Invalid fixture parameter or ceiling",
                        key + "." + name,
                        min(high, ceiling),
                    )
                choices = [value]
            else:
                choices = spec["allowed"].split(";")
                if name in supplied:
                    if supplied[name] not in choices:
                        raise AstreaError(
                            "E_CONFIG", "Unknown fixture variant", key + "." + name
                        )
                    choices = [supplied[name]]
            variants = [
                dict(v, **{name: choice}) for v in variants for choice in choices
            ]
        result.extend(
            Case(key, row["locale"], client, provider, params) for params in variants
        )
    return sorted(result, key=lambda case: case.key)


def preview(value, base=Path(".")):
    plan = normalize(value, base)
    selected = cases(plan)
    minimum = sum(case.size for case in selected)
    messages = []
    for period in plan["periods"]:
        count = period["count"]
        if count < minimum:
            raise AstreaError(
                "E_COVERAGE_COUNT",
                "Period count is below coverage minimum",
                period["id"],
                minimum,
            )
        allocated = []
        occurrences = {case.key: 0 for case in selected}
        while len(allocated) < count:
            progress = False
            for case in selected:
                if len(allocated) + case.size <= count:
                    occurrence = occurrences[case.key]
                    allocated.extend(
                        (case, occurrence, member) for member in range(case.size)
                    )
                    occurrences[case.key] += 1
                    progress = True
            if not progress:
                raise AstreaError(
                    "E_COVERAGE_COUNT",
                    "Count cannot fit complete fixture groups",
                    period["id"],
                )
        start = datetime.fromisoformat(period["start"]).replace(tzinfo=UTC)
        end = datetime.fromisoformat(period["end"]).replace(tzinfo=UTC) + timedelta(
            days=1, seconds=-1
        )
        length = int((end - start).total_seconds())
        for i, (case, occurrence, member) in enumerate(allocated):
            offset = i * length // (count - 1) if count > 1 else (length + 1) // 2
            messages.append(
                {
                    "index": len(messages) + 1,
                    "period_index": i,
                    "period_id": period["id"],
                    "date": (start + timedelta(seconds=offset))
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "fixture_id": case.fixture_id,
                    "locale": case.locale,
                    "profiles": {
                        "client": {"id": case.client},
                        "provider": {"id": case.provider},
                    },
                    "occurrence": occurrence,
                    "thread_member_index": member,
                    "parameters": case.parameters.copy(),
                }
            )
    if "messages" in plan and plan["messages"] != messages:
        raise AstreaError(
            "E_CONFIG", "Saved message list conflicts with computed plan", "messages"
        )
    plan["messages"] = messages
    return plan


def read_plan(path):
    path = Path(path)
    if not path.name.endswith(".astrea-plan.json"):
        raise AstreaError("E_CONFIG", "Expected .astrea-plan.json suffix", "plan")
    return preview(load(path), path.parent)


def digest(plan, message, field):
    identity = [
        plan["seed"],
        message["period_id"],
        message["fixture_id"],
        message["locale"],
        message["occurrence"],
        message["thread_member_index"],
        field,
    ]
    return hashlib.sha256(
        json.dumps(identity, ensure_ascii=True, separators=(",", ":")).encode()
    ).hexdigest()


def domain(plan, message, offset):
    return plan["domains"][(message["period_index"] + offset) % len(plan["domains"])]
