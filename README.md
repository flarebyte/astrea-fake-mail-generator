# astrea-fake-mail-generator
Generate fake `.eml` email files for tests.

The Python CLI is currently specified in [doc/design-meta/examples](doc/design-meta/examples/overview.md). Start with the [generated specification](doc/design/specification.md) for fixture coverage, CLI commands, expected test results, and optional parser stress cases with fixed limits.

Output is an ordinary folder of `.eml` files plus `batch.astrea-plan.json` (saved generation settings) and `batch.astrea-manifest.json` (file index and expected test results). Maildir, mbox, mailbox import/export, and sending email are out of scope. See the [glossary](doc/design-meta/examples/glossary.csv) for definitions.

Regenerate the design documentation with:

```sh
flyb validate --config doc/design-meta
flyb generate markdown --config doc/design-meta
```

The proposed runtime command is `uv run --locked astrea`; implementation is not included yet.

Generation settings belong in the plan file:

```sh
uv run --locked astrea plan --template core > custom123.astrea-plan.json
# Edit the plan to select fixtures and set count, seed, and other settings.
uv run --locked astrea generate --plan custom123.astrea-plan.json --out ./fixtures
```

`generate` accepts only `--plan`, `--out`, and optional `--json-diagnostics`. See [plan settings](doc/design-meta/examples/plan-fields.csv).

Set allowed domains using either a `domains` JSON array in the plan or `domain_file` pointing to an `.astrea-domains.txt` file with one domain per line. All domains must end in `.test`. See [the example list](doc/design-meta/examples/example.astrea-domains.txt) and [file-based plan](doc/design-meta/examples/file-domains.astrea-plan.json).
