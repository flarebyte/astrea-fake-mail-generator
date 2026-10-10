# Generation rules

## Purpose and scope

Generate a new folder containing fake `.eml` email files for tests. Include `batch.astrea-plan.json` to repeat generation and `batch.astrea-manifest.json` to describe the files and their expected properties. Maildir, mbox, mailbox import/export, sending email, and accessing email accounts are out of scope.

A **fixture** defines a test case. A **plan** says which cases to generate. A **manifest** lists the files actually generated and what tests should check. See [glossary.csv](glossary.csv) for the other terms used in these specs.

## Running the CLI

Package the implementation under `src/astrea/` with an `astrea` console command. Use Python 3.12 or newer and commit `uv.lock`. Record the exact Python version used for repeatable reference files. Installing dependencies may require networking; generating emails must work offline. Templates and attachments must be included in the installed package.

```sh
uv run --locked astrea list fixtures --json
uv run --locked astrea plan --count 24 --seed 42 > custom123.astrea-plan.json
uv run --locked astrea generate --plan custom123.astrea-plan.json --out ./fixtures
uv run --locked astrea validate --input ./fixtures --json-diagnostics
uv run --locked astrea generate --pack stress --include-stress --count 20 --out ./parser-stress
```

Implementation steps: check arguments, select supported fixtures, plan the files, build email parts, write email bytes, apply any requested format errors, check the results, and complete the output folder. Check client/provider profile combinations and fixture requirements before writing files.

## Selecting cases and counting files

Only fixtures marked MVP are available in the first release. The core pack covers English, European Latin-script languages, Japanese (`ja_JP`), and Arabic (`ar_EG`). Later releases add more languages and cases.

Each supported language or format-error variant is a separate test case. Sort selected cases by fixture ID, locale, and profile IDs so CSV row order does not change the result.

Coverage mode generates every selected case once before repeating cases. The core pack contains 15 cases and needs at least 17 `.eml` files: most cases produce one file, while `fixture.uk.thread` produces three. `--count` counts files, including every email in a thread.

After generating each case, repeat cases in the same order until the requested count is reached. Keep thread groups complete. Skip a group if it cannot fit the remaining count and try the next case. If no complete group fits, return `E_COVERAGE_COUNT`. A thread-only batch must have a count divisible by three. Never silently drop cases, cut a thread short, or change the requested count.

Phase 2 adds weighted proportions. Use integer weights, round allocations to whole case groups, and use fixture IDs to break ties. Reject a request if its count cannot be met with complete groups.

`--locale` selects existing language variants; it does not automatically translate fixtures. Reject incompatible filters rather than silently ignoring them. A saved plan already contains all choices, so only output location and diagnostic format may be added to `generate --plan`.

Reject unknown JSON fields, unsupported versions, unavailable fixture/profile/error IDs, and conflicting settings. Derive expected test results from the fixture definitions rather than trusting values supplied in a plan.

## Making output repeatable

The same plan and software versions must produce identical email bytes and JSON output. Record generator, fixture catalog, template, profile, Python, and dependency versions.

Use the batch seed to derive separate seeds for each email and content field. For implementation, hash consistently formatted JSON with SHA-256. Include format version, batch seed, fixture ID, locale, repetition index, thread member index, and field name. This keeps one field's random choices from affecting another field.

Fix dates, message IDs, MIME boundaries, header order, line wrapping, encodings, and attachment bytes. Do not use the current time, machine name, local language settings, Python `hash()`, global random state, or directory listing order. Use Unicode NFC normalization except when a fixture explicitly tests another form. Keep existing message IDs stable when the requested count increases.

## Writing email files

Normal emails follow RFC 5322 and MIME rules. Write bytes with CRLF line endings and an explicit email serialization policy. Use UTF-8 body text by default, RFC 2047 for non-ASCII subjects/display names, and RFC 2231 for non-ASCII attachment filenames. Raw UTF-8 headers and older character encodings are explicit Phase 2 options.

Use repeatable MIME boundaries and check that a boundary does not occur inside its parts. Respect line-length limits in normal emails. The default date is `2025-01-15T12:00:00Z`; add one minute for each file. Any simulated delivery steps use fixed time differences from that date. MVP uses recorded winter timezone offsets; later DST tests must use a fixed timezone-data version.

Number MIME parts by position: root `1`, first child `1.1`, second child `1.2`. An attached email (`message/rfc822`) has its own root counted as a child. Count containers, text parts, attachments, and attached email roots. Record type, depth, character encoding, transfer encoding, disposition, and Content-ID for each part.

Root depth is 1. The nested fixture ends in a plain-text/HTML alternative. At depth 2 this is a root `multipart/alternative` with two text children. Each additional level wraps it in one `multipart/mixed` container. Normal depth is at most 16; explicit stress cases allow at most 64.

Expected results cover both file bytes and decoded content. Check header order, repeated headers, line wrapping, encodings, subjects, recipients, text facts, part structure, attachment checksums, and reply links. Record absent properties too, such as Bcc. Optional Bcc recipient expectations are test metadata only; they are not written into the email headers. Plain-text and HTML alternatives describe the same facts. Packaged attachments have fixed contents and metadata.

## Parser stress cases

Stress cases require explicit fixture selection and `--include-stress`. That flag alone does not select any cases. Content remains passive, but a weak parser may still crash on the structure. Astrea never automatically opens generated files or runs the parser being tested.

Deep and wide MIME cases follow the format rules and have `validity: stress-valid`. Malformed cases break a specific format rule and have `validity: malformed`. Ordinary cases have `validity: valid`.

For a malformed case, first build a normal email, then apply one named direct byte edit. Do not parse and rewrite it afterward, since that might repair the intended error. Record the original checksum, edit offsets, removed byte counts, inserted bytes in base64, final checksum, and planned error code. A filename traversal case changes an attachment's advertised filename only; it never changes the output file path.

Supported error codes are `MIME_MISSING_CLOSE`, `MIME_BOUNDARY_REUSED`, `MIME_BOUNDARY_MISMATCH`, `HEADER_DUPLICATE_CONTENT_TYPE`, `HEADER_BROKEN_FOLD`, `HEADER_LINE_TOO_LONG`, `HEADER_BODY_SEPARATOR_MISSING`, `TRANSFER_INVALID_BASE64`, `TRANSFER_TRUNCATED_QP`, `CHARSET_MISMATCH`, and `MESSAGE_TRUNCATED`. These are Astrea labels. Different parsers may use different names for the same problem.

A parser test may accept the file, report a format error, or reject it because of a resource limit. A crash, hang, excessive memory use, unsafe attachment path, or unexpected network access is a test failure. Run parser tests separately with a timeout, memory limit, and networking disabled. Suggested starting limits are 5 seconds and 256 MiB; adjust them for the target parser/platform.

Enforce the maximums in `constraints.csv` before and during writing. Count actual bytes, including base64 expansion and deliberate byte edits. Count headers inside all nested parts. Use empty text parts for large sibling-count tests. Avoid algorithms that require unlimited recursion or exponential memory. Users may lower limits but cannot raise the fixed maximums.

## JSON filenames

Use `<name>.astrea-<purpose>.json` for Astrea-owned JSON files. The last extension stays `.json` so editors and tools recognize the format. The prefix is a user-chosen label, such as `custom123` or `example`.

- Plans end in `.astrea-plan.json`, for example `custom123.astrea-plan.json`.
- Manifests end in `.astrea-manifest.json`, for example `custom123.astrea-manifest.json`.
- Any future Astrea configuration file follows the same pattern with its own purpose name and real format extension.

Generated batches use `batch.astrea-plan.json` and `batch.astrea-manifest.json` by default. Saved plans may use another prefix. `generate --plan` requires the plan suffix and checks the JSON fields and version; a filename alone does not prove valid contents. `validate --input` finds the single file ending in `.astrea-manifest.json` in the supplied folder and reports an error if none or more than one exists. It checks the contents before using them. It does not scan for plan files; use `generate --plan` to choose a saved plan explicitly.

The `.eml` extension stays unchanged. `app.cue` and `uv.lock` belong to flyb and uv, so their tool-defined names stay unchanged.

## Output folder and manifest

Write all `.eml` files directly inside the requested output folder:

```text
fixtures/
  000001-fixture.uk.plain.eml
  000002-fixture.us.pdf.eml
  000003-fixture.ar.notification.eml
  batch.astrea-plan.json
  batch.astrea-manifest.json
```

This is an ordinary folder, not a mailbox format. Filenames use a six-digit index and the fixture ID. If stress cases are selected, their `.eml` files go in the same folder and are identified by fixture ID and the manifest's `validity` field.

`batch.astrea-plan.json` is the saved input: selected fixtures, languages, profiles, seed, dates, counts, and limits. It contains no machine-specific output path.

`batch.astrea-manifest.json` is the generated-file index and expected test results. It has one entry per `.eml` file containing:

- Relative filename and source fixture ID.
- Language, header profiles, and normal/stress classification.
- File size and SHA-256 checksum.
- Expected headers, decoded text, MIME parts, attachments, and reply links.
- Deliberate format errors or stress parameters, when applicable.

Batch-level fields record software versions, seed, total bytes, and file counts by fixture. The `assets` list describes the packaged attachments used: ID, type, size, checksum, source, license, and safety review version. Attachments are embedded in the `.eml` files; they are not extracted into another folder. Omit the current time, host paths, and local usernames from metadata.

For example, `fixture.us.pdf` defines an invoice case. Its manifest entry points to the generated file and says that tests should find one `application/pdf` attachment with a known filename and checksum. The fixture is the definition; the manifest describes its generated instance.

`example.astrea-plan.json` and `example.astrea-manifest.json` show proposed JSON fields. Zero checksums, zero sizes, and version placeholders are illustrative, not values for a runnable test. Implement strict versioned JSON schemas that reject unknown fields before building the CLI.

Write to a temporary sibling folder first. Check the complete batch, then rename it to the requested output folder. Reject existing destinations, symlinked paths, and path traversal. There is no overwrite option in MVP. On failure, remove only this run's temporary files and leave no completed output folder. Write diagnostics to stderr and command results to stdout.

## Errors and completion checks

Return 0 for success, 2 for invalid requests or plans, and 1 for file-access errors or failed generated-file checks. Error codes include `E_CONFIG`, `E_SELECTION`, `E_PROFILE_PAIR`, `E_COVERAGE_COUNT`, `E_LIMIT`, `E_PLAN_VERSION`, `E_OUTPUT_EXISTS`, `E_UNSAFE_PATH`, `E_IO`, `E_HASH`, and `E_ASSERTION`. JSON errors include the code, a clear message, the affected field or fixture, and relevant limits. Do not dump message bodies or arbitrary file contents into errors.

MVP checks must cover repeatable output, every core case and MVP profile, exact file counts, complete threads, offline generation, multilingual text, safe attachments, normal MIME correctness, and accurate stress errors within limits. Compare fixture expectations with both direct file-byte inspection and a standard-library parser with processing limits. Never run an unlimited parser on stress files inside the CLI process.
