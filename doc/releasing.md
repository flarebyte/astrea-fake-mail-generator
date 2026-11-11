# Publishing a release

Maintainer instructions for the Python package and GitHub release. For local
setup and development checks, see [Contributing](../CONTRIBUTING.md).


[Publish PyPI release](../.github/workflows/publish.yaml) is a manual GitHub Actions
workflow. It runs only for `main` and takes the stable `major.minor.patch` version
from `[project].version` in `pyproject.toml`; the Git tag is `v<version>`. It checks
that `uv.lock` agrees, the selected commit is still the tip of `main`, and neither
the tag nor the PyPI version already exists. Registry failures stop publication.

Before the first run, sign in to PyPI as `olih` and configure a GitHub Trusted
Publisher. For a new project, use [your account's Publishing page](https://pypi.org/manage/account/publishing/)
to add a pending publisher; for an existing project, use its Publishing settings.
Enter these values exactly:

| PyPI setting | Value |
| --- | --- |
| PyPI project name (pending publisher only) | `astrea-fake-mail-generator` |
| GitHub owner | `flarebyte` |
| GitHub repository | `astrea-fake-mail-generator` |
| Workflow filename | `publish.yaml` |
| Environment name | `pypi` |

The PyPI account name and GitHub owner are separate identities. The workflow uses
GitHub's OIDC identity, so no PyPI password or API-token secret is needed. See the
[PyPI Trusted Publishing guide](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).
A pending publisher does not reserve the project name before its first upload.

In GitHub repository settings, create the `pypi` environment and restrict its
deployment branches to `main`. Required reviewers can optionally provide a human
approval gate. Without that rule, the environment does not require approval.
The workflow's own branch and commit checks apply either way.

For each release:

1. Update `pyproject.toml`, run `uv lock`, and commit both version files to `main`.
2. Open Actions → **Publish PyPI release** → **Run workflow**, selecting `main`.
3. Approve the `pypi` environment deployment if reviewers are configured.

Validation runs the release-checker tests, formatting, lint, coverage, the package
build (including runtime tests on Linux), and strict distribution metadata checks.
The build tools use the repository's pinned Python, uv 0.8.22, and gh-flarebyte
0.24.0. The built wheel, source distribution, and checksums are retained for seven
days. After the environment gate, the workflow rechecks the selected commit and
version, verifies checksums, and publishes the distributions through the PyPA
Trusted Publishing action. A separate job then creates the GitHub release at the
same commit with generated notes and attaches those exact files and checksums.
Builds and tests have no OIDC or release-write permissions. All external actions
are pinned to full upstream commit SHAs; review action updates and retain SHA
pins. The offline release tests enforce this policy.

PyPI publication and GitHub release creation are separate operations. If only the
GitHub release job fails after PyPI succeeds, rerun the failed job while its build
artifact is still retained. A fresh full run refuses an already-published version.
If a PyPI upload is only partly completed, inspect the published files before
attempting recovery; the workflow deliberately does not skip duplicate uploads.

The release preflight also has offline tests:

```sh
python3 -m unittest discover -s .github/scripts -p 'test_*.py'
```

Changing workflow filenames or the environment name requires updating the PyPI
Trusted Publisher configuration too.
