# Generation rules

## Purpose and scope

Generate a new folder containing fake `.eml` email files for tests. Include `batch.astrea-plan.json` to repeat generation and `batch.astrea-manifest.json` to describe the files and their expected properties. Maildir, mbox, mailbox import/export, sending email, and accessing email accounts are out of scope.

A **fixture** defines a test case. A **plan** says which cases to generate. A **manifest** lists the files actually generated and what tests should check. See [glossary.csv](glossary.csv) for the other terms used in these specs.

## Running the CLI

Package the implementation under `src/astrea/` with an `astrea` console command. Use Python 3.12 or newer and commit `uv.lock`. Record the exact Python version used for repeatable reference files. Installing dependencies may require networking; generating emails must work offline. Templates and attachments must be included in the installed package.

```sh
uv run --locked astrea list fixtures --json
uv run --locked astrea plan --template core > custom123.astrea-plan.json
# Edit the JSON file to set periods, seed, languages, and other settings.
uv run --locked astrea plan --plan custom123.astrea-plan.json
uv run --locked astrea generate --plan custom123.astrea-plan.json --out ./fixtures
uv run --locked astrea validate --input ./fixtures --json-diagnostics
uv run --locked astrea plan --template stress > parser-tests.astrea-plan.json
uv run --locked astrea generate --plan parser-tests.astrea-plan.json --out ./parser-stress
```

Implementation steps: check arguments, select supported fixtures, plan the files, build email parts, write email bytes, apply any requested format errors, check the results, and complete the output folder. Check client/provider profile combinations, fixture requirements, and the domain list before writing files.

## Plan-driven generation

`generate` requires `--plan <name>.astrea-plan.json` and `--out <folder>`. Its only additional option is `--json-diagnostics`. It has no count, seed, language, profile, depth, stress, or limit overrides. These settings belong in the plan so one file describes the whole test batch.

`plan --template core` prints an editable normal-batch template. `plan --template stress` prints a template that selects the stress pack and sets `include_stress` to `true`. The default template is core. Each template includes the required fields and useful starting values. Edit the JSON to change the batch.

`plan --plan <file>` checks an existing plan and prints a preview with the complete computed email list. It does not generate `.eml` files and cannot be combined with `--template`. This preview uses the same planning rules as `generate`.

See `plan-fields.csv` for field names, defaults provided by templates, and validation rules. Required fields must be present in an input plan; `generate` never fills them from command-line options or environment variables. Fixture-specific optional settings use the documented fixture defaults.

The plan's `periods` specifies date ranges and email counts. Its `selection` chooses packs, fixture IDs, locales, and optional profile overrides. `fixture_parameters` contains settings for individual fixtures, such as nesting depth, transfer encoding, or a deliberate format-error variant. `limits` contains the processing limits. The output location stays on the CLI so the same plan can generate the same batch in different folders.

Editable plans omit the computed `messages` array. `generate` computes it and includes it in the saved `batch.astrea-plan.json`. A saved plan is valid input for another run. When `messages` is present, check that it matches the plan settings and current fixture definitions; reject conflicts rather than silently changing the file list. Derive expected test results from fixture rules, not user-supplied expectations.

## Example with header profiles

`outlook.astrea-plan.json` selects three fixtures and sets both profiles explicitly:

```json
"client_profile": "client.outlook-desktop",
"provider_profile": "provider.outlook"
```

The client profile adds example Outlook desktop headers such as `X-Mailer`, `Thread-Index`, and `Thread-Topic`. The provider profile adds example delivery headers such as `Received`, `Authentication-Results`, and `X-MS-Exchange-Organization-SCL`. All domain values still come from the plan's allowed `.test` domains. These are synthetic examples, not authenticated emails from Microsoft.

The plan generates PDF invoices, forwarded emails, and Spanish travel confirmations: 30 files in January and 55 in February. All selected fixtures support this profile combination. Setting either profile to `null` uses that fixture's default for that profile.

```sh
uv run --locked astrea generate --plan doc/design-meta/examples/outlook.astrea-plan.json --out ./outlook-fixtures
```

## Titled date periods

A plan can generate different email counts for several periods:

```json
"periods": [
  {
    "id": "january-2025",
    "title": "January 2025",
    "start": "2025-01-01",
    "end": "2025-01-31",
    "count": 30
  },
  {
    "id": "february-2025",
    "title": "February 2025",
    "start": "2025-02-01",
    "end": "2025-02-28",
    "count": 55
  }
]
```

This generates 85 `.eml` files in one folder: 30 dated in January and 55 dated in February. See `monthly.astrea-plan.json` for a complete example.

`start` and `end` are ISO 8601 calendar dates (`YYYY-MM-DD`). Both days are included. Interpret the range in UTC from the start day's midnight through the end day's 23:59:59. Equal dates allow a single-day period. Use real calendar dates, including leap-year rules. The plan has no top-level `count` or `base_date`; total count is the sum of period counts.

Each period needs a unique stable `id`, a nonempty documentation `title`, and a positive integer `count`. IDs use lowercase ASCII letters, digits, and hyphens. Keep periods in chronological order without overlapping dates; gaps are allowed. Titles describe periods in the saved plan and manifest and do not change email contents. All periods share the plan's fixtures, languages, profiles, domains, and limits. Period-specific fixture overrides are outside the MVP scope.

Plan each period separately. Include every selected case in each period, keep complete thread groups within that period, and reject a count that cannot meet those rules. The 10000-file limit applies to the sum across all periods. Changing one period must not change the email contents generated for an unchanged period, although global output filenames may be renumbered.

Spread dates evenly across the range in file order, using whole seconds. For `N > 1`, let `S` be UTC start midnight and `L` be the last included second; file `i` (zero-based within the period) uses `S + floor(i * (L - S) / (N - 1))`. For `N = 1`, use the midpoint `S + floor((L - S + 1) / 2)`. This rule is repeatable and keeps every Date within the period. It does not require random date sampling. Thread members receive consecutive slots and increasing dates. All allowed date ranges have enough seconds for the supported file count.

Write the email Date header in its normal RFC email format with UTC offset `+0000`; store the same instant in the plan preview and manifest as an ISO timestamp ending in `Z`. Simulated delivery-header timestamps use the same instant in MVP. These dates do not constrain appointment or receipt dates mentioned in the body unless the fixture defines that relationship.

## Selecting cases and counting files

Only fixtures marked MVP are available in the first release. The core pack covers English, European Latin-script languages, Japanese (`ja_JP`), and Arabic (`ar_EG`). Later releases add more languages and cases.

Each supported language or format-error variant is a separate test case. Sort selected cases by fixture ID, locale, and profile IDs so CSV row order does not change the result.

Coverage mode generates every selected case once in each period before repeating cases. The core pack contains 15 cases and needs at least 17 `.eml` files per period: most cases produce one file, while `fixture.uk.thread` produces three. Each period’s `count` counts files, including every email in a thread.

Within each period, after generating each case, repeat cases in the same order until that period’s requested count is reached. Keep thread groups complete. Skip a group if it cannot fit the remaining count and try the next case. If no complete group fits, return `E_COVERAGE_COUNT`. A thread-only batch must have a count divisible by three. Never silently drop cases, cut a thread short, or change the requested count.

Phase 2 adds weighted proportions. For each period, use integer weights, round allocations to whole case groups, and use fixture IDs to break ties. Reject a request if a period count cannot be met with complete groups.

The plan’s `selection.locales` selects existing language variants; it does not automatically translate fixtures. Reject incompatible selections rather than silently ignoring them. Empty fixture or locale lists mean all supported cases within the selected packs, not all cases in the entire catalog.

Reject unknown JSON fields, unavailable fixture/profile/error IDs, and conflicting settings. Support only the current plan format; there are no format-version fields, compatibility modes, or migrations. Derive expected test results from the fixture definitions rather than trusting values supplied in a plan.

## Configurable test domains

Provide exactly one of these fields in the plan:

```json
"domains": ["example.test", "newletter.test", "blue.test"]
```

or:

```json
"domain_file": "example.astrea-domains.txt"
```

The text file is UTF-8 with one domain per line:

```text
example.test
newletter.test
blue.test
```

Resolve a relative file path from the folder containing the plan, not from the shell's working folder. Read the file once before planning. Ignore blank lines, trim surrounding whitespace, and convert domains to lowercase. Preserve input order. Comments are not supported. Reject an empty list, duplicate domains after normalization, invalid DNS hostnames, URLs, email addresses, wildcard names, trailing dots, and domains outside `.test`. Each JSON item must be a string. Use ASCII DNS labels; a label may contain letters, digits, and internal hyphens, has at most 63 characters, and cannot start or end with a hyphen. The full hostname is at most 253 characters and must contain a label before `.test`. Allow names such as `mail.blue.test`, but use only explicitly listed names rather than inventing subdomains. Limit the source to 1000 domains and a 64 KiB text file.

Use the list for sender/recipient addresses, Message-ID domains, Content-IDs, simulated delivery hostnames, authentication examples, and URL hosts. Client/provider names describe header styles; they do not force actual vendor domains. Existing `example.test` values in examples illustrate one allowed domain, not a hardcoded rule.

Assign domains by cycling through the ordered list using `(email_index + role_offset) % domain_count`, where `email_index` is zero-based within its period. Fixed role offsets are sender 0, recipient 1, Message-ID 2, Content-ID 3, delivery hostname 4 plus hop index, authentication identity 0, and URL host 1. Multiple values in the same role add their zero-based position to the offset. This produces varied but predictable domains. Keep thread participant addresses consistent by using the first email's index for participant fields across the thread. Record actual values in the manifest. A small batch need not use every domain. The same normalized list must produce identical output whether it came from JSON or text.

The saved batch plan replaces `domain_file` with the normalized `domains` array. Include that array in the manifest too. This makes replay independent of the original text file and records the domains that were actually used. Changing the input file affects a new run, never an already saved batch plan. A missing or unreadable source file is an error before any output is written. There are no CLI domain overrides.

## Making output repeatable

The same plan and installed software must produce identical email bytes and JSON output. Use uv.lock to keep dependencies consistent. Plans and manifests do not contain version fields; repeatability across software updates is not guaranteed.

Use the batch seed to derive separate seeds for each email and content field. For implementation, hash consistently formatted JSON with SHA-256. Include batch seed, period ID, fixture ID, locale, repetition index within the period, thread member index, and field name. Do not include the period title or global file index. This keeps one field's random choices from affecting another field.

Fix dates, message IDs, MIME boundaries, header order, line wrapping, encodings, and attachment bytes. Do not use the current time, machine name, local language settings, Python `hash()`, global random state, or directory listing order. Use Unicode NFC normalization except when a fixture explicitly tests another form. Keep existing message IDs stable when the requested count increases.

## Writing email files

Normal emails follow RFC 5322 and MIME rules. Write bytes with CRLF line endings and an explicit email serialization policy. Use UTF-8 body text by default, RFC 2047 for non-ASCII subjects/display names, and RFC 2231 for non-ASCII attachment filenames. Raw UTF-8 headers and older character encodings are explicit Phase 2 options.

Use repeatable MIME boundaries and check that a boundary does not occur inside its parts. Respect line-length limits in normal emails. Assign dates using the period rule above. MVP writes UTC dates throughout; locale-specific date wording in body text remains a separate fixture property. Later timezone/DST header tests must use a fixed timezone-data version and remain within the period when converted to UTC.

Number MIME parts by position: root `1`, first child `1.1`, second child `1.2`. An attached email (`message/rfc822`) has its own root counted as a child. Count containers, text parts, attachments, and attached email roots. Record type, depth, character encoding, transfer encoding, disposition, and Content-ID for each part.

Root depth is 1. The nested fixture ends in a plain-text/HTML alternative. At depth 2 this is a root `multipart/alternative` with two text children. Each additional level wraps it in one `multipart/mixed` container. Normal depth is at most 16; explicit stress cases allow at most 64.

Expected results cover both file bytes and decoded content. Check header order, repeated headers, line wrapping, encodings, subjects, recipients, text facts, part structure, attachment checksums, and reply links. Record absent properties too, such as Bcc. Optional Bcc recipient expectations are test metadata only; they are not written into the email headers. Plain-text and HTML alternatives describe the same facts. Packaged attachments have fixed contents and metadata.

## Parser stress cases

Stress cases require a selected stress pack or fixture and `include_stress: true` in the plan. That setting alone does not select any cases. Content remains passive, but a weak parser may still crash on the structure. Astrea never automatically opens generated files or runs the parser being tested.

Deep and wide MIME cases follow the format rules and have `validity: stress-valid`. Malformed cases break a specific format rule and have `validity: malformed`. Ordinary cases have `validity: valid`.

For a malformed case, first build a normal email, then apply one named direct byte edit. Do not parse and rewrite it afterward, since that might repair the intended error. Record the original checksum, edit offsets, removed byte counts, inserted bytes in base64, final checksum, and planned error code. A filename traversal case changes an attachment's advertised filename only; it never changes the output file path.

Supported error codes are `MIME_MISSING_CLOSE`, `MIME_BOUNDARY_REUSED`, `MIME_BOUNDARY_MISMATCH`, `HEADER_DUPLICATE_CONTENT_TYPE`, `HEADER_BROKEN_FOLD`, `HEADER_LINE_TOO_LONG`, `HEADER_BODY_SEPARATOR_MISSING`, `TRANSFER_INVALID_BASE64`, `TRANSFER_TRUNCATED_QP`, `CHARSET_MISMATCH`, and `MESSAGE_TRUNCATED`. These are Astrea labels. Different parsers may use different names for the same problem.

A parser test may accept the file, report a format error, or reject it because of a resource limit. A crash, hang, excessive memory use, unsafe attachment path, or unexpected network access is a test failure. Run parser tests separately with a timeout, memory limit, and networking disabled. Suggested starting limits are 5 seconds and 256 MiB; adjust them for the target parser/platform.

Enforce the maximums in `constraints.csv` before and during writing. Count actual bytes, including base64 expansion and deliberate byte edits. Count headers inside all nested parts. Use empty text parts for large sibling-count tests. Avoid algorithms that require unlimited recursion or exponential memory. Users may lower limits but cannot raise the fixed maximums.

## JSON filenames

Use `<name>.astrea-<purpose>.json` for Astrea-owned JSON files. The last extension stays `.json` so editors and tools recognize the format. The prefix is a user-chosen label, such as `custom123` or `example`.

- Plans end in `.astrea-plan.json`, for example `custom123.astrea-plan.json`.
- Manifests end in `.astrea-manifest.json`, for example `custom123.astrea-manifest.json`.
- Domain lists end in `.astrea-domains.txt`, for example `custom123.astrea-domains.txt`.
- Any future Astrea configuration file follows the same pattern with its own purpose name and real format extension.

Generated batches use `batch.astrea-plan.json` and `batch.astrea-manifest.json` by default. Saved plans may use another prefix. `generate --plan` requires the plan suffix and checks the JSON fields and settings; a filename alone does not prove valid contents. `validate --input` finds the single file ending in `.astrea-manifest.json` in the supplied folder and reports an error if none or more than one exists. It checks the contents before using them. It does not scan for plan files; use `generate --plan` to choose a saved plan explicitly.

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

`batch.astrea-plan.json` saves the complete generation settings and the computed `messages` list. It contains selected fixtures, languages, profiles, seed, titled date periods and their counts, fixture parameters, limits, and the normalized domain list. External domain-file references are replaced by the inline list. It contains no machine-specific output path.

`batch.astrea-manifest.json` is the generated-file index and expected test results. It has one entry per `.eml` file containing:

- Relative filename, source fixture ID, period ID, and generated ISO date.
- Language, header profiles, and normal/stress classification.
- File size and SHA-256 checksum.
- Expected headers, decoded text, MIME parts, attachments, and reply links.
- Deliberate format errors or stress parameters, when applicable.

Batch-level fields record seed, total bytes, and file counts by fixture. A `periods` summary repeats each ID, title, range, and actual count; the manifest’s top-level `count` is the derived total. Record coverage counts separately for each period. The `assets` list describes the packaged attachments used: ID, type, size, checksum, source, license, and safety review record. Attachments are embedded in the `.eml` files; they are not extracted into another folder. Omit the current time, host paths, and local usernames from metadata.

For example, `fixture.us.pdf` defines an invoice case. Its manifest entry points to the generated file and says that tests should find one `application/pdf` attachment with a known filename and checksum. The fixture is the definition; the manifest describes its generated instance.

`example.astrea-plan.json` shows inline domains; `file-domains.astrea-plan.json` shows a local domain-file reference. `example.astrea-domains.txt` contains the matching text list. `example.astrea-manifest.json` shows proposed output fields. Zero checksums and zero sizes are illustrative, not values for a runnable test. Define one JSON schema for plans and one for manifests, rejecting unknown fields. JSON schemas validate structure and types; they do not introduce version selection or support for older formats.

Write to a temporary sibling folder first. Check the complete batch, then rename it to the requested output folder. Reject existing destinations, symlinked paths, and path traversal. There is no overwrite option in MVP. On failure, remove only this run's temporary files and leave no completed output folder. Write diagnostics to stderr and command results to stdout.

## Errors and completion checks

Return 0 for success, 2 for invalid requests or plans, and 1 for file-access errors or failed generated-file checks. Error codes include `E_CONFIG`, `E_SELECTION`, `E_PROFILE_PAIR`, `E_COVERAGE_COUNT`, `E_LIMIT`, `E_OUTPUT_EXISTS`, `E_UNSAFE_PATH`, `E_IO`, `E_HASH`, and `E_ASSERTION`. JSON errors include the code, a clear message, the affected field or fixture, and relevant limits. Do not dump message bodies or arbitrary file contents into errors.

MVP checks must cover repeatable output, every core case and MVP profile, exact file counts per period, dates inside each range, complete threads within periods, offline generation, multilingual text, safe attachments, normal MIME correctness, and accurate stress errors within limits. Compare fixture expectations with both direct file-byte inspection and a standard-library parser with processing limits. Never run an unlimited parser on stress files inside the CLI process.
