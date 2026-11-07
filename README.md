# astrea-fake-mail-generator

Astrea generates repeatable batches of synthetic `.eml` files for testing email
parsing, display, indexing, attachments, and reply threads. It works offline and
writes an ordinary folder of emails, a saved generation plan, and a manifest of
expected test results. It does not send email or access email accounts.

## Quick start

From a checkout, install [uv](https://docs.astral.sh/uv/) and sync the environment.
The package requires Python 3.12+; local development pins Python 3.14.6.
Generation currently supports macOS and Linux filesystems with exclusive rename
support. The Linux publication path has not yet been verified on a Linux host.

```sh
uv sync --locked
uv run --locked astrea plan --template core > sample.astrea-plan.json
uv run --locked astrea plan --plan sample.astrea-plan.json
uv run --locked astrea generate --plan sample.astrea-plan.json --out ./fixtures
uv run --locked astrea validate --input ./fixtures
```

The core template creates 100 emails dated in January 2025. Edit the plan before
generation to change periods, counts, fixture selections, profiles, seed, or limits.
The output folder must not already exist; its parent must exist and its path must
not contain symlinks or `..` components.

```text
fixtures/
  000001-fixture.ar.notification.eml
  ...
  batch.astrea-plan.json
  batch.astrea-manifest.json
```

The manifest records file hashes, decoded-content expectations, ordered headers,
MIME structure, attachments, and thread links. Validation recomputes required
fixture expectations from the saved plan, so editing the manifest cannot weaken
those checks. Replaying the saved plan with the same software produces identical
email bytes and JSON:

```sh
uv run --locked astrea generate --plan fixtures/batch.astrea-plan.json --out ./replayed
```

## Select test cases

```sh
uv run --locked astrea list fixtures --json
uv run --locked astrea list profiles --json
uv run --locked astrea list locales --json
uv run --locked astrea list packs --json
uv run --locked astrea list limits --json
```

The core pack has 15 cases and needs at least 17 files per period, including a
complete three-email thread. It covers UK/US English, French, German, Spanish,
Italian, Japanese, and Arabic; synthetic client/provider profiles; plain text and
HTML; passive attachments; inline images; forwarded messages; and nested MIME.
Templates are project-authored examples; language review is still needed before
claiming production-quality localized prose. Faker fallback locales are recorded
for generated names and never substitute for localized body templates.

All generation settings live in the [plan](doc/design-meta/examples/tables/plan-fields.csv).
`generate` accepts only `--plan`, `--out`, and optional `--json-diagnostics`.
Provide allowed domains through either a `domains` array or a `domain_file`
pointing to a one-domain-per-line `.astrea-domains.txt` file. Every domain must end
in `.test`. Saved plans embed the normalized list.

Example plans:

- [Monthly counts](doc/design-meta/examples/plans/monthly.astrea-plan.json):
  30 emails in January and 55 in February.
- [Outlook profiles](doc/design-meta/examples/plans/outlook.astrea-plan.json):
  invoices, forwarded messages, and Spanish confirmations.
- [Nested MIME](doc/design-meta/examples/plans/nested.astrea-plan.json):
  fixture-specific MIME depth of 8.
- [File-based domains](doc/design-meta/examples/plans/file-domains.astrea-plan.json):
  a local allowlist instead of inline domains.

Maildir, mbox, mailbox import/export, weighted selection, legacy encodings, and
additional regional coverage are outside the implemented MVP.

## Parser stress fixtures

Stress cases require explicit selection plus `include_stress: true` in the plan.
The stress template selects all 16 cases, including bounded deep/wide MIME,
malformed headers/boundaries/encodings, truncation, and advertised filename cases.

```sh
uv run --locked astrea plan --template stress > stress.astrea-plan.json
uv run --locked astrea generate --plan stress.astrea-plan.json --out ./parser-stress
uv run --locked astrea validate --input ./parser-stress
```

Content is passive, but difficult structures can crash weak parsers. Astrea never
automatically opens the files or parses stress output in its own process.
Run downstream parser tests in a separate process with time and memory limits
and networking disabled. Mutation metadata records original/final hashes and
byte edits; malformed messages are never parsed and rewritten by the generator.

## Diagnostics

Exit codes are 0 for success, 2 for invalid requests or plans, and 1 for file-access
errors or failed batch checks. Add `--json-diagnostics` for structured errors on
stderr; command results use stdout.

## Development and design

- [Contributing](CONTRIBUTING.md): setup, checks, and specification maintenance.
- [Technical design](TECHNICAL_DESIGN.md): components, data flow, and boundaries.
- [Generated specification](doc/design/specification.md) and
  [generation contracts](doc/design-meta/examples/contracts.md).
- [AI agent task map](doc/design-meta/AGENTS.md),
  [concept registry](doc/design-meta/examples/concepts.csv), and
  [targeted search guide](doc/design-meta/examples/retrieval.md).

The design specification describes the runtime contracts and roadmap. Edit its
authored inputs under `doc/design-meta` through the owning workflow, then run
`make doc-design`.

## License

See [LICENSE](LICENSE) for the MIT license.
