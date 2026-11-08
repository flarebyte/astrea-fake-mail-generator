"""Fail closed before releasing a new stable version from the tip of main."""

import os
import re
import subprocess
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def git(*arguments):
    return subprocess.run(
        ["git", *arguments], check=False, capture_output=True, text=True
    )


def release_metadata(root):
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    name, version = project.get("name"), project.get("version")
    if not isinstance(name, str) or not re.fullmatch(
        r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?", name
    ):
        raise SystemExit("Release requires a valid Python distribution name")
    if not isinstance(version, str) or not re.fullmatch(
        r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version
    ):
        raise SystemExit("Release version must be stable major.minor.patch")
    lock = tomllib.loads((root / "uv.lock").read_text())
    local = [
        package
        for package in lock.get("package", [])
        if package.get("source") == {"editable": "."}
    ]
    if len(local) != 1 or (local[0].get("name"), local[0].get("version")) != (
        name,
        version,
    ):
        raise SystemExit(
            "pyproject.toml and uv.lock name/version must match; run uv lock after changing the version"
        )
    return name, version


def check_registry(name, version):
    name, version = (urllib.parse.quote(value, safe="") for value in (name, version))
    try:
        with urllib.request.urlopen(
            f"https://pypi.org/pypi/{name}/{version}/json", timeout=15
        ):
            raise SystemExit("This version is already published on PyPI")
    except urllib.error.HTTPError as error:
        error.close()
        if error.code != 404:
            raise SystemExit(f"Unable to check PyPI: HTTP {error.code}") from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise SystemExit(
            "Unable to check PyPI; refusing to assume the version is available"
        ) from error


def main():
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise SystemExit("Publishing is restricted to main")
    sha = os.environ.get("GITHUB_SHA")
    if not sha:
        raise SystemExit("GITHUB_SHA is required")
    for ref in ("HEAD", "refs/remotes/origin/main"):
        result = git("rev-parse", "--verify", ref)
        if result.returncode or result.stdout.strip() != sha:
            raise SystemExit(
                "Release commit must be the current tip of main; start a new workflow run"
            )
    name, version = release_metadata(Path("."))
    if os.environ.get("EXPECTED_VERSION", version) != version:
        raise SystemExit("Version changed after release validation")
    tag = f"v{version}"
    result = git("show-ref", "--verify", "--quiet", f"refs/tags/{tag}")
    if result.returncode == 0:
        raise SystemExit(f"Git tag already exists: {tag}")
    if result.returncode != 1:
        raise SystemExit("Unable to check Git tags")
    check_registry(name, version)
    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"version={version}\ntag={tag}\n")
    print(f"Release validated: {name}@{version}")


if __name__ == "__main__":
    main()
