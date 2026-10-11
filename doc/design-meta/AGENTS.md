# Navigate design specifications by task

This directory contains the source specifications for the proposed Python email generator. Start with the task map below, then retrieve matching records and follow their IDs. Read additional files only when the task needs them. Use [examples/overview.md](examples/overview.md) for product context and [examples/tables/glossary.csv](examples/tables/glossary.csv) for unfamiliar terms.

All paths in the task map are relative to this directory. All shell commands below run from the repository root.

## Task map

| Task | Concepts to search | Start with | Example or next step |
| --- | --- | --- | --- |
| Commands, options, diagnostics | `tooling.cli`, `generation.validation` | `examples/tables/cli.csv` | `examples/contracts.md`: Running the CLI; Errors and completion checks |
| Plan fields and fixture selection | `generation.plan`, `fixture.parameters` | `examples/tables/plan-fields.csv`, `examples/tables/fixture-parameters.csv` | `examples/plans/example.astrea-plan.json`; contracts: Selecting cases and counting files |
| Date periods and email counts | `generation.periods` | `examples/tables/plan-fields.csv` | `examples/plans/monthly.astrea-plan.json`; contracts: Titled date periods |
| Test domains and file references | `generation.domains` | `examples/tables/plan-fields.csv` | `examples/plans/file-domains.astrea-plan.json`, `examples/domains/example.astrea-domains.txt` |
| Bodies, attachments, encodings, threads | `fixture.content`, `fixture.attachments`, `fixture.encoding`, `fixture.threading` | `examples/tables/fixtures.csv` | Follow `feature_ids` into `examples/tables/features.csv` |
| MIME nesting and fixture settings | `fixture.mime`, `fixture.parameters` | `examples/tables/fixtures.csv`, `examples/tables/fixture-parameters.csv` | `examples/plans/nested.astrea-plan.json` |
| Client and provider headers | `fixture.profiles`, `fixture.headers` | `examples/tables/profiles.csv`, `examples/tables/fixtures.csv` | `examples/plans/outlook.astrea-plan.json`; check `valid_pairings` |
| Languages, regions, writing systems | `fixture.localization` | `examples/tables/regions.csv`, `examples/tables/fixtures.csv` | Filter fixtures by locale or tags such as `rtl` |
| Safety, parser stress, resource limits | `safety.content`, `safety.stress`, `safety.limits` | `examples/tables/constraints.csv`, `examples/tables/fixtures.csv` | `examples/plans/stress.astrea-plan.json`; contracts: Parser stress cases |
| Output files, assertions, repeatability | `generation.output`, `generation.manifest`, `generation.reproducibility` | `examples/tables/constraints.csv` | `examples/reference/` contains a matching manifest and hand-authored email; contracts: Output folder and manifest; Making output repeatable |
| Python tools, packaging, dependencies | `tooling.development` and the task's concept | `examples/tables/tech.csv` | Search by the task's concept to find related tools |
| Documentation assembly and search metadata | `tooling.documentation` | `app.cue`, `examples/concepts.csv` | [examples/retrieval.md](examples/retrieval.md); `../../scripts/validate-specs.py` |

## Retrieve only what the task needs

1. Choose a concept from the map; confirm its meaning in `examples/concepts.csv`, the canonical registry.
2. Search that concept across tables, then read the headers of matching files to interpret their columns.
3. Follow record IDs into related tables. `profiles.csv`, `regions.csv`, `fixture-parameters.csv`, and `glossary.csv` have useful existing fields instead of a `concept` column.
4. Read the relevant section of `examples/contracts.md` and the named example when detailed behavior is needed. Use the generated `../design/specification.md` when a complete report is requested.

```sh
# Locate the period concept and related records.
rg -n '^generation[.]periods,' doc/design-meta/examples/concepts.csv
rg -n ',generation[.]periods(,|$)' doc/design-meta/examples/tables -g '*.csv'
head -n 1 doc/design-meta/examples/tables/plan-fields.csv

# Find a fixture's row and its parameter definitions.
rg -n '^fixture[.]uk[.]nested,' doc/design-meta/examples/tables/fixtures.csv
rg -n ',fixture[.]uk[.]nested,' doc/design-meta/examples/tables/fixture-parameters.csv

# Locate contract sections before reading a selected section.
rg -n '^## ' doc/design-meta/examples/contracts.md

# Discover available plan examples without reading their contents.
rg --files doc/design-meta/examples/plans -g '*.astrea-plan.json'
```

See [examples/retrieval.md](examples/retrieval.md) for subtree searches, exact tag matching, and equivalent `grep` commands.

## Editing specifications

Edit sources under `examples/` and update `app.cue` when source paths or report structure change. Generate `../design/specification.md` with the script below. Preserve stable record IDs and relationships; reuse registered concepts. Keep each CSV record on one physical line, preserve column order, and use a CSV library when changing quoted cells. Fixture tags use comma-separated keywords in a quoted cell; existing semicolon-separated relationship lists retain their format.

Paths in `app.cue` are relative to this directory. A plan's `domain_file` is relative to that plan; a reference manifest's email path is relative to its own folder. The source subfolders do not change the CLI's flat output-folder contract.

```sh
# Validate specification sources and regenerate Markdown through flyb.
sh scripts/generate-design.sh

# Run these regression checks when changing the validator.
python3 -B -m unittest discover -s tests -v
```

The generator script checks CSV integrity, concept references, and manifest search metadata, then runs flyb validation and Markdown generation. It does not validate every runtime contract or implement the proposed CLI.
