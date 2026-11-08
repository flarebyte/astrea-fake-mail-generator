"""CLI stdout/stderr, diagnostics, and process-level reproducibility."""

import json
import os
import subprocess
import sys
import tomllib

import pytest
from test_planning import ROOT, single

from astrea.cli import main
from astrea.jsonio import dumps


def test_cli_catalog_templates_and_version(capsys):
    for kind in ["fixtures", "profiles", "locales", "packs", "limits"]:
        assert main(["list", kind, "--json"]) == 0
        assert json.loads(capsys.readouterr().out)
        assert main(["list", kind]) == 0
        assert capsys.readouterr().out
    assert main(["plan"]) == 0
    assert json.loads(capsys.readouterr().out)["selection"]["packs"] == ["core"]
    assert main(["plan", "--template", "stress"]) == 0
    assert json.loads(capsys.readouterr().out)["include_stress"] is True
    with pytest.raises(SystemExit) as result:
        main(["--version"])
    assert result.value.code == 0
    assert (
        capsys.readouterr().out.strip()
        == tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    )


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["generate"],
        ["plan", "--template", "core", "--plan", "x"],
        ["generate", "--count", "1"],
        ["list", "unknown"],
    ],
)
def test_invalid_arguments_have_json_errors(args, capsys):
    assert main(args + ["--json-diagnostics"]) == 2
    output = capsys.readouterr()
    assert not output.out
    assert json.loads(output.err)["code"] == "E_CONFIG"


def test_cli_generate_validate_and_failures(tmp_path, capsys):
    source = tmp_path / "source.astrea-plan.json"
    source.write_text(dumps(single()))
    output = tmp_path / "output"
    assert main(["plan", "--plan", str(source)]) == 0
    assert len(json.loads(capsys.readouterr().out)["messages"]) == 1
    assert main(["generate", "--plan", str(source), "--out", str(output)]) == 0
    assert json.loads(capsys.readouterr().out)["count"] == 1
    assert main(["validate", "--input", str(output)]) == 0
    assert json.loads(capsys.readouterr().out)["count"] == 1
    assert (
        main(
            [
                "generate",
                "--plan",
                str(source),
                "--out",
                str(output),
                "--json-diagnostics",
            ]
        )
        == 2
    )
    assert json.loads(capsys.readouterr().err)["code"] == "E_OUTPUT_EXISTS"
    assert main(["plan", "--plan", str(tmp_path / "missing.astrea-plan.json")]) == 1
    assert "E_IO" in capsys.readouterr().err
    assert (
        main(["validate", "--input", str(tmp_path / "absent"), "--json-diagnostics"])
        == 1
    )
    assert json.loads(capsys.readouterr().err)["code"] == "E_IO"


def test_cross_process_repeatability(tmp_path):
    source = tmp_path / "source.astrea-plan.json"
    source.write_text(dumps(single()))
    for index, seed in enumerate(["1", "987654"]):
        env = dict(
            os.environ,
            PYTHONHASHSEED=seed,
            TZ="Pacific/Honolulu" if index else "Europe/London",
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "astrea",
                "generate",
                "--plan",
                str(source),
                "--out",
                str(tmp_path / str(index)),
            ],
            check=True,
            capture_output=True,
            env=env,
            timeout=20,
        )
    first, second = tmp_path / "0", tmp_path / "1"
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()
    }
