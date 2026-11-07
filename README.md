# astrea-fake-mail-generator
Generate fake `.eml` email files for tests.

The Python CLI is currently specified in [doc/design-meta/examples](doc/design-meta/examples/overview.md). Start with the [generated specification](doc/design/specification.md) for fixture coverage, CLI commands, expected test results, and optional parser stress cases with fixed limits.

Output is an ordinary folder of `.eml` files plus `batch.astrea-plan.json` (saved generation settings) and `batch.astrea-manifest.json` (file index and expected test results). Maildir, mbox, mailbox import/export, and sending email are out of scope. See the [glossary](doc/design-meta/examples/tables/glossary.csv) for definitions.

Regenerate the design documentation with:

```sh
make doc-design
```

The proposed runtime command is `uv run --locked astrea`; implementation is not included yet.

Generation settings belong in the plan file:

```sh
uv run --locked astrea plan --template core > custom123.astrea-plan.json
# Edit the plan to select fixtures and set periods, seed, and other settings.
uv run --locked astrea generate --plan custom123.astrea-plan.json --out ./fixtures
```

`generate` accepts only `--plan`, `--out`, and optional `--json-diagnostics`. See [plan settings](doc/design-meta/examples/tables/plan-fields.csv).

Set allowed domains using either a `domains` JSON array in the plan or `domain_file` pointing to an `.astrea-domains.txt` file with one domain per line. All domains must end in `.test`. See [the example list](doc/design-meta/examples/domains/example.astrea-domains.txt) and [file-based plan](doc/design-meta/examples/plans/file-domains.astrea-plan.json).

A plan can contain titled ISO date periods with exact counts, such as January 30 emails and February 55 emails. See [the monthly example](doc/design-meta/examples/plans/monthly.astrea-plan.json). Each email's Date falls within its period; all 85 files go in the same output folder.

See [the Outlook example plan](doc/design-meta/examples/plans/outlook.astrea-plan.json) for explicit client and provider profiles, using PDF invoice, forwarded-email, and Spanish confirmation fixtures.

See [the nested email example plan](doc/design-meta/examples/plans/nested.astrea-plan.json) for `fixture_parameters` that sets MIME depth to 8 for one selected fixture.

For selective specification retrieval, start with the [AI agent task map](doc/design-meta/AGENTS.md), then use [concepts.csv](doc/design-meta/examples/concepts.csv) and the [coding-agent search guide](doc/design-meta/examples/retrieval.md). Validate search metadata with `gh flarebyte script validate-specs.py`; run its regression checks with `gh flarebyte test`.

## Python development

Install [uv](https://docs.astral.sh/uv/) and the `gh flarebyte` GitHub CLI
extension. The package supports Python 3.12+; `.python-version` pins Python
3.14.6 for local development and reproducible reference fixtures.

```sh
uv sync --locked
gh flarebyte config validate
gh flarebyte format
gh flarebyte lint
gh flarebyte test
gh flarebyte cov
gh flarebyte build
```

The development dependencies are locked in `uv.lock`. Tests use pytest (including
the existing unittest suite), formatting and lint use Ruff, and coverage uses
coverage.py with an enforced 80% minimum across the package and specification
validator. The package skeleton lives in `src/astrea`; the `astrea` console command
will be added with the CLI implementation.

`gh flarebyte build` runs tests and writes the wheel, source distribution, and
`checksums.txt` to `build/`. The static version in `pyproject.toml` is the release
version source. `.gh-flarebyte.cue` manages local workflows and repository policy;
this setup does not apply settings to GitHub or publish a release.

The Makefile covers documentation generation, which combines the Python validator
with `flyb` validation and Markdown generation. Run `make` for help,
`make check-tools` to check the documentation tools, or `make install-tools-help`
for installation guidance. Python scripts run through gh flarebyte directly:

```sh
gh flarebyte script validate-specs.py
# Arguments are forwarded after --:
gh flarebyte script validate-specs.py -- --help
```

The validator uses the standard library and does not need dependency installation.
