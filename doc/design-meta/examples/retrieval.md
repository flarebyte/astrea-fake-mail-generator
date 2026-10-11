# Find specification records without reading the full report

Start with `concepts.csv`, the canonical registry of semantic groups. Each concept has an `id`, a short description, and a parent. Root concepts have an empty parent; child concepts use their immediate dotted ancestor. For example, `fixture.mime` belongs to `fixture`. Concept IDs are lowercase dot-separated words, not versions or individual fixture IDs.

Use one primary `concept` per record. Reuse it across tables to connect a feature, its rules, configuration fields, and implementation tools. Choose the existing group that best describes the record; add a concept only when it enables a useful new query. Broader searches include descendants. Concepts classify specifications; they do not change fixture behavior, relationships, phases, or generation settings.

## Source folders

Keep the layout shallow so agents can select a file type before searching its contents:

```text
examples/
  concepts.csv       # Canonical concept registry
  overview.md        # Purpose and source index
  retrieval.md       # Search conventions and commands
  contracts.md       # Generation rules
  tables/            # CSV specification tables
  plans/             # Editable *.astrea-plan.json examples
  domains/           # One-domain-per-line *.astrea-domains.txt lists
  reference/         # Hand-authored .eml and its matching manifest
```

These folders organize specification sources. Generated email batches still use one flat output folder. Paths in `app.cue` are relative to `doc/design-meta`; `domain_file` paths are relative to their plan file. The file-based example uses `../domains/example.astrea-domains.txt`. A reference manifest's email paths are relative to its own folder.

## Which tables carry search metadata

| File | Added columns | Reason |
| --- | --- | --- |
| `tables/features.csv` | `concept` | Find requirements for a particular subsystem. |
| `tables/constraints.csv` | `concept` | Retrieve its safety, output, and generation rules. |
| `tables/fixtures.csv` | `concept`, `tags` | Group cases and filter content, scripts, encodings, or stress properties. |
| `tables/plan-fields.csv` | `concept` | Find configuration fields belonging to that subsystem. |
| `tables/cli.csv` | `concept` | Locate the related command interface. |
| `tables/tech.csv` | `concept` | Find tools selected to implement that subsystem. |

`tables/fixture-parameters.csv`, `tables/profiles.csv`, `tables/regions.csv`, and `tables/glossary.csv` stay unchanged. Their existing `fixture_id`, `kind`, locale, and term fields already support focused lookups. Search these directly by their existing IDs instead of adding uniform concept columns with little filtering value.

Existing columns remain in their original order; search metadata is appended. Each record occupies one physical line. The `tags` cell is optional and may be empty. When it contains multiple keywords, use a standard quoted CSV cell, for example `"rtl,arabic,unicode,attachment"`. Keywords are lowercase with optional hyphens, comma-separated without spaces, and unique within the record. Tags describe useful secondary properties; they have no separate registry and do not duplicate every existing column.

The existing semicolon-separated lists (such as `feature_ids` and `valid_pairings`) keep their format. Only `tags` uses comma-separated keywords inside a single CSV cell. Use a CSV library to edit or transform these files; splitting records on every comma breaks quoted tags.

## Native search examples

Run these from the repository root. `rg` returns only matching records with filenames and line numbers. Read the table header before interpreting a record.

```sh
# List only editable plan examples.
rg --files doc/design-meta/examples/plans -g '*.astrea-plan.json'

# List only specification tables.
rg --files doc/design-meta/examples/tables -g '*.csv'

# Discover the exact period concept in the registry.
rg -n '^generation[.]periods,' doc/design-meta/examples/concepts.csv

# Retrieve related period rules, requirements, and plan fields across tables.
rg -n ',generation[.]periods(,|$)' doc/design-meta/examples/tables -g '*.csv'

# Search all generation concepts, including descendants.
rg -n ',generation[.][a-z0-9.]+(,|$)' doc/design-meta/examples/tables -g '*.csv'

# Retrieve MIME structure and fixture-parameter configuration records.
rg -n ',fixture[.](mime|parameters)(,|$)' doc/design-meta/examples/tables -g '*.csv'

# Follow the named nested fixture into its parameter table.
rg -n '^parameter[.][^,]+,fixture[.]uk[.]nested,' doc/design-meta/examples/tables/fixture-parameters.csv

# Match rtl as a complete keyword in the final tags cell (quoted or single tag).
rg -n ',"([^"]*,)?rtl(,[^"]*)?"$|,rtl$' doc/design-meta/examples/tables/fixtures.csv

# Find files relevant to parser stress work without reading every matching row.
rg -l ',safety[.]stress(,|$)' doc/design-meta/examples/tables -g '*.csv'

# Inspect selected table headers.
head -n 1 doc/design-meta/examples/tables/features.csv doc/design-meta/examples/tables/constraints.csv

# Equivalent exact-concept search with standard grep.
grep -nE ',generation\.periods(,|$)' doc/design-meta/examples/tables/*.csv
```

Match concepts as comma-delimited fields rather than using `rg fixture`, which also finds unrelated record IDs and prose. Search exact concepts first, then widen to a subtree or use fixture tags. Parent descriptions live in the registry; files without a `concept` column can still contain relevant detail accessible through the IDs in retrieved records.

## Manifest and documentation

Each generated manifest message copies `concept` and `tags` from its source fixture. The manifest uses a JSON string for the concept and an array of keywords for tags, for example `"concept": "fixture.content"` and `"tags": ["plain-text", "ascii"]`. These are output search metadata, not plan inputs, parser assertions, or email headers. Editing them must not change seeds, message IDs, dates, domains, or `.eml` bytes. They do change the manifest metadata. The registry remains canonical: do not define concepts independently in a manifest.

`app.cue` includes the concept registry and passes enriched CSV files to flyb's existing table renderer. The renderer handles the new columns and quoted cells directly; it needs no separate CSV preprocessing. The report includes a link to this retrieval guide.

## Validation and generation

```sh
# Validate every CSV, concept link, and manifest's copied metadata.
python3 scripts/validate-specs.py

# Check validator behavior, including broken CSVs and unknown concepts.
python3 -B -m unittest discover -s tests -v

# Validate sources first, then run flyb validation and Markdown generation.
sh scripts/generate-design.sh
```

The validator scans CSVs and example manifests recursively, with `concepts.csv` at the examples root as the canonical registry. It uses only Python's standard library. It checks UTF-8 CSV parsing, column counts, unique/nonempty column names, nonempty/unique IDs within each table, one-line records, concept IDs and parents, concept references, tags, and agreement between fixture metadata and manifest messages. It rejects duplicate JSON keys and invalid manifest metadata. Parent links must follow the dotted hierarchy, which prevents cycles. It does not validate every CLI/runtime rule; those implementation tests remain separate.
