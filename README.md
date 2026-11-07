# astrea-fake-mail-generator

Astrea is a planned Python CLI for generating synthetic `.eml` files to test email
parsing, display, indexing, attachments, and reply threads. The design covers
multilingual content, client/provider header profiles, nested MIME, and optional
bounded parser stress cases.

**Current status:** the repository contains specifications, reference examples,
a Python package skeleton, and specification validation tooling. The `astrea`
console command and email generation are not implemented yet.

## Try the specification tooling

From the repository root, with Python 3.12 or newer installed:

```sh
python3 scripts/validate-specs.py
python3 -m unittest discover -s tests
```

The validator uses only the standard library. A successful run prints
`Specification CSVs, concepts, and manifest metadata are valid.`

Read the [generated specification](doc/design/specification.md) for the full
proposed interface and fixture coverage. For local development setup and the
managed checks, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Planned usage

These commands describe the proposed interface; they will work once the CLI is
implemented:

```sh
uv run --locked astrea plan --template core > custom123.astrea-plan.json
# Edit the plan to select fixtures and set periods, seed, and other settings.
uv run --locked astrea generate --plan custom123.astrea-plan.json --out ./fixtures
```

Output will be one ordinary folder containing `.eml` files,
`batch.astrea-plan.json` (saved generation settings), and
`batch.astrea-manifest.json` (file index and expected test results). Maildir,
mbox, mailbox import/export, and sending email are outside the design's scope.

`generate` accepts only `--plan`, `--out`, and optional `--json-diagnostics`.
Generation settings belong in the [plan](doc/design-meta/examples/tables/plan-fields.csv).
Provide allowed domains through either a `domains` array or a `domain_file`
pointing to a one-domain-per-line `.astrea-domains.txt` file. All domains must end
in `.test`.

Example plans illustrate common cases:

- [Monthly counts](doc/design-meta/examples/plans/monthly.astrea-plan.json):
  30 emails in January and 55 in February, all in one output folder.
- [Outlook profiles](doc/design-meta/examples/plans/outlook.astrea-plan.json):
  explicit client/provider profiles with invoices, forwarded emails, and Spanish confirmations.
- [Nested MIME](doc/design-meta/examples/plans/nested.astrea-plan.json):
  fixture-specific MIME depth of 8.
- [File-based domains](doc/design-meta/examples/plans/file-domains.astrea-plan.json):
  a local allowlist instead of inline domains.
- [Parser stress cases](doc/design-meta/examples/plans/stress.astrea-plan.json):
  explicit opt-in with fixed resource limits.

## Documentation

- [Contributing](CONTRIBUTING.md): setup, checks, and documentation maintenance.
- [Technical design](TECHNICAL_DESIGN.md): current components and planned runtime boundaries.
- [Design source overview](doc/design-meta/examples/overview.md) and
  [generation contracts](doc/design-meta/examples/contracts.md).
- [AI agent task map](doc/design-meta/AGENTS.md),
  [concept registry](doc/design-meta/examples/concepts.csv), and
  [targeted search guide](doc/design-meta/examples/retrieval.md).
- [Glossary](doc/design-meta/examples/tables/glossary.csv).

The design Markdown is generated from `doc/design-meta`; regenerate it with
`make doc-design` after setting up the documentation tools described in the
contributing guide.

## License

See [LICENSE](LICENSE) for the MIT license.
