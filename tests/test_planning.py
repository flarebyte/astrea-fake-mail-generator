"""Planning invariants, strict inputs, and installed specification parity."""

import copy
import csv
import json
from pathlib import Path

import pytest

from astrea.catalog import DATA, LIMITS, listing
from astrea.errors import AstreaError
from astrea.jsonio import load
from astrea.planning import cases, digest, domains, preview, read_plan, template

ROOT = Path(__file__).resolve().parents[1]


def single(fixture="fixture.uk.plain", count=1, pack="core"):
    plan = template(pack)
    plan["selection"]["fixtures"] = [fixture]
    plan["periods"][0]["count"] = count
    return plan


def test_installed_catalog_matches_authored_specification():
    for name, installed in DATA.items():
        path = ROOT / "doc/design-meta/examples/tables" / f"{name}.csv"
        expected = [
            r for r in csv.DictReader(path.open()) if r.get("phase", "MVP") == "MVP"
        ]
        assert installed == expected
    assert len(listing("fixtures")) == 22
    assert len(listing("locales")) == 8
    assert listing("limits") == LIMITS
    assert len(listing("profiles")) == 7
    for pack, minimum, size in [("core", 17, 15), ("stress", 16, 16)]:
        assert len(cases(template(pack))) == size
        value = template(pack)
        value["periods"][0]["count"] = minimum
        assert len(preview(value)["messages"]) == minimum
        value["periods"][0]["count"] -= 1
        with pytest.raises(AstreaError, match="coverage"):
            preview(value)


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(seed=True),
        lambda p: p.update(seed=1.0),
        lambda p: p.update(seed=-1),
        lambda p: p.update(seed=2**64),
        lambda p: p.update(seed="1"),
        lambda p: p.update(extra=1),
        lambda p: p.pop("limits"),
        lambda p: p.update(include_stress=1),
        lambda p: p["selection"].update(fixtures="fixture.uk.plain"),
        lambda p: p["selection"].update(client_profile=1),
        lambda p: p["limits"].update(max_parts=1001),
        lambda p: p["limits"].update(max_depth=0),
        lambda p: p["periods"][0].update(count=False),
        lambda p: p["periods"][0].update(title=1),
        lambda p: p["periods"][0].update(title="  "),
        lambda p: p["periods"][0].update(start="2025-02-30"),
        lambda p: p["periods"][0].update(start="2025-02-01"),
        lambda p: p["periods"][0].update(id="Bad_ID"),
        lambda p: p.update(periods=[]),
        lambda p: p.update(domains=[]),
        lambda p: p.update(domain_file="also.astrea-domains.txt"),
        lambda p: p.update(fixture_parameters={"fixture.uk.plain": {"depth": 3}}),
        lambda p: p.update(fixture_parameters={"fixture.uk.nested": {"depth": 3}}),
    ],
)
def test_rejects_invalid_configuration(change):
    plan = single()
    change(plan)
    with pytest.raises(AstreaError):
        preview(plan)


@pytest.mark.parametrize(
    "values",
    [
        None,
        [],
        [1],
        ["test"],
        ["real.com"],
        ["a.test."],
        ["*.a.test"],
        ["a..test"],
        ["-a.test"],
        ["a-.test"],
        ["é.test"],
        ["a" * 64 + ".test"],
        ["a.test", " A.TEST "],
        ["https://a.test"],
        ["a@b.test"],
        ["a.test"] * 1001,
    ],
)
def test_domains_reject_invalid_inputs(values):
    with pytest.raises(AstreaError):
        domains(values)


def test_domains_normalize_order_and_file_resolution(tmp_path):
    assert domains([" B.TEST ", "mail.a.test"]) == ["b.test", "mail.a.test"]
    folder = tmp_path / "plans"
    folder.mkdir()
    (tmp_path / "source.astrea-domains.txt").write_text(" B.TEST \n\nmail.a.test\n")
    plan = single()
    plan.pop("domains")
    plan["domain_file"] = "../source.astrea-domains.txt"
    path = folder / "sample.astrea-plan.json"
    path.write_text(json.dumps(plan))
    resolved = read_plan(path)
    assert resolved["domains"] == ["b.test", "mail.a.test"]
    assert "domain_file" not in resolved
    assert preview(resolved) == resolved
    for content in ["# comment\na.test", "é.test", "a" * 65537]:
        (tmp_path / "source.astrea-domains.txt").write_text(content)
        with pytest.raises(AstreaError):
            read_plan(path)


@pytest.mark.parametrize(
    "selection",
    [
        {"packs": []},
        {"packs": ["future"]},
        {"fixtures": ["fixture.fr.unicode"]},
        {"locales": ["unknown"]},
        {"locales": ["fr_FR"]},
        {"client_profile": "client.apple-mail"},
        {"provider_profile": "provider.yahoo"},
        {"client_profile": "client.gmail-web", "provider_profile": "provider.generic"},
    ],
)
def test_rejects_invalid_selection(selection):
    plan = single()
    plan["selection"].update(selection)
    with pytest.raises(AstreaError):
        preview(plan)


def test_locale_filter_and_selection_deduplication():
    plan = template()
    plan["selection"].update(locales=["ja_JP", "ja_JP"], packs=["core", "core"])
    resolved = preview(plan)
    assert {m["fixture_id"] for m in resolved["messages"]} == {
        "fixture.jp.notification"
    }
    assert resolved["selection"]["locales"] == ["ja_JP"]


def test_thread_counts_and_dates():
    plan = single("fixture.uk.thread", 6)
    messages = preview(plan)["messages"]
    assert [m["thread_member_index"] for m in messages] == [0, 1, 2, 0, 1, 2]
    assert [m["occurrence"] for m in messages] == [0, 0, 0, 1, 1, 1]
    assert messages[0]["date"] == "2025-01-01T00:00:00Z"
    assert messages[-1]["date"] == "2025-01-31T23:59:59Z"
    assert [m["date"] for m in messages] == sorted(m["date"] for m in messages)
    plan["periods"][0]["count"] = 7
    with pytest.raises(AstreaError) as error:
        preview(plan)
    assert error.value.code == "E_COVERAGE_COUNT"
    assert preview(single())["messages"][0]["date"] == "2025-01-16T12:00:00Z"


def test_period_constraints_and_independence():
    plan = single()
    second = dict(
        plan["periods"][0], id="february", start="2025-02-01", end="2025-02-28"
    )
    plan["periods"].append(second)
    before = preview(plan)
    plan["periods"][0]["count"] = 2
    after = preview(plan)
    a, b = before["messages"][-1], after["messages"][-1]
    assert {k: v for k, v in a.items() if k != "index"} == {
        k: v for k, v in b.items() if k != "index"
    }
    assert digest(before, a, "name") == digest(after, b, "name")
    for change in [
        {"id": "january-2025"},
        {"start": "2025-01-31"},
        {"count": 10000},
    ]:
        invalid = copy.deepcopy(plan)
        invalid["periods"][1].update(change)
        with pytest.raises(AstreaError):
            preview(invalid)
    leap = single()
    leap["periods"][0].update(start="2024-02-29", end="2024-02-29")
    assert preview(leap)["messages"][0]["date"] == "2024-02-29T12:00:00Z"


@pytest.mark.parametrize(
    ("fixture", "parameters"),
    [
        ("fixture.uk.nested", {"depth": 1}),
        ("fixture.uk.nested", {"depth": True}),
        ("fixture.stress.width", {"total_parts": 1001}),
        ("fixture.stress.boundary", {"mutation_id": "UNKNOWN"}),
    ],
)
def test_invalid_fixture_parameters(fixture, parameters):
    pack = "stress" if ".stress." in fixture else "core"
    plan = single(fixture, pack=pack)
    plan["fixture_parameters"][fixture] = parameters
    with pytest.raises(AstreaError):
        preview(plan)


def test_stress_permission_and_selected_variant():
    plan = single("fixture.stress.filename", pack="stress")
    plan["fixture_parameters"] = {"fixture.stress.filename": {"filename_case": "bidi"}}
    assert preview(plan)["messages"][0]["parameters"] == {"filename_case": "bidi"}
    plan["include_stress"] = False
    with pytest.raises(AstreaError):
        preview(plan)


def test_saved_plan_conflicts_and_strict_json(tmp_path):
    plan = preview(single())
    plan["messages"][0]["date"] = "2020-01-01T00:00:00Z"
    with pytest.raises(AstreaError):
        preview(plan)
    path = tmp_path / "bad.astrea-plan.json"
    for content in ['{"seed":0,"seed":1}', '{"seed":NaN}', "{", "\ufeff{}"]:
        path.write_text(content)
        with pytest.raises(AstreaError):
            read_plan(path)
    with pytest.raises(AstreaError):
        read_plan(tmp_path / "bad.json")
    with pytest.raises(AstreaError):
        load(path, maximum=1)
    with pytest.raises(AstreaError) as error:
        load(tmp_path / "missing.json")
    assert error.value.exit_code == 1
