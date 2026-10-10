# Astrea fake email generator

Astrea is a Python CLI that creates local batches of synthetic `.eml` messages for email-client rendering, MIME parsing, indexing, attachment handling, threading, and mailbox import tests. The proposed console entry point is `astrea`; the packaged project uses `pyproject.toml`, `uv.lock`, and `uv run --locked astrea`. These documents are specifications; the CLI is not implemented yet.

The MVP establishes representative multilingual test coverage with UK and US English, several European Latin-script languages, Japanese, and Arabic. This initial set exercises accented Latin characters, Japanese characters, and right-to-left text alongside Gmail-style and Outlook-style delivery headers, Thunderbird-style desktop headers, plain text, HTML, inert attachments, nested MIME, and bounded parser stress cases. Subsequent releases expand regional and language coverage as reviewed templates become available. Delivery stages describe implementation scope and test diversity rather than a ranking of languages or communities. Geography and writing system are independent; “Latin” means a writing system, including accented characters, rather than the Latin language.

## Design inputs

- `tech.csv`: selected runtime, development, and documentation technologies with rationale and official references.
- `features.csv`: stable feature IDs, delivery phases, contracts, and acceptance criteria.
- `fixtures.csv`: concrete fixture/use-case catalog, MIME shapes, locales, profile pairings, and assertions.
- `regions.csv`: delivery stages and regional language coverage. Multiple regions share the initial stage, including Japanese and Arabic coverage.
- `profiles.csv`: independent client and provider header profiles and their compatibility.
- `cli.csv`: proposed subcommands, options, defaults, and examples.
- `constraints.csv`: deterministic generation, safety, resource, and filesystem rules.
- `contracts.md`: batch planning, serialization, manifest, error, and testing contracts.
- `plan.example.json` and `manifest.example.json`: illustrative version 1 payloads for a single plain-text message. Zero hashes are placeholders, not golden fixture hashes.

CSV IDs remain stable. Semicolon-separated cells are ordered lists, not additional CSV columns. Fixture rows with multiple locales expand into distinct variants. MIME shape notation describes children in wire order: `mixed`, `alternative`, and `related` mean `multipart/*`; `plain`, `html`, and attachment labels mean leaf media types. These inputs are authoritative; `app.cue` assembles them into `doc/design/specification.md`.

## Safety and parser robustness

All content is invented, all email identities use reserved `.test` domains, and all assets are reviewed and inert. Templates resemble everyday messages without copying private correspondence or generating real payment details. Provider-style headers are synthetic examples, not authenticated correspondence or a promise of exact vendor behavior.

“Safe content” and “safe to feed to every parser” are different guarantees. Opt-in stress fixtures intentionally exercise structural weaknesses: recursion, large sibling lists, malformed boundaries, duplicate headers, decoder recovery, truncation, and dangerous advertised attachment filenames. These contain no exploit code, malware, executable attachments, remote resources, or decompression bombs. A vulnerable parser can still crash or exhaust its resources. The CLI creates these files without automatically opening them; downstream tests should process them in isolated, bounded subprocesses.

Stress generation is available in the MVP, requires explicit selection plus `--include-stress`, and always has hard caps. Normal batches and import exports exclude it by default. Adding an arbitrary unbounded crash generator or exploit catalog is outside this design.

## Technology and standards basis

The Python [email package](https://docs.python.org/3/library/email.html) provides the message tree, byte parser, generator, and policy controls used for normal MIME output. [RFC 2046](https://www.rfc-editor.org/rfc/rfc2046) specifies the underlying multipart media types. The [uv project execution guide](https://docs.astral.sh/uv/concepts/projects/run/) describes running an installed project command in its managed environment. [Faker documentation](https://faker.readthedocs.io/en/stable/) describes locale providers and seeded generation; reproducibility requires pinned versions and disclosed locale fallbacks. Curated language templates supplement Faker because names and lorem text alone do not make realistic regional correspondence.

Exact vendor fingerprints remain an evidence task: acquire reviewed, sanitized reference samples and record client/provider version and provenance before advertising exact fidelity. No real-mail samples are required for the initial synthetic profiles.
