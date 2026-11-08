"""End-to-end generation, independent MIME checks, and hostile batch inputs."""

import base64
import copy
import json
import os
import socket
import subprocess
import sys
import time
from email.parser import BytesParser
from unittest.mock import patch

import pytest
from test_planning import ROOT, single

from astrea import batch, storage
from astrea.batch import generate, inspect_normal, validate
from astrea.catalog import PROFILES
from astrea.errors import AstreaError
from astrea.jsonio import dumps, load, read_bytes
from astrea.planning import preview, read_plan, template
from astrea.rendering import POLICY, render, sha, walk


def directory_bytes(path):
    return {p.name: p.read_bytes() for p in path.iterdir()}


@pytest.mark.parametrize(
    "example",
    sorted((ROOT / "doc/design-meta/examples/plans").glob("*.json")),
    ids=lambda p: p.name,
)
def test_examples_generate_validate_and_replay(example, tmp_path):
    plan = read_plan(example)
    first, second = tmp_path / "first", tmp_path / "second"
    result = generate(plan, first)
    assert result["count"] == sum(p["count"] for p in plan["periods"])
    assert validate(first) == result
    generate(read_plan(first / "batch.astrea-plan.json"), second)
    assert directory_bytes(first) == directory_bytes(second)
    index = load(first / "batch.astrea-manifest.json")
    assert index["coverage"]["fixture_counts"]
    assert len(index["messages"]) == result["count"]


def test_core_semantics_and_offline_generation(tmp_path, monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Network access is forbidden")

    monkeypatch.setattr(socket, "socket", deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket, "getaddrinfo", deny)
    plan = template()
    plan["periods"][0]["count"] = 17
    target = tmp_path / "core"
    generate(preview(plan), target)
    manifest = load(target / "batch.astrea-manifest.json")
    assert len(manifest["assets"]) == 5
    messages = {}
    for entry in manifest["messages"]:
        raw = (target / entry["path"]).read_bytes()
        assert b"\n" not in raw.replace(b"\r\n", b"")
        assert all(len(line) <= 998 for line in raw.split(b"\r\n"))
        msg = BytesParser(policy=POLICY).parsebytes(raw)
        messages.setdefault(entry["fixture_id"], []).append((msg, entry))
        assert msg["Bcc"] is None
        for node, _, _ in walk(msg):
            assert not node.defects
    arabic, entry = messages["fixture.ar.notification"][0]
    assert entry["effective_faker_locales"]["recipient_name"] == "en_US"
    assert "تذكير" in str(arabic["Subject"])
    assert 'dir="rtl"' in arabic.get_body(preferencelist=("html",)).get_content()
    assert next(arabic.iter_attachments()).get_filename() == "ملاحظات.txt"
    assert "U+0627" in entry["expectations"]["unicode_codepoints"]
    recipients, recipient_entry = messages["fixture.us.recipients"][0]
    assert recipient_entry["expectations"]["bcc_recipients"]
    assert recipients["Bcc"] is None
    japanese, _ = messages["fixture.jp.notification"][0]
    assert "サービス" in str(japanese["Subject"])
    empty, _ = messages["fixture.uk.empty"][0]
    assert empty.get_payload(decode=True) == b""
    nested, entry = messages["fixture.uk.nested"][0]
    assert max(depth for _, _, depth in walk(nested)) == 6
    inline, _ = messages["fixture.fr.inline"][0]
    html = inline.get_body(preferencelist=("html",))
    image = next(p for p, _, _ in walk(inline) if p.get_content_type() == "image/png")
    assert "cid:" + str(image["Content-ID"])[1:-1] in html.get_content()
    thread = messages["fixture.uk.thread"]
    ids = [str(msg["Message-ID"]) for msg, _ in thread]
    for i, (msg, _) in enumerate(thread):
        if i:
            assert str(msg["In-Reply-To"]) == ids[i - 1]
            assert str(msg["References"]).split() == ids[:i]
        assert str(msg["From"]) == str(thread[0][0]["From"])
    forward, _ = messages["fixture.us.forward"][0]
    embedded = next(iter(forward.iter_attachments())).get_payload()[0]
    assert embedded["Message-ID"] != forward["Message-ID"]
    assert validate(target)["count"] == 17


def test_all_supported_profile_pairs():
    for client, row in PROFILES.items():
        if row["kind"] != "client":
            continue
        for provider in row["valid_pairings"].split(";"):
            if provider not in PROFILES:
                continue
            plan = single()
            plan["selection"].update(client_profile=client, provider_profile=provider)
            resolved = preview(plan)
            result = render(resolved, resolved["messages"][0])
            inspect_normal(result.data, result.entry["expectations"])
            assert (b"X-Mailer:" in result.data) == (client == "client.outlook-desktop")
            assert (b"User-Agent:" in result.data) == (client == "client.thunderbird")


def test_period_content_independence():
    plan = single(count=2)
    plan["periods"].append(
        dict(plan["periods"][0], id="february", start="2025-02-01", end="2025-02-28")
    )
    before = preview(plan)
    bytes_before = [
        render(before, m).data
        for m in before["messages"]
        if m["period_id"] == "february"
    ]
    plan["periods"][0]["count"] = 5
    plan["periods"][0]["title"] = "Renamed January"
    after = preview(plan)
    assert bytes_before == [
        render(after, m).data for m in after["messages"] if m["period_id"] == "february"
    ]


def test_stress_mutation_records_and_bounded_parser(tmp_path):
    plan = template("stress")
    plan["periods"][0]["count"] = 16
    plan = preview(plan)
    target = tmp_path / "stress"
    # Stress files never enter the CLI's parser.
    with patch(
        "astrea.batch.BytesParser",
        side_effect=AssertionError("No in-process stress parsing"),
    ):
        generate(plan, target)
        validate(target)
    payloads = []
    for message in plan["messages"]:
        result = render(plan, message)
        stress = result.entry["expectations"]["stress"]
        output = result.data
        # Reverse recorded edits cannot restore removed bytes; verify baseline by
        # building the same fixture before the mutation layer instead.
        with patch(
            "astrea.mutations.mutate",
            side_effect=lambda root, raw, expected, msg, baseline=stress: (
                raw,
                dict(baseline),
            ),
        ):
            original = render(plan, message).data
        assert sha(original) == stress["original_sha256"]
        for edit in sorted(stress["edits"], key=lambda e: e["offset"], reverse=True):
            offset = edit["offset"]
            original = (
                original[:offset]
                + base64.b64decode(edit["inserted_base64"])
                + original[offset + edit["removed_bytes"] :]
            )
        assert original == output
        assert sha(output) == stress["final_sha256"]
        if result.entry["validity"] == "malformed":
            assert stress["error_code"]
        payloads.append(base64.b64encode(output).decode())
    # This is a downstream parser check in a separate bounded process.
    script = """
import base64,json,resource,socket,sys
from email.parser import BytesParser
resource.setrlimit(resource.RLIMIT_CPU,(4,4))
if sys.platform != "darwin":
    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
def deny(*args, **kwargs): raise RuntimeError("network disabled")
socket.socket=socket.create_connection=socket.getaddrinfo=deny
for value in json.load(open(sys.argv[1])):
    BytesParser().parsebytes(base64.b64decode(value))
"""
    source = tmp_path / "parser-input.json"
    source.write_text(json.dumps(payloads))
    # macOS rejects RLIMIT_AS; supervise resident memory externally there.
    with subprocess.Popen(
        [sys.executable, "-c", script, str(source)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as process:
        deadline = time.monotonic() + 5
        while process.poll() is None:
            if time.monotonic() >= deadline:
                process.kill()
                pytest.fail("Parser exceeded the five-second deadline")
            if sys.platform == "darwin":
                sample = subprocess.run(
                    ["ps", "-o", "rss=", "-p", str(process.pid)],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=1,
                ).stdout.strip()
                if sample and int(sample) > 256 * 1024:
                    process.kill()
                    pytest.fail("Parser exceeded the 256 MiB memory limit")
            time.sleep(0.01)
        _stdout, stderr = process.communicate(timeout=1)
        assert process.returncode == 0, stderr.decode()


@pytest.mark.parametrize(
    ("fixture", "params", "depth", "parts"),
    [
        ("fixture.uk.nested", {"depth": 2}, 2, 3),
        ("fixture.uk.nested", {"depth": 16}, 16, 17),
        ("fixture.stress.depth", {"depth": 64}, 64, 65),
        ("fixture.stress.width", {"total_parts": 1000}, 2, 1000),
    ],
)
def test_structure_boundaries(fixture, params, depth, parts):
    plan = single(fixture, pack="stress" if ".stress." in fixture else "core")
    plan["fixture_parameters"][fixture] = params
    plan = preview(plan)
    result = render(plan, plan["messages"][0])
    assert result.entry["expectations"]["mime"]["depth"] == depth
    assert result.entry["expectations"]["mime"]["node_count"] == parts


@pytest.mark.parametrize(
    "limit,value",
    [
        ("max_message_bytes", 10),
        ("max_batch_bytes", 10),
        ("max_header_bytes", 10),
        ("max_parts", 1),
        ("max_depth", 1),
    ],
)
def test_resource_failures_leave_no_output(tmp_path, limit, value):
    plan = single("fixture.uk.alternative")
    plan["limits"][limit] = value
    with pytest.raises(AstreaError) as error:
        generate(preview(plan), tmp_path / "batch")
    assert error.value.code == "E_LIMIT"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "tamper",
    [
        "bytes",
        "missing",
        "extra",
        "expectations",
        "path",
        "symlink",
        "plan",
        "unknown",
        "second-manifest",
        "domain-file",
    ],
)
def test_tampered_batches_are_rejected(tmp_path, tamper):
    target = tmp_path / "batch"
    generate(preview(single()), target)
    manifest_path = target / "batch.astrea-manifest.json"
    manifest = load(manifest_path)
    email = target / manifest["messages"][0]["path"]
    if tamper == "bytes":
        email.write_bytes(email.read_bytes() + b"changed")
    elif tamper == "missing":
        email.unlink()
    elif tamper == "extra":
        (target / "extra.eml").write_text("extra")
    elif tamper == "expectations":
        manifest["messages"][0]["expectations"]["body_facts"] = []
    elif tamper == "path":
        manifest["messages"][0]["path"] = "../outside.eml"
    elif tamper == "symlink":
        email.unlink()
        email.symlink_to(tmp_path / "outside.eml")
    elif tamper == "plan":
        saved = load(target / "batch.astrea-plan.json")
        saved["messages"][0]["occurrence"] = 10
        (target / "batch.astrea-plan.json").write_text(dumps(saved))
    elif tamper == "unknown":
        manifest["messages"][0]["unknown"] = 1
    elif tamper == "second-manifest":
        (target / "other.astrea-manifest.json").write_text(dumps(manifest))
    elif tamper == "domain-file":
        saved = load(target / "batch.astrea-plan.json")
        saved.pop("domains")
        saved["domain_file"] = "../../outside.astrea-domains.txt"
        (target / "batch.astrea-plan.json").write_text(dumps(saved))
    manifest_path.write_text(dumps(manifest))
    with pytest.raises(AstreaError) as error:
        validate(target)
    assert error.value.exit_code == 1


def test_existing_and_racing_destinations_are_preserved(tmp_path, monkeypatch):
    target = tmp_path / "batch"
    target.mkdir()
    marker = target / "keep.txt"
    marker.write_text("preserve")
    with pytest.raises(AstreaError) as error:
        generate(preview(single()), target)
    assert error.value.code == "E_OUTPUT_EXISTS"
    assert marker.read_text() == "preserve"
    target = tmp_path / "race"
    publish = storage.publish

    def racing_publish(parent, staging, destination, identity):
        os.mkdir(destination, dir_fd=parent)
        publish(parent, staging, destination, identity)

    monkeypatch.setattr(storage, "publish", racing_publish)
    with pytest.raises(AstreaError) as error:
        generate(preview(single()), target)
    assert error.value.code == "E_OUTPUT_EXISTS"
    assert target.is_dir()
    assert not list(tmp_path.glob(".astrea-*"))


def test_unsafe_output_paths_and_failure_cleanup(tmp_path, monkeypatch):
    actual = tmp_path / "actual"
    actual.mkdir()
    (tmp_path / "link").symlink_to(actual, target_is_directory=True)
    for target in [tmp_path / "link" / "batch", tmp_path / ".." / "escape"]:
        with pytest.raises(AstreaError):
            generate(preview(single()), target)
    with pytest.raises(AstreaError):
        read_bytes(actual, 100)
    for name in ["", "..", "/outside", "a/b", "a\\b", "\x00"]:
        with pytest.raises(AstreaError):
            storage.safe_name(name)
    monkeypatch.setattr(
        batch,
        "render",
        lambda *args: (_ for _ in ()).throw(OSError("simulated write failure")),
    )
    with pytest.raises(OSError):
        generate(preview(single()), tmp_path / "failed")
    assert not (tmp_path / "failed").exists()
    assert not list(tmp_path.glob(".astrea-*"))


def test_normal_inspector_checks_independent_assertions():
    plan = preview(single())
    result = render(plan, plan["messages"][0])
    for mutation in [
        lambda e: e["headers"]["ordered_names"].reverse(),
        lambda e: e["headers"]["decoded_values"].update(Subject="Wrong"),
        lambda e: e["headers"]["absent"].append("Subject"),
        lambda e: e["mime"].update(node_count=99),
        lambda e: e["mime"]["nodes"][0].update(path="2"),
        lambda e: e["mime"]["nodes"][0].update(decoded_sha256="0" * 64),
        lambda e: e.update(body_facts=["Missing fact"]),
    ]:
        expected = copy.deepcopy(result.entry["expectations"])
        mutation(expected)
        with pytest.raises(AstreaError):
            inspect_normal(result.data, expected)


@pytest.mark.skipif(
    sys.version_info[:3] != (3, 14, 6), reason="Reference bytes pin Python 3.14.6"
)
def test_saved_runtime_reference(tmp_path):
    reference = ROOT / "tests/reference/plain"
    target = tmp_path / "reference"
    generate(read_plan(reference / "batch.astrea-plan.json"), target)
    assert directory_bytes(target) == directory_bytes(reference)
