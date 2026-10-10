# Astrea fake email generator

Astrea is a Python CLI that creates local batches of synthetic `.eml` messages for testing email display, parsing, indexing, attachments, and reply threads. Output is an ordinary folder of `.eml` files with supporting JSON. Mailbox formats such as Maildir and mbox, mailbox import/export, and email delivery are out of scope. The proposed console entry point is `astrea`; the packaged project uses `pyproject.toml`, `uv.lock`, and `uv run --locked astrea`. These documents are specifications; the CLI is not implemented yet.

The MVP establishes representative multilingual test coverage with UK and US English, several European Latin-script languages, Japanese, and Arabic. This initial set exercises accented Latin characters, Japanese characters, and right-to-left text alongside Gmail-style and Outlook-style delivery headers, Thunderbird-style desktop headers, plain text, HTML, inert attachments, nested MIME, and bounded parser stress cases. Subsequent releases expand regional and language coverage as reviewed templates become available. Delivery stages describe implementation scope and test diversity rather than a ranking of languages or communities. Geography and writing system are independent; “Latin” means a writing system, including accented characters, rather than the Latin language.

## Plan-driven command

```sh
uv run --locked astrea generate --plan custom123.astrea-plan.json --out ./fixtures
```

All generation settings come from the plan: titled date periods and their email counts, fixture selection, languages, headers, domains, seed, nesting depth, stress cases, and limits. The command only selects the plan, output folder, and optional JSON error reporting. Use `astrea plan --template core` to get an editable starter plan.

## Fixtures, plans, and manifests

A **fixture** is a test-case definition, such as an invoice with one PDF attachment. A **batch plan** records which fixtures and settings to generate. The **manifest** (`batch.astrea-manifest.json`) lists each generated `.eml` file, its source fixture, and the expected properties tests can check. It is an index of test files and expected results, not a mailbox format.

Example: `fixture.us.pdf` defines the case; `000001-fixture.us.pdf.eml` is one generated email; its manifest entry records the expected PDF filename, type, and checksum.

See [glossary.csv](glossary.csv) for short definitions and examples of the other terms.

Astrea JSON filenames follow `<name>.astrea-<purpose>.json`: plans end in `.astrea-plan.json` and manifests end in `.astrea-manifest.json`. A custom label such as `custom123` is allowed; the final `.json` extension identifies the format.

## Design inputs

- `glossary.csv`: terms used in the specs, with definitions and examples.
- `tech.csv`: selected runtime, development, and documentation technologies with rationale and official references.
- `features.csv`: stable feature IDs, delivery phases, contracts, and acceptance criteria.
- `fixtures.csv`: concrete fixture/use-case catalog, MIME shapes, locales, profile pairings, and assertions.
- `regions.csv`: delivery stages and regional language coverage. Multiple regions share the initial stage, including Japanese and Arabic coverage.
- `profiles.csv`: independent client and provider header profiles and their compatibility.
- `cli.csv`: proposed subcommands, options, defaults, and examples.
- `outlook.astrea-plan.json`: January and February emails with explicit Outlook desktop and Outlook provider header profiles; includes PDF invoices, forwarded messages, and Spanish travel confirmations.
- `monthly.astrea-plan.json`: a complete plan for January (30 emails) and February (55 emails), using ISO date ranges.
- `example.astrea-domains.txt`: one allowed test domain per line; plans can use this file or an inline `domains` array.
- `file-domains.astrea-plan.json`: example plan using the text-file domain source.
- `plan-fields.csv`: generation settings stored in the plan, their starting values, and validation rules.
- `constraints.csv`: deterministic generation, safety, resource, and filesystem rules.
- `contracts.md`: rules for selecting cases, writing files, recording expected results, and reporting errors.
- `example.astrea-plan.json` and `example.astrea-manifest.json`: example JSON documents for a single plain-text message. Zero hashes are placeholders, not reference test checksums.

CSV IDs remain stable. Semicolon-separated cells are ordered lists, not additional CSV columns. Fixture rows with multiple locales expand into distinct variants. MIME shape notation describes children in file order: `mixed`, `alternative`, and `related` mean `multipart/*`; `plain`, `html`, and attachment labels mean parts with no children. These files are the source specifications; `app.cue` assembles them into `doc/design/specification.md`.

## Safety and parser robustness

All content is invented, all email identities use configured `.test` domains from an inline plan array or a one-domain-per-line text file, and all assets are reviewed and inert. Templates resemble everyday messages without copying private correspondence or generating real payment details. Provider-style headers are synthetic examples, not authenticated correspondence or a promise of exact vendor behavior.

“Safe content” and “safe to feed to every parser” are different guarantees. Opt-in stress fixtures intentionally exercise structural weaknesses: recursion, large sibling lists, malformed boundaries, duplicate headers, decoder recovery, truncation, and dangerous advertised attachment filenames. These contain no exploit code, malware, executable attachments, remote resources, or decompression bombs. A vulnerable parser can still crash or exhaust its resources. The CLI creates these files without automatically opening them; downstream tests should process them in isolated, bounded subprocesses.

Stress generation is available in the MVP, requires explicit selection plus `include_stress: true` in the plan, and always has hard caps. Normal batches exclude stress fixtures by default. Adding an arbitrary unbounded crash generator or exploit catalog is outside this design.

## Technology and standards basis

The Python [email package](https://docs.python.org/3/library/email.html) provides the message tree, byte parser, generator, and policy controls used for normal MIME output. [RFC 2046](https://www.rfc-editor.org/rfc/rfc2046) specifies the underlying multipart media types. The [uv project execution guide](https://docs.astral.sh/uv/concepts/projects/run/) describes running an installed project command in its managed environment. [Faker documentation](https://faker.readthedocs.io/en/stable/) describes locale providers and seeded generation; reproducibility requires pinned versions and disclosed locale fallbacks. Curated language templates supplement Faker because names and lorem text alone do not make realistic regional correspondence.

Profiles contain example headers inspired by real clients and providers. They do not promise an exact match to a particular vendor version. To make that claim later, compare with reviewed samples that have private data removed and record the sample source and software version.
