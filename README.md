# astrea-fake-mail-generator
Generate fake `.eml` email files for tests.

The Python CLI is currently specified in [doc/design-meta/examples](doc/design-meta/examples/overview.md). Start with the [generated specification](doc/design/specification.md) for fixture coverage, CLI commands, expected test results, and optional parser stress cases with fixed limits.

Output is an ordinary folder of `.eml` files plus `batch.astrea-plan.json` (saved generation settings) and `batch.astrea-manifest.json` (file index and expected test results). Maildir, mbox, mailbox import/export, and sending email are out of scope. See the [glossary](doc/design-meta/examples/tables/glossary.csv) for definitions.

Regenerate the design documentation with:

```sh
sh scripts/generate-design.sh
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

For selective specification retrieval, start with [concepts.csv](doc/design-meta/examples/concepts.csv) and the [coding-agent search guide](doc/design-meta/examples/retrieval.md). Validate search metadata with `python3 scripts/validate-specs.py`; run its regression checks with `python3 -B -m unittest discover -s tests -v`.
