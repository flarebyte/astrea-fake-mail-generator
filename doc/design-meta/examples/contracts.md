# CLI and fixture contracts

## Packaging and workflow

Use a `src/astrea/` Python package with the `astrea` console script. Configure Python 3.12 or newer, commit `uv.lock`, and record the exact interpreter patch used for golden fixtures. `uv sync --locked` prepares dependencies; generation itself is offline. Packaged templates and assets must work when installed outside this repository. Proposed examples:

```sh
uv run --locked astrea list fixtures --json
uv run --locked astrea plan --count 24 --seed 42 > batch-plan.json
uv run --locked astrea generate --plan batch-plan.json --out ./fixtures
uv run --locked astrea validate --input ./fixtures --json-diagnostics
uv run --locked astrea generate --pack stress --include-stress --count 20 --out ./parser-stress
```

The CLI has layers for argument validation, catalog resolution, planning, semantic message construction, byte serialization, bounded raw mutations, validation, and atomic output publication. Client profiles govern composition hints; provider profiles govern synthetic delivery trace headers. Validate fixture requirements as well as profile pairings before writing. A profile override that removes a fixture's required headers is an error.

## Planning and exact coverage

Resolve pack, fixture, locale, client, and provider selections against a versioned catalog. MVP ships only MVP rows; selecting a future-phase row fails clearly. Region delivery order governs implementation and curated pack ordering. Coverage planning sorts expanded variants by fixture ID then locale then profile IDs for stable tie breaking, independent of CSV row order.

An expanded fixture variant is a coverage unit. Most units produce one wire message; `fixture.uk.thread` produces an atomic group of three. The core pack has 13 units and a minimum of 15 wire messages. Count includes all group members, not just top-level scenarios. A coverage request below the selected units' minimum fails with `E_COVERAGE_COUNT` and the required count. After one of each unit, cycle the stable order, adding only complete groups that fit the remaining count. Continue scanning for a fitting group; fail if none fits. A thread-only request must therefore have a count divisible by three. Do not truncate threads or silently reduce count. Weighted mode in Phase 2 allocates unit groups with the same exact-count constraint; reject unrepresentable allocations.

`--locale` is a strict filter of declared locale variants, not permission to translate every fixture automatically. Explicit selections that cannot all be satisfied fail. A supplied plan is fully resolved and cannot be combined with generation selectors. Reject unknown fields, unsupported schema/catalog/profile versions, unknown mutation IDs, and contradictory expectations. Regenerate derived expectations from catalog rules rather than trusting arbitrary plan values. `plan` emits no wall-clock values or machine-specific paths.

Derive per-message and per-component seeds from SHA-256 over canonical JSON containing schema version, batch seed, fixture ID, locale, occurrence, thread member index, and component namespace. Normalize strings to NFC except fixtures explicitly testing another form. Never use Python `hash()`, global random state, wall clock, hostnames, OS locale, or filesystem enumeration order. Message identities use deterministic `example.test` addresses. Thread IDs remain stable as count grows; record generation revisions so library or template updates are deliberate fixture migrations.

## Serialization and structural assertions

Normal messages use RFC 5322 headers and MIME media types. Use bytes serialization, explicit policy, CRLF, a deterministic header order, fixed folding rules, deterministic multipart boundaries, fixed transfer encodings, and explicit charset. The default is UTF-8 body content with RFC 2047 encoding for non-ASCII display names and subjects. RFC 6532 raw UTF-8 headers are a later explicit profile, not the default. Boundary generation must detect collisions with payload bytes deterministically. Valid headers obey wire line limits. Date uses a fixed UTC base instant, a one-minute increment per global message index, and a recorded offset; provider trace hops are fixed offsets relative to Date. For MVP use fixed winter timezone mappings and record the mapping revision. Later timezone/DST coverage must pin timezone data and record its revision.

MIME root path is `1`, first child `1.1`, and subsequent siblings follow wire order. Embedded `message/rfc822` roots count as contained nodes, including their own headers. Record every node's path, depth, media type, charset, disposition, content ID, transfer encoding, and decoded hash where applicable. Root depth is 1; total node count includes multipart containers and embedded messages. The regular nested fixture has a linear `multipart/mixed` chain ending in `multipart/alternative(plain;html)`; requested depth includes the final text leaves. To realize depth 2 the root is directly `multipart/alternative`. Increasing depth wraps this root with `depth - 2` mixed containers. Stress depth uses the same construction. Normal limits are 16 levels; stress limits are 64.

Raw assertions preserve header order, exact casing when profiled, multiplicity, byte ranges, folding, transfer encoding, and boundary values. Semantic assertions independently record decoded subject/body facts, recipients, content IDs, attachment checksums, and thread links. Expected absence includes Bcc on the wire, active HTML, and unrequested attachment/profile headers. Bcc envelope expectations belong in the manifest only. HTML and plain alternatives express the same facts. Attachments have stable packaged bytes and deterministic metadata; no timestamps from the build machine.

## Stress mutation contract

First construct a bounded normal byte representation and its expectations. Apply exactly one named mutation per malformed fixture variant at a recorded byte range; no object-model round trip afterward, which could repair the intentional defect. The stress width and depth cases are structurally valid and tagged `stress-valid`. For malformed cases record `mutation_id`, original fixture hash, ordered edits with byte offsets/remove lengths/inserted bytes as base64, final hash, anomaly codes, and intended raw invariants. The advertised traversal filename fixture changes header metadata only; generated output names never use that metadata.

Mutation variants expand into separate coverage units just like locale variants. Allowed anomaly codes include `MIME_MISSING_CLOSE`, `MIME_BOUNDARY_REUSED`, `MIME_BOUNDARY_MISMATCH`, `HEADER_DUPLICATE_CONTENT_TYPE`, `HEADER_BROKEN_FOLD`, `HEADER_LINE_TOO_LONG`, `HEADER_BODY_SEPARATOR_MISSING`, `TRANSFER_INVALID_BASE64`, `TRANSFER_TRUNCATED_QP`, `CHARSET_MISMATCH`, and `MESSAGE_TRUNCATED`. These are Astrea codes, not promises of a particular parser library's defect names. Include the chosen variant and parameter values in the resolved plan; selection is predictable.

Downstream expectation is a controlled outcome: bounded parse success, documented defect, or explicit rejection/resource-limit error. Crashes, hangs, excessive memory, unsafe attachment paths, and unintended network activity are failures of the tested parser. Suggested test harness defaults are a 5-second wall timeout and 256 MiB process memory cap, adjusted explicitly for the target platform. Astrea does not launch or manage the downstream parser in the MVP.

Apply hard limits in `constraints.csv` to raw generation and mutations. MIME node width tests use empty text leaves to stay within byte budgets. Header budget includes nested entity headers; MIME node count and attachment limits are separate. Lower requested caps are allowed; higher caps fail. Use iterative planning and counting, avoid exponential trees, account for base64 expansion, and enforce actual serialized byte totals during writes.

## Output and manifest

A successful batch publishes one new directory:

```text
fixtures/
  valid/000001-fixture.uk.plain.eml
  stress/000002-fixture.stress.boundary.eml
  plan.json
  manifest.json
  assets.json
```

The layout illustrates both categories; files exist only for selected messages. File numbering is the deterministic global message order, with six-digit indices and ASCII fixture IDs. Every entry in `manifest.json` references exactly one relative `.eml` path and includes schema/generator/catalog/template/profile/toolchain versions, seed namespace, fixture/locale/region/script, validity, size, raw SHA-256, expected ordered headers, decoded facts, MIME tree, attachment expectations, thread links, and stress annotations. Batch metadata contains exact selections, total bytes, coverage counts, and expected minimum. No generated-at timestamp, host path, or local username appears.

`assets.json` inventories used assets by stable ID, media type, byte length, SHA-256, provenance, license, and safety review revision. Assets are embedded in messages, not copied from arbitrary user paths. A separate `manifest.example.json` shows a minimal plain-message entry; hashes and toolchain versions there are explicit illustrative placeholders. It is an example shape rather than an executable golden batch. Implement strict versioned JSON schemas for plans and manifests with unknown-field rejection before adding the CLI.

Publish by writing to a private sibling staging directory and atomically renaming after all checks pass. Existing destination, symlinked paths, and traversal are errors; MVP has no overwrite flag. On failure leave no published batch and clean only files created by this invocation. Check budget estimates before writing and actual totals while streaming. Diagnostic output is separate from JSON plan/catalog stdout.

Maildir export in Phase 2 preserves normal `.eml` bytes and deterministically creates `cur/`, `new/`, and `tmp/`. Files have stable names and optional fixture-defined flags; users import the result using their client or local test tooling. Stress output is excluded and cannot be exported into a mailbox through this command. mbox is a later adapter because envelope separators and From-line escaping alter the container representation.

## Diagnostics and acceptance

Success returns 0; IO or generated-corpus validation failure returns 1; invocation, unsupported selection, invalid plan, and resource-limit request errors return 2. Stable diagnostic codes include `E_CONFIG`, `E_SELECTION`, `E_PROFILE_PAIR`, `E_COVERAGE_COUNT`, `E_LIMIT`, `E_PLAN_VERSION`, `E_OUTPUT_EXISTS`, `E_UNSAFE_PATH`, `E_IO`, `E_HASH`, and `E_ASSERTION`. JSON diagnostics contain code, message, field/fixture context, and relevant limits. Errors never dump credentials, arbitrary file contents, or message bodies.

MVP acceptance requires byte-identical replay under a pinned toolchain; every core fixture and profile exercised; exact count and intact thread groups; offline generation; correct multilingual decoded content; reviewed asset checksums; no active or reachable content; normal tree/header/encoding consistency; and stress mutation correctness within limits. Verify plan expectations against an independent raw-byte inspector as well as a bounded standard-library parser. Add importer smoke tests when Maildir is implemented. Do not validate stress output by invoking an unbounded parser on the main CLI process.

Before implementation, finalize dependency pins, reviewed localized text, inert asset inventory, strict JSON schemas, and golden profile examples. These are implementation deliverables, not reasons to postpone the current specification.
