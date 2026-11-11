# Contributing

The runtime CLI lives in `src/astrea/`, with specifications and examples under
`doc/design-meta/`. See [TECHNICAL_DESIGN.md](TECHNICAL_DESIGN.md) for the component
map and [README.md](README.md) for generation and validation examples.

## Setup

Run commands from the repository root. Install [uv](https://docs.astral.sh/uv/),
[GitHub CLI](https://cli.github.com/), and the `gh flarebyte` extension:

```sh
gh extension install flarebyte/gh-flarebyte
uv sync --locked
gh flarebyte config validate
```

Use macOS or Linux for runtime filesystem checks. The package requires Python
3.12+. `.python-version` pins Python 3.14.6 for local development and reproducible reference fixtures. `uv.lock` locks dependencies;
`pyproject.toml` declares the package, build backend, and development tools.

## Development checks

`.gh-flarebyte.cue` owns the Python workflows. The Makefile owns documentation
and code metadata generation; run `make` to list its targets.

| Task | Command |
| --- | --- |
| Format Python | `gh flarebyte format` |
| Lint Python | `gh flarebyte lint` |
| Run tests | `gh flarebyte test` |
| Check coverage | `gh flarebyte cov` |
| Build distributions | `gh flarebyte build` |
| Validate specification metadata | `gh flarebyte script validate-specs.py` |
| Regenerate design Markdown | `make doc-design` |

Tests use pytest, including the existing unittest suite. Formatting and lint use
Ruff. Coverage uses coverage.py and enforces an 80% minimum across `astrea` and
`scripts`. The build runs tests and writes the wheel, source distribution, and
`checksums.txt` to `build/`; it does not publish a release. The static version in
`pyproject.toml` is the release version source.

For a focused check of the existing validator suite:

```sh
uv run --locked pytest tests/test_validate_specs.py
```

The specification validator and its original regression suite also run without
third-party dependencies:

```sh
python3 scripts/validate-specs.py
python3 -m unittest discover -s tests -p test_validate_specs.py
```

Arguments to the managed script runner go after `--`:

```sh
gh flarebyte script validate-specs.py -- --help
```

## Runtime changes and regression checks

Use the [change guide](TECHNICAL_DESIGN.md#where-to-make-changes) to locate the
implementation and its focused tests.

```sh
uv run --locked pytest tests/test_planning.py
uv run --locked pytest tests/test_runtime.py tests/test_cli.py
uv run --locked pytest tests/test_security_boundaries.py
```

The runtime tests exercise all supplied plans, saved-plan replay, cross-process
repeatability, profiles, multilingual MIME, exact coverage, tampered batches,
resource limits, unsafe paths, and destination races. Network access is blocked
in the offline-generation test. Stress parsing runs in a separate process with a
five-second timeout and 256 MiB memory budget; macOS uses external RSS monitoring
because its `RLIMIT_AS` setting is unavailable. The macOS test needs permission to
run `ps` when executed in a restricted sandbox.

The packaged `src/astrea/data/catalog.json` contains MVP metadata copied from the
specification tables. Update it together with the source tables when changing
supported fixtures, profiles, regions, or parameters; a regression check enforces
consistency. Runtime schemas, localized templates, and passive assets are also
packaged under `src/astrea/data/`. Keep asset provenance and safety inventory in
sync with attachment changes. Localized templates still need human language review.

## Code metadata

Run `make thoth-meta` before a substantial review to refresh the tracked
`thoth-meta/**/*.thoth.yaml` overview. This optional workflow needs
[thoth](https://github.com/flarebyte/thoth-ostraca), Node.js 24+, and npm/npx.
The pipelines use the published `maat-ostraca@0.9.0` analyzer; its first run
requires registry access. It statically analyzes Python without importing or
executing the project.

```sh
make thoth-meta          # source and tests
make thoth-python       # source and maintenance scripts
make thoth-python-test  # tests
thoth search --root ./thoth-meta --term storage --fields purpose,responsibilities
```

The two root `pipeline-python*-maat.thoth.cue` files are maintained unchanged in
`baldrick-reserve/shared/python/all/`: neither names this package nor assumes a
`src/` layout. Discovery respects `.gitignore` and excludes common environments,
build outputs, and metadata. Files under `test/` or `tests/`, or named `test_*.py`
or `*_test.py`, go to `thoth-meta/python-test`; other Python files go to
`thoth-meta/python`. This includes maintenance and release scripts. Adjust the
filters for repositories with different test conventions.

Each summary contains imports and sorted function, method, and class names;
test summaries also contain statically detected test titles. These titles are
an orientation aid, not a pytest collection count. Curate `meta.purpose`,
`meta.responsibilities`, and `meta.architecture_notes` in the YAML files: reruns
merge structural fields while preserving those authored fields. Review metadata
alongside code changes. Deleted or moved source files require removing or moving
their old metadata explicitly; the pipelines do not prune stale files.

Debug JSON goes to ignored `temp/pipeline-python*-maat.json`. Keep the YAML
tracked.

### Syncing shared pipelines

This workflow also needs GitHub CLI with the `gh arrow` extension.
The Makefile records both reserve source/destination pairs. `make reserve-check`
checks drift; `make reserve-sync` replaces those two local configs. Neither runs
automatically during builds or metadata generation. Both targets use your global
`~/.gh-arrow` mappings, with no config override or revision pin. Map
`baldrick-reserve` to your local checkout to pick up improvements from its
working tree, including uncommitted changes. Without a matching global mapping,
Arrow fetches the repository's default branch from GitHub.

Run `make reserve-check` to review differences, then `make reserve-sync` to copy
the reserve versions into this repository. Review the resulting diff and run
`make thoth-meta` after changing the pipelines.
Keep package-specific curation in each repository.

## Changing specifications

Read [doc/design-meta/AGENTS.md](doc/design-meta/AGENTS.md) before changing files
under that directory. Use the [retrieval guide](doc/design-meta/examples/retrieval.md)
and canonical [concept registry](doc/design-meta/examples/concepts.csv) to find
the relevant contracts and rows.

Edit authored inputs under `doc/design-meta/examples/` and the assembly config
`doc/design-meta/app.cue`. Do not hand-edit `doc/design/specification.md`.
CSV records must remain on one physical line, use stable unique IDs, and refer
to registered concepts. Quote comma-separated tag cells. Manifest example
concepts and tags must match their fixture definitions.

Documentation generation requires `sh`, Python 3, GitHub CLI with `gh flarebyte`,
and [flyb](https://github.com/flarebyte/baldrick-flying-buttress). Inspect tool
availability and installation guidance with:

```sh
make check-tools
make install-tools-help
```

After editing design sources:

```sh
make doc-design
```

This validates specification metadata, runs `flyb validate`, then regenerates the
Markdown with `flyb generate markdown`. Review the generated diff alongside the
source changes. The reference `.eml` is hand-authored; if its bytes change, update
the corresponding manifest sizes and checksums.

## Preparing a change

Keep runtime implementation in `src/astrea/` and regression tests in `tests/`.
Changes to validator behavior should include tests for valid input and the
relevant failure cases. Update examples and authored documentation when contracts
or contributor workflows change, and clearly distinguish proposed behavior from
implemented behavior.

Before submitting, run the checks relevant to the change and describe the result
and any checks you could not run. For Python changes, run formatting, lint, tests,
and coverage; for design changes, validate and regenerate the design documentation.

## Publishing a release

See the [release guide](doc/releasing.md) for Trusted Publisher setup, the manual
release workflow, and recovery after partial publication. Release preflight tests
are separate from the default pytest suite:

```sh
python3 -m unittest discover -s .github/scripts -p 'test_*.py'
```
