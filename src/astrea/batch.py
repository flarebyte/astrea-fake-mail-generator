"""Batch orchestration and validation against independently recomputed fixtures."""

import json
import os
import stat
from collections import Counter
from email.parser import BytesParser
from importlib.resources import files

from .assets import inventory
from .catalog import FIXTURES
from .errors import AstreaError
from .jsonio import dumps, load, read_bytes
from .planning import cases, check_schema, preview
from .rendering import POLICY, render, sha, walk
from .storage import directory, safe_name, staging, write


def manifest(plan, entries, assets):
    periods = []
    minimum = sum(case.size for case in cases(plan))
    for period in plan["periods"]:
        counts = Counter(
            e["fixture_id"] for e in entries if e["period_id"] == period["id"]
        )
        periods.append(
            dict(
                period,
                coverage={"minimum_messages": minimum, "fixture_counts": dict(counts)},
            )
        )
    return {
        "seed": plan["seed"],
        "domains": plan["domains"],
        "count": len(entries),
        "total_message_bytes": sum(e["size_bytes"] for e in entries),
        "coverage": {"fixture_counts": dict(Counter(e["fixture_id"] for e in entries))},
        "periods": periods,
        "assets": inventory(assets),
        "messages": entries,
    }


def inspect_normal(data, expected):
    """Parse only exact bounded normal bytes, never attacker-controlled/stress bytes."""
    parsed = BytesParser(policy=POLICY).parsebytes(data)
    if list(parsed.keys()) != expected["headers"]["ordered_names"]:
        raise AstreaError("E_ASSERTION", "Header order mismatch", exit_code=1)
    for key, value in expected["headers"]["decoded_values"].items():
        values = [str(v) for v in parsed.get_all(key, [])]
        target = value if isinstance(value, list) else [value]
        # Folding whitespace may differ, semantic header values may not.
        if [" ".join(v.split()) for v in values] != [
            " ".join(v.split()) for v in target
        ]:
            raise AstreaError(
                "E_ASSERTION", "Decoded header mismatch", key, exit_code=1
            )
    for name in expected["headers"]["absent"]:
        if parsed.get_all(name):
            raise AstreaError(
                "E_ASSERTION", "Forbidden header is present", name, exit_code=1
            )
    nodes = list(walk(parsed))
    if len(nodes) != expected["mime"]["node_count"]:
        raise AstreaError("E_ASSERTION", "MIME node count mismatch", exit_code=1)
    texts = []
    for (part, path, depth), target in zip(nodes, expected["mime"]["nodes"]):
        payload = part.get_payload(decode=True)
        if part.defects or path != target["path"] or depth != target["depth"]:
            raise AstreaError("E_ASSERTION", "Invalid MIME structure", exit_code=1)
        if (
            part.get_content_type() != target["media_type"]
            or part.get_content_charset() != target["charset"]
            or part.get_content_disposition() != target["disposition"]
            or (sha(payload) if payload is not None else None)
            != target["decoded_sha256"]
        ):
            raise AstreaError(
                "E_ASSERTION", "Decoded MIME properties mismatch", path, exit_code=1
            )
        if part.get_content_maintype() == "text" and payload is not None:
            texts.append(payload.decode(part.get_content_charset() or "ascii"))
    if any(not any(fact in text for text in texts) for fact in expected["body_facts"]):
        raise AstreaError("E_ASSERTION", "Expected body fact is missing", exit_code=1)


def schema_manifest(value):
    schema = json.loads(
        files("astrea").joinpath("data/manifest.schema.json").read_text()
    )
    check_schema(value, schema)


def generate(plan, output):
    entries, assets = [], set()
    total = 0
    with staging(output) as fd:
        for message in plan["messages"]:
            result = render(plan, message)
            total += len(result.data)
            if total > plan["limits"]["max_batch_bytes"]:
                raise AstreaError(
                    "E_LIMIT",
                    "Batch exceeds byte limit",
                    "max_batch_bytes",
                    plan["limits"]["max_batch_bytes"],
                )
            if result.entry["validity"] == "valid":
                inspect_normal(result.data, result.entry["expectations"])
            write(fd, result.entry["path"], result.data)
            entries.append(result.entry)
            assets.update(result.assets)
        summary = manifest(plan, entries, assets)
        schema_manifest(summary)
        write(fd, "batch.astrea-plan.json", dumps(plan).encode())
        write(fd, "batch.astrea-manifest.json", dumps(summary).encode())
        # Validate the complete staged batch before publication.
        validate_fd(fd)
    return {"count": len(entries), "total_message_bytes": total}


def validate_fd(fd):
    names = os.listdir(fd)
    if len(names) > 10002:
        raise AstreaError("E_LIMIT", "Too many batch entries", limit=10002, exit_code=1)
    for name in names:
        safe_name(name)
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode):
            raise AstreaError(
                "E_UNSAFE_PATH", "Batch entries must be regular files", exit_code=1
            )
    manifests = [name for name in names if name.endswith(".astrea-manifest.json")]
    if len(manifests) != 1:
        raise AstreaError(
            "E_ASSERTION", "Batch must contain exactly one manifest", exit_code=1
        )
    saved = load("batch.astrea-plan.json", nofollow=True, dir_fd=fd)
    # A generated plan must be self-contained. Never read a domain_file during validation.
    if not isinstance(saved, dict) or "domain_file" in saved or "messages" not in saved:
        raise AstreaError(
            "E_ASSERTION",
            "Saved plan must contain domains and computed messages",
            exit_code=1,
        )
    plan = preview(saved)
    supplied = load(manifests[0], nofollow=True, dir_fd=fd)
    schema_manifest(supplied)
    for entry in supplied["messages"]:
        safe_name(entry["path"])
    expected_names = {
        f"{m['index']:06d}-{m['fixture_id']}.eml" for m in plan["messages"]
    }
    if {name for name in names if name.endswith(".eml")} != expected_names:
        raise AstreaError("E_ASSERTION", "Missing or extra email files", exit_code=1)
    entries, assets = [], set()
    total = 0
    for message in plan["messages"]:
        result = render(plan, message)
        data = read_bytes(
            result.entry["path"],
            plan["limits"]["max_message_bytes"],
            nofollow=True,
            dir_fd=fd,
        )
        total += len(data)
        if total > plan["limits"]["max_batch_bytes"]:
            raise AstreaError("E_LIMIT", "Batch exceeds byte limit", exit_code=1)
        if data != result.data:
            raise AstreaError(
                "E_HASH",
                "Email bytes differ from the fixture and saved plan",
                result.entry["path"],
                exit_code=1,
            )
        if FIXTURES[message["fixture_id"]]["validity"] == "valid":
            inspect_normal(data, result.entry["expectations"])
        entries.append(result.entry)
        assets.update(result.assets)
    if supplied != manifest(plan, entries, assets):
        raise AstreaError(
            "E_ASSERTION",
            "Manifest differs from required fixture expectations",
            exit_code=1,
        )
    return {"count": len(entries), "total_message_bytes": total}


def validate(path):
    with directory(path) as fd:
        try:
            return validate_fd(fd)
        except AstreaError as exc:
            exc.exit_code = 1
            raise
