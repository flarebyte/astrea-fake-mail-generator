"""Regression checks for metadata amplification and staging-source substitution."""

import json
import os
import stat
import subprocess
import sys
from unittest.mock import patch

import pytest
from test_planning import single

from astrea import batch, storage
from astrea.errors import AstreaError
from astrea.jsonio import iter_json, json_size
from astrea.planning import preview


def test_identifier_and_title_limits():
    for field, size in [("id", 129), ("title", 1025)]:
        plan = single()
        plan["periods"][0][field] = "a" * size
        with pytest.raises(AstreaError) as error:
            preview(plan)
        assert error.value.code == "E_CONFIG"
    plan = single()
    plan["periods"][0].update(id="a" * 128, title="a" * 1024)
    assert preview(plan)["messages"]
    # This previously expanded a 66 KB input into a saved plan larger than 64 MiB.
    plan["periods"][0].update(id="a" * 65536, count=1024)
    with pytest.raises(AstreaError):
        preview(plan)


def test_streamed_json_exact_byte_limit():
    value = {"unicode": "ملاحظات", "array": [1, 2]}
    expected = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode()
    assert b"".join(iter_json(value, len(expected))) == expected
    assert json_size(value, len(expected)) == len(expected)
    with pytest.raises(AstreaError) as error:
        list(iter_json(value, len(expected) - 1))
    assert error.value.code == "E_LIMIT"
    with pytest.raises(AstreaError):
        json_size(value, len(expected), indent_offset=4)
    # Count the array slot's indentation and comma without building the whole array.
    cost = json_size(value, indent_offset=4) + 1
    array = {"messages": [value]}
    assert cost >= len(expected)
    assert cost < json_size(array)


def test_expanded_plan_fails_before_rendering_or_staging(tmp_path, monkeypatch):
    plan = preview(single(count=5))
    monkeypatch.setattr(batch, "MAX_JSON_BYTES", json_size(plan) - 1)
    with (
        patch.object(
            batch, "render", side_effect=AssertionError("Must fail before rendering")
        ),
        pytest.raises(AstreaError) as error,
    ):
        batch.generate(plan, tmp_path / "output")
    assert error.value.code == "E_LIMIT"
    assert not list(tmp_path.iterdir())


def test_manifest_budget_stops_accumulation_and_cleans_staging(tmp_path, monkeypatch):
    plan = preview(single(count=5))
    # The saved plan fits but full fixture expectations do not.
    monkeypatch.setattr(batch, "MAX_JSON_BYTES", 9000)
    with (
        patch.object(batch, "render", wraps=batch.render) as rendering,
        pytest.raises(AstreaError) as error,
    ):
        batch.generate(plan, tmp_path / "output")
    assert error.value.code == "E_LIMIT"
    assert 1 < rendering.call_count < 5
    assert not list(tmp_path.iterdir())


def test_streamed_write_failure_cleans_partial_metadata(tmp_path):
    with pytest.raises(AstreaError), storage.staging(tmp_path / "output") as fd:
        storage.write_chunks(
            fd, "partial.json", iter_json({"items": list(range(100))}, 60)
        )
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("replacement", ["symlink", "directory", "missing"])
def test_staging_source_replacement_is_rejected(tmp_path, monkeypatch, replacement):
    (tmp_path / "outside").mkdir()
    (tmp_path / "outside" / "marker").write_text("preserve")
    publish = storage.publish

    def replace(parent, name, destination, identity):
        os.rename(name, name + ".moved", src_dir_fd=parent, dst_dir_fd=parent)
        if replacement == "symlink":
            os.symlink("outside", name, dir_fd=parent)
        elif replacement == "directory":
            os.mkdir(name, dir_fd=parent)
        publish(parent, name, destination, identity)

    monkeypatch.setattr(storage, "publish", replace)
    with pytest.raises(AstreaError) as error:
        batch.generate(preview(single()), tmp_path / "output")
    assert error.value.code == "E_UNSAFE_PATH"
    assert not (tmp_path / "output").exists()
    assert (tmp_path / "outside" / "marker").read_text() == "preserve"


def test_source_replacement_after_precheck_cannot_report_success(tmp_path, monkeypatch):
    (tmp_path / "outside").mkdir()
    verify = storage.verify_identity

    def replace_after_check(parent, name, identity):
        verify(parent, name, identity)
        if name.startswith(".astrea-"):
            os.rename(name, name + ".moved", src_dir_fd=parent, dst_dir_fd=parent)
            os.symlink("outside", name, dir_fd=parent)

    monkeypatch.setattr(storage, "verify_identity", replace_after_check)
    with pytest.raises(AstreaError) as error:
        batch.generate(preview(single()), tmp_path / "output")
    assert error.value.code == "E_UNSAFE_PATH"
    # A same-user actor is outside the permission boundary; never delete its entry.
    assert (tmp_path / "output").is_symlink()


@pytest.mark.parametrize("mode", [0o777, 0o770])
def test_shared_writable_output_parent_is_rejected(tmp_path, mode):
    parent = tmp_path / "shared"
    parent.mkdir(mode=mode)
    parent.chmod(mode)  # Ignore the process umask for this regression.
    with pytest.raises(AstreaError) as error:
        batch.generate(preview(single()), parent / "output")
    assert error.value.code == "E_UNSAFE_PATH"
    assert not list(parent.iterdir())


def test_untrusted_owner_is_rejected(tmp_path, monkeypatch):
    with storage.directory(tmp_path) as fd:
        actual = os.fstat(fd)
        with (
            patch.object(
                storage.os,
                "fstat",
                return_value=type(
                    "Info",
                    (),
                    {"st_uid": os.geteuid() + 10000, "st_mode": actual.st_mode},
                )(),
            ),
            pytest.raises(AstreaError),
        ):
            storage.trusted_directory(fd)


def test_sticky_parent_is_allowed(tmp_path):
    parent = tmp_path / "sticky"
    parent.mkdir()
    parent.chmod(0o1777)
    assert parent.stat().st_mode & stat.S_ISVTX
    assert batch.generate(preview(single()), parent / "output")["count"] == 1


def test_parent_permissions_rechecked_before_publication(tmp_path):
    parent = tmp_path / "parent"
    parent.mkdir()
    with pytest.raises(AstreaError), storage.staging(parent / "output"):
        parent.chmod(0o777)
    assert not list(parent.iterdir())


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS extended ACL regression")
def test_extended_allow_acl_is_rejected_even_without_write_mode_bits(tmp_path):
    parent = tmp_path / "acl-parent"
    parent.mkdir(mode=0o700)
    subprocess.run(
        ["chmod", "+a", "everyone allow add_subdirectory,delete_child", str(parent)],
        check=True,
    )
    assert not parent.stat().st_mode & (stat.S_IWGRP | stat.S_IWOTH)
    with pytest.raises(AstreaError) as error:
        batch.generate(preview(single()), parent / "output")
    assert error.value.code == "E_UNSAFE_PATH"
    assert not list(parent.iterdir())


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS deny-only ACL regression")
def test_deny_only_acl_allows_private_output(tmp_path):
    parent = tmp_path / "deny-parent"
    parent.mkdir(mode=0o700)
    subprocess.run(["chmod", "+a", "everyone deny delete", str(parent)], check=True)
    try:
        assert batch.generate(preview(single()), parent / "output")["count"] == 1
    finally:
        subprocess.run(["chmod", "-N", str(parent)], check=True)


def test_shared_writable_ancestor_is_rejected(tmp_path):
    shared = tmp_path / "shared"
    shared.mkdir()
    shared.chmod(0o777)
    private = shared / "private"
    private.mkdir(mode=0o700)
    with pytest.raises(AstreaError) as error:
        batch.generate(preview(single()), private / "output")
    assert error.value.code == "E_UNSAFE_PATH"
    assert not list(private.iterdir())
