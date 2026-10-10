# Astrea fake email generator specification

Python CLI that generates repeatable folders of safe .eml test files, including optional parser stress cases.

## 01 Product and delivery

### 01 Intent and scope

#### Intent and scope

Astrea is a proposed Python CLI that generates a folder of fake `.eml` email files for tests. Use `uv run --locked astrea`. Mailbox formats, import/export, and sending email are out of scope.

Run `astrea generate --plan custom123.astrea-plan.json --out ./fixtures`. Generation settings come from the plan; CLI options select only the input plan, output folder, and diagnostic format.

A fixture defines a test case. `batch.astrea-plan.json` records what to generate. `batch.astrea-manifest.json` lists the generated files and their expected headers, text, parts, and attachments so tests can check them.

The MVP establishes representative multilingual coverage with UK and US English, several European Latin-script languages, Japanese, and Arabic RTL. It also covers synthetic Gmail/Outlook/Thunderbird header profiles, plain text, HTML, safe attachments, nested MIME, and opt-in bounded parser stress cases. Later releases broaden regional and language coverage as reviewed templates become available.

See [intent, source conventions, and standards references](../design-meta/examples/overview.md). The CLI is specified here and has not been implemented.

### 02 Glossary

#### Glossary

| example | id | meaning | term |
| --- | --- | --- | --- |
| 000001-fixture.uk.plain.eml | glossary.eml | One email stored as a file. It contains headers a body and any MIME parts or attachments. | .eml file |
| fixture.uk.thread defines three related email files | glossary.fixture | A reusable test-case definition with known content and expected properties. A fixture can generate one email or a group of related emails. | Fixture |
| A Japanese notification encoded as UTF-8 | glossary.variant | A specific version of a fixture chosen by language encoding or deliberate format error. | Fixture variant |
| 100 .eml files in ./fixtures | glossary.batch | All email files produced by one generate command. | Batch |
| core for normal test cases; stress for parser robustness tests | glossary.pack | A named group of fixture definitions. | Pack |
| list fixtures --json | glossary.catalog | The list of supported fixtures packs languages and header profiles with their versions. | Fixture catalog |
| batch.astrea-plan.json selects fixture IDs counts seed and languages | glossary.plan | The required JSON input to generate. It sets fixtures file count languages headers seed dates stress permission and limits. | Batch plan |
| A file uses fixture.us.pdf and should contain one PDF attachment | glossary.manifest | The output index in batch.astrea-manifest.json. It lists generated email files their source fixtures checksums and expected test results. | Manifest |
| Subject equals Meeting on Friday; Bcc is absent | glossary.assertion | A property that a test checks against an expected value. | Assertion |
| seed: 42 in an .astrea-plan.json file | glossary.seed | An integer that controls generated random values. Same inputs and software versions give the same output. | Seed |
| sha256 in a manifest entry identifies the exact .eml bytes | glossary.checksum | A fingerprint of file bytes used to check that content has not changed. | SHA-256 checksum |
| client.thunderbird.v1 with provider.generic.v1 | glossary.profile | A named set of example headers and formatting rules for a client or provider. Profiles use synthetic values. | Header profile |
| en_GB for UK English; ja_JP for Japanese; ar_EG for Arabic | glossary.locale | A language and regional variant used for text and formatting. | Locale |
| Arabic HTML body with dir=rtl | glossary.rtl | Right-to-left text direction. Mixed text can also contain left-to-right words or digits. | RTL |
| multipart/alternative holds plain-text and HTML versions | glossary.mime | The email format rules for text HTML attachments and groups of parts. | MIME |
| A text/plain part followed by an application/pdf part | glossary.part | One item in an email structure: text an attachment an embedded email or a container for other parts. | MIME part |
| A root container with direct text children has depth 2 | glossary.depth | Number of part levels from the root to a part. The root has depth 1. | Nesting depth |
| --astrea-boundary-001 | glossary.boundary | A marker in the file that separates parts inside a multipart container. | MIME boundary |
| UTF-8 text represented using quoted-printable | glossary.encoding | Character encoding maps text to bytes; transfer encoding represents those bytes inside the email file. | Character and transfer encoding |
| cid:logo@example.test | glossary.cid | An identifier for an embedded part. HTML can refer to an embedded image using a cid: URL. | Content-ID / CID |
| \r\n | glossary.crlf | Carriage return followed by line feed: the line-ending bytes used in email files. | CRLF |
| One initial email and two replies | glossary.thread | Related emails connected using Message-ID In-Reply-To and References headers. | Thread |
| Deeply nested MIME or a missing closing boundary | glossary.stress | A deliberately difficult parser test with passive content and limited file size part count and depth. | Stress fixture |
| Remove a closing MIME boundary | glossary.mutation | A planned direct edit to generated bytes to create a specific format error. | Mutation |
| Two conflicting Content-Type headers | glossary.malformed | An email that deliberately breaks a format rule. Its manifest records the intended error. | Malformed email |
| MIME_MISSING_CLOSE | glossary.mutationcode | An Astrea identifier for a deliberate format error. A parser may use a different error name. | Anomaly code |
| uv.lock plus an exact Python patch version | glossary.version | Exact Python dependency template and profile versions recorded to make generation repeatable. | Pinned software versions |
| Core multilingual fixtures and bounded stress fixtures | glossary.mvp | The first supported release. Phase 2 Phase 3 and Later describe follow-up work. | MVP |

### 03 CLI features

#### CLI features

| acceptance | contract | feature | id | phase | priority |
| --- | --- | --- | --- | --- | --- |
| The folder contains exactly one .eml file for each manifest entry | Create the requested number of .eml files in a new folder; default 100 | Generate a folder of .eml files | feature.batch | MVP | must |
| Same inputs and software versions produce identical email files and batch.astrea-manifest.json | Use seed 0 by default; derive a separate random seed for each email and content field | Repeatable generation | feature.seed | MVP | must |
| No generation-setting CLI overrides; replaying the saved plan produces identical files and checksums | Require an .astrea-plan.json file for generate; read fixtures counts languages profiles seed dates parameters and limits from it; save the full plan in the batch | Saved generation plan | feature.plan | MVP | must |
| Reject counts too small to include all selected cases; report how many files each fixture produced | Generate each selected fixture variant at least once before repeating cases | Include every selected test case | feature.coverage | MVP | must |
| Produce the requested file count; use fixture IDs to break allocation ties; reject counts that cannot fit complete groups | Phase 2: assign integer weights to fixtures and convert them to whole test-case groups; keep thread groups complete | Control fixture proportions | feature.weighted | Phase 2 | should |
| Core fixtures cover en_GB en_US fr_FR de_DE es_ES it_IT ja_JP ar_EG; check characters encoding and text direction | Start with English European Latin-script languages Japanese and Arabic RTL; add more languages in later releases | Language and writing-system coverage | feature.locale | MVP | must |
| Each manifest entry identifies the two profiles and their versions and expected headers | Use separate named sets of client headers and provider headers; allow only supported combinations | Client and provider header examples | feature.profiles | MVP | must |
| Check header values order repeated headers and encoding; Bcc is absent from the .eml file by default | Generate standard sender recipient date subject and MIME headers; add reply list and delivery headers when requested | Predictable email headers | feature.headers | MVP | must |
| Decoded text and character encoding match the expected values in batch.astrea-manifest.json | Support ASCII and UTF-8 text; use CRLF line endings and a specified transfer encoding | Plain-text emails | feature.text | MVP | must |
| No scripts forms tracking remote images or active links | Support HTML-only emails and emails with both plain-text and HTML versions; escape inserted text | HTML emails | feature.html | MVP | must |
| Attachment type size filename and SHA-256 checksum match the manifest | Attach reviewed PNG JPEG PDF TXT and CSV files with predictable names and contents | Safe test attachments | feature.attachments | MVP | must |
| Each cid: link points to exactly one embedded image in the same related group | Embed images as MIME parts and reference them with cid: links in the HTML | Images inside HTML emails | feature.inline | MVP | must |
| Part paths types order and nesting depth match the manifest | Generate simple multipart emails and nested parts with a requested depth; enforce part-count limits | Simple and nested email parts | feature.nesting | MVP | must |
| Reply links point to generated emails; thread dates increase; attached emails have their own IDs | Generate related emails with Message-ID In-Reply-To and References; support an attached email using message/rfc822 | Replies and forwarded emails | feature.threading | MVP | must |
| Check both encoded file bytes and decoded text or attachment contents | Support 7bit quoted-printable and base64; encode non-ASCII headers with RFC 2047 and filenames with RFC 2231 | Standard email encodings | feature.encoding | MVP | must |
| Reject text that the chosen encoding cannot represent; never silently replace characters | Phase 2: support ISO-8859-1 Windows-1252 ISO-2022-JP and GB18030; add a separate profile for raw UTF-8 headers | Older character encodings | feature.legacy | Phase 2 | should |
| Tests can find each file and check what should be present or absent; expectations come from the fixture rules | Write batch.astrea-manifest.json with one entry per .eml file: source fixture checksum and expected headers text parts and attachments | Generated-file index and expected results | feature.manifest | MVP | must |
| Record each deliberate error or stress parameter and the expected safe parser response | Require both explicit stress-case selection and include_stress: true in the plan; generate deep wide or intentionally malformed emails within fixed limits | Parser robustness test cases | feature.stress | MVP | must |
| Reject requests exceeding limits; leave no completed output folder after failure | Check maximum files bytes parts headers depth and attachments before and during generation | Generation limits | feature.limits | MVP | must |
| Generation works with networking disabled; all attachment contents are reviewed and passive | Generate locally from packaged templates and attachments without sending email or fetching content | Offline generation and safe content | feature.offline | MVP | must |
| Detect changed or missing files; check planned errors in stress cases without unbounded parsing | Check file checksums attachment contents expected headers selected cases and normal MIME structure | Check a generated batch | feature.validate | MVP | must |
| Exit 0 for success; 2 for invalid requests; 1 for file-access errors or failed output checks | Return stable error codes; optionally write error details as JSON | Useful CLI errors | feature.errors | MVP | must |
| JSON output is repeatable for the same inputs | List available fixtures profiles languages packs and limits; show a generation plan without writing emails | List options and preview a batch | feature.inspect | MVP | must |

### 04 Regional coverage roadmap

#### Regional coverage roadmap

| assertions | content_focus | delivery_stage | id | locales | phase | region | scripts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Locale recorded; repeatable offset from fixed dates; £ encoded correctly | GBP receipts DD/MM/YYYY prose British spelling fixed Europe/London winter offset; DST expansion later | 1 | region.uk | en_GB | MVP | United Kingdom | Latin |
| Do not rely on OS language settings; check body date formatting separately from the Date header | USD receipts MM/DD/YYYY prose US spelling America/New_York | 1 | region.us | en_US | MVP | United States | Latin |
| NFC accents preserved in subjects bodies display names and filenames | EUR receipts accents umlauts apostrophes and localized business prose | 1 | region.europe.latin | fr_FR;de_DE;es_ES;it_IT | MVP | Europe Latin scripts | Latin |
| Reviewed Japanese body; encoded subject and display name preserve Japanese characters | UTF-8 Japanese notifications mixed-script display names and subjects | 1 | region.asia.japan | ja_JP | MVP | Japan | Japanese |
| HTML dir=rtl; bidi code points recorded; RFC 2047 subject and RFC 2231 filename; output paths remain ASCII | RTL appointment reminder mixed-script text and Unicode attachment filename | 1 | region.rtl.arabic | ar_EG | MVP | Arabic-language baseline (Egypt locale) | Arabic |
| Script and normalization cases recorded; reviewed localized templates required | Broader diacritics Greek and Cyrillic coverage | 2 | region.europe.expanded | pt_PT;nl_NL;pl_PL;sv_SE;el_GR;uk_UA | Phase 2 | Europe broader coverage | Latin;Greek;Cyrillic |
| Geography independent of script; template locale and effective Faker locale both recorded | INR SGD IDR VND dates Vietnamese combining-mark edge cases | 2 | region.asia.latin | en_IN;en_SG;id_ID;vi_VN | Phase 2 | Asia Latin and English baseline | Latin |
| UTF-8 first; reviewed translations and fonts not assumed on recipient client | CJK wide characters mixed-script names local currency and no-space wrapping | 2 | region.asia.nonlatin | ja_JP;zh_CN;zh_TW;ko_KR;hi_IN;th_TH | Phase 2 | Asia additional scripts | Japanese;Han;Hangul;Devanagari;Thai |
| No real street addresses payment details or reachable contacts | BRL MXN AUD ZAR local business fixtures | 3 | region.world.latin | pt_BR;es_MX;en_AU;en_ZA | Phase 3 | Rest of world Latin and English | Latin |
| Explicit dir attributes and bidi code points in manifest; filenames remain generated ASCII | RTL body mixed-direction subjects and filenames | 3 | region.world.rtl | ar_EG;he_IL | Phase 3 | Middle East and additional RTL coverage | Arabic;Hebrew |
| Reject unsupported languages; record any fallback language used by Faker; do not claim fallback text is translated content | Add locales only with reviewed content and fixture assertions | 4 | region.world.expanded | reviewed-locale-registry | Later | Additional regions | Multiple |

## 02 Fixture coverage

### 01 Fixture and use-case catalog

#### Fixture and use-case catalog

| assertions | client_profile | feature_ids | id | locale | mime_shape | pack | phase | provider_profile | use_case | validity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASCII body; To one address; no attachments; User-Agent present | client.thunderbird.v1 | feature.text;feature.headers | fixture.uk.plain | en_GB | text/plain | core | MVP | provider.generic.v1 | Personal meeting request | valid |
| USD prose; no X-Mailer; HTML-only; no remote URLs | client.gmail-web.v1 | feature.html;feature.profiles | fixture.us.html | en_US | text/html | core | MVP | provider.gmail.v1 | Order confirmation | valid |
| Plain first HTML second; same appointment facts; quoted-printable | client.gmail-web.v1 | feature.html;feature.encoding | fixture.uk.alternative | en_GB | alternative(plain;html) | core | MVP | provider.gmail.v1 | Appointment reminder | valid |
| One application/pdf attachment; hash filename and decoded bytes; Thread-Topic | client.outlook-desktop.v1 | feature.attachments;feature.profiles | fixture.us.pdf | en_US | mixed(plain;pdf) | core | MVP | provider.outlook.v1 | Invoice with PDF | valid |
| French accents; one CID image; related scope and disposition inline | client.gmail-web.v1 | feature.inline;feature.locale | fixture.fr.inline | fr_FR | alternative(plain;related(html;png)) | core | MVP | provider.gmail.v1 | French newsletter with inline logo | valid |
| Five attachments in specified order; umlaut filename RFC 2231 | client.thunderbird.v1 | feature.attachments;feature.nesting | fixture.de.attachments | de_DE | mixed(alternative(plain;html);png;jpeg;pdf;txt;csv) | core | MVP | provider.generic.v1 | German project report | valid |
| RFC 2047 subject; accents; base64 HTML; decoded names | client.outlook-desktop.v1 | feature.encoding;feature.locale | fixture.es.encoded | es_ES | alternative(plain;html) | core | MVP | provider.outlook.v1 | Spanish travel confirmation | valid |
| List-ID and List-Unsubscribe use .test; no real unsubscribe endpoint | client.generic.v1 | feature.headers;feature.locale | fixture.it.list | it_IT | alternative(plain;html) | core | MVP | provider.generic.v1 | Italian community newsletter | valid |
| Group of three; References links; increasing Date; quoted reply body | client.thunderbird.v1 | feature.threading;feature.seed | fixture.uk.thread | en_GB | text/plain per message | core | MVP | provider.generic.v1 | Three-message support conversation | valid |
| Embedded From Subject and Message-ID distinct; manifest includes inner message | client.outlook-desktop.v1 | feature.threading;feature.nesting | fixture.us.forward | en_US | mixed(plain;message/rfc822(plain)) | core | MVP | provider.outlook.v1 | Forwarded message as attachment | valid |
| Default depth 6; requested normal depth 2..16; exact part paths in parent-before-child order and node count | client.generic.v1 | feature.nesting | fixture.uk.nested | en_GB | mixed chain with final alternative(plain;html) | core | MVP | provider.generic.v1 | Nested MIME parser traversal | valid |
| Multiple To and Cc addresses; Reply-To; Bcc recipient listed only in test metadata; header spans multiple lines | client.generic.v1 | feature.headers | fixture.us.recipients | en_US | text/plain | core | MVP | provider.generic.v1 | Team announcement with recipient variants | valid |
| Body is zero decoded bytes; required headers retained | client.generic.v1 | feature.text | fixture.uk.empty | en_GB | text/plain | core | MVP | provider.generic.v1 | Empty message body | valid |
| NFC and explicitly tagged NFD variants; RFC 2231 continuations; source code points asserted | client.thunderbird.v1 | feature.legacy;feature.encoding | fixture.fr.unicode | fr_FR | mixed(plain;txt) | encoding | Phase 2 | provider.generic.v1 | Normalization and filename variants | valid |
| ISO-8859-1 or Windows-1252 selector; charset decoded text and raw bytes asserted | client.generic.v1 | feature.legacy | fixture.de.legacy | de_DE | text/plain | encoding | Phase 2 | provider.generic.v1 | Legacy Western encoding | valid |
| ISO-2022-JP charset; transfer encoding and decoded Japanese text asserted | client.thunderbird.v1 | feature.locale;feature.legacy | fixture.jp.legacy | ja_JP | text/plain | encoding | Phase 2 | provider.generic.v1 | Legacy Japanese service notification | valid |
| One variant per locale; local currency and reviewed body template | client.generic.v1 | feature.locale;feature.html | fixture.asia.latin | en_IN;en_SG;id_ID;vi_VN | alternative(plain;html) | asia-latin | Phase 2 | provider.generic.v1 | Regional receipt | valid |
| Japanese subject body and display name; UTF-8; RFC 2047 subject; decoded Japanese characters preserved | client.thunderbird.v1 | feature.locale;feature.encoding | fixture.jp.notification | ja_JP | alternative(plain;html) | core | MVP | provider.generic.v1 | Japanese service notification | valid |
| Arabic subject body display name and attachment filename; HTML dir=rtl; mixed Arabic and Latin digits; RFC 2231 filename; code points and decoded attachment hash asserted | client.generic.v1 | feature.locale;feature.html;feature.encoding;feature.attachments | fixture.ar.notification | ar_EG | mixed(alternative(plain;html);txt) | core | MVP | provider.generic.v1 | Arabic appointment reminder with text attachment | valid |
| Separate simplified/traditional variants; Unicode subject and filename | client.generic.v1 | feature.locale;feature.encoding | fixture.cn.receipt | zh_CN;zh_TW | mixed(alternative(plain;html);pdf) | asia-nonlatin | Phase 2 | provider.generic.v1 | Chinese order receipt | valid |
| One variant per locale; no silent English body fallback | client.generic.v1 | feature.locale;feature.encoding | fixture.asia.scripts | ko_KR;hi_IN;th_TH | text/plain | asia-nonlatin | Phase 2 | provider.generic.v1 | Multiscript appointment reminder | valid |
| One variant per locale with local date and currency prose | client.generic.v1 | feature.locale;feature.html | fixture.world.latin | pt_BR;es_MX;en_AU;en_ZA | alternative(plain;html) | world-latin | Phase 3 | provider.generic.v1 | Regional delivery update | valid |
| RTL dir attribute; mixed digits and Latin terms; code points asserted | client.generic.v1 | feature.locale;feature.encoding | fixture.world.rtl | ar_EG;he_IL | alternative(plain;html) | world-rtl | Phase 3 | provider.generic.v1 | RTL support conversation | valid |
| Requested depth 17..64; valid MIME; parser accepts or reports resource limit | client.generic.v1 | feature.stress;feature.limits | fixture.stress.depth | en_GB | Nested mixed chain | stress | MVP | provider.generic.v1 | Recursion handling | stress-valid |
| Up to 1000 total MIME nodes; linear generation; node count exact | client.generic.v1 | feature.stress;feature.limits | fixture.stress.width | en_US | mixed with many empty plain parts | stress | MVP | provider.generic.v1 | Large sibling list | stress-valid |
| One selected missing-close reused-boundary or mismatched-boundary mutation; offset and bytes recorded | client.generic.v1 | feature.stress | fixture.stress.boundary | en_GB | Mutated mixed | stress | MVP | provider.generic.v1 | Boundary recovery | malformed |
| One selected duplicate-Content-Type broken-fold oversized-line or missing-separator variant | client.generic.v1 | feature.stress | fixture.stress.headers | en_US | text/plain with mutated headers | stress | MVP | provider.generic.v1 | Header recovery and limits | malformed |
| One selected invalid-base64 truncated-quoted-printable or charset-mismatch variant | client.generic.v1 | feature.stress | fixture.stress.encoding | en_GB | text/plain with mutated payload | stress | MVP | provider.generic.v1 | Transfer decoding recovery | malformed |
| Deterministic cut point; expected missing terminator and incomplete final part | client.generic.v1 | feature.stress | fixture.stress.truncated | en_US | Truncated multipart | stress | MVP | provider.generic.v1 | Truncated message recovery | malformed |
| Inert attachment advertises traversal absolute or bidi filename; outer .eml path always generated ASCII | client.generic.v1 | feature.stress;feature.attachments | fixture.stress.filename | en_GB | mixed(plain;txt) | stress | MVP | provider.generic.v1 | Attachment filename extraction safety | stress-valid |

### 02 Client and provider profiles

#### Client and provider profiles

| accuracy_notes | assertions | id | illustrative_headers | kind | phase | valid_pairings |
| --- | --- | --- | --- | --- | --- | --- |
| Standards baseline | Common RFC headers always present | client.generic.v1 | No client-specific X headers | client | MVP | provider.generic.v1;provider.gmail.v1;provider.outlook.v1 |
| Synthetic webmail approximation; not a claim Gmail always emits this layout | Assert absence of X-Mailer; stable MIME template | client.gmail-web.v1 | No X-Mailer; MIME multipart alternative template | client | MVP | provider.gmail.v1 |
| Illustrative subset; verify against sanitized samples before claiming version accuracy | Versioned placeholder X-Mailer and repeatable synthetic threading fields | client.outlook-desktop.v1 | X-Mailer;Thread-Index;Thread-Topic | client | MVP | provider.outlook.v1;provider.generic.v1 |
| Illustrative desktop subset; not a full header fingerprint | Synthetic User-Agent version and locale-derived Content-Language | client.thunderbird.v1 | User-Agent;Content-Language | client | MVP | provider.generic.v1;provider.gmail.v1;provider.outlook.v1 |
| Illustrative subset | Versioned synthetic value and raw header casing | client.apple-mail.v1 | X-Mailer;Mime-Version | client | Phase 2 | provider.generic.v1 |
| Synthetic delivery trace | Two fixed delivery steps using reserved IPs and .test domains | provider.generic.v1 | Return-Path;Received | provider | MVP | client.generic.v1;client.outlook-desktop.v1;client.thunderbird.v1;client.apple-mail.v1 |
| Synthetic provider-style shape; no real signatures or authentication claims | Placeholder values and example.test authentication identity | provider.gmail.v1 | Received;X-Received;Authentication-Results;X-Google-Smtp-Source | provider | MVP | client.gmail-web.v1;client.generic.v1;client.thunderbird.v1 |
| Synthetic provider-style shape; verify exact values against sanitized samples | Stable synthetic internal/external and SCL cases labeled in manifest | provider.outlook.v1 | Received;Authentication-Results;X-MS-Exchange-Organization-AuthAs;X-MS-Exchange-Organization-SCL | provider | MVP | client.outlook-desktop.v1;client.generic.v1;client.thunderbird.v1 |
| Illustrative subset | Random-looking placeholder value controlled by the seed | provider.yahoo.v1 | Received;X-YMail-OSG | provider | Phase 2 | client.generic.v1 |
| Illustrative subset | Reserved-domain identity and trace ordering | provider.fastmail.v1 | Received;Authentication-Results | provider | Phase 2 | client.generic.v1;client.thunderbird.v1 |
| No fetched or unreviewed provider dumps | Reject uncontrolled raw headers outside stress mutation layer | provider.custom.v1 | Reviewed versioned local profile | provider | Later | compatibility-registry |

## 03 Implementation rules

### 01 Technology choices

#### Technology choices

| constraint | decision | id | phase | rationale | reference | role | technology |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pin exact Python patch for byte-identical saved reference fixtures | selected | tech.python | MVP | Typed Python package with console entry point astrea | https://docs.python.org/3/ | Runtime | Python 3.12+ |
| Dependency setup may use network; fixture generation must be offline | selected | tech.uv | MVP | Use pyproject.toml and uv.lock; uv run --locked astrea | https://docs.astral.sh/uv/concepts/projects/run/ | Environment and invocation | uv |
| Validate all choices and bounds before writes | selected | tech.argparse | MVP | Subcommands and stable help without a CLI framework dependency | https://docs.python.org/3/library/argparse.html | CLI parsing | argparse (stdlib) |
| Fix line endings header order wrapping encodings and boundaries; edit file bytes directly for malformed cases | selected | tech.email | MVP | EmailMessage and BytesGenerator with explicit policy | https://docs.python.org/3/library/email.html | Build and write MIME emails | email (stdlib) |
| Pin version; never use uncontrolled email/url/phone/address providers; record fallback language used by Faker | selected | tech.faker | MVP | Seeded locale providers supplement curated body templates | https://faker.readthedocs.io/en/stable/ | Localized synthetic names and organizations | Faker |
| Faker lorem is not a substitute for natural localized sentences; no external template execution | selected | tech.templates | MVP | Small reviewed templates for receipts newsletters conversations and notifications | https://docs.python.org/3/library/html.html | Realistic body content | Curated UTF-8 templates plus html.escape (stdlib) |
| No remote downloads; PDFs have no JavaScript actions links forms or embedded files; images have bounded dimensions | selected | tech.assets | MVP | Reviewed passive assets reused byte-for-byte with checksums | project-owned-assets | Attachments | Packaged PNG JPEG PDF TXT CSV assets |
| Reject unknown fields; write UTF-8 JSON in a consistent format | selected | tech.json | MVP | Versioned JSON formats and typed Python data models | https://docs.python.org/3/library/json.html | Batch plans and manifest | json and dataclasses (stdlib) |
| Never use process-dependent hash() or global random state | selected | tech.hashlib | MVP | SHA-256 of consistently formatted input and fixture ID | https://docs.python.org/3/library/hashlib.html | Repeatable IDs seeds and checksums | hashlib (stdlib) |
| Reject existing destinations symlinks and path traversal; clean only own staging files | selected | tech.pathlib | MVP | Write to a temporary folder then rename it to the destination | https://docs.python.org/3/library/pathlib.html | Write output files safely | pathlib and tempfile (stdlib) |
| Test dependencies pinned in uv.lock; independently inspect raw output | selected-dev | tech.pytest | MVP | CLI error tests saved reference files manifest checks and content safety checks | https://docs.pytest.org/en/stable/ | Regression and integration checks | pytest |
| Hard bounds and replayable examples; no unbounded fuzzing | candidate-dev | tech.hypothesis | Phase 2 | Exercise MIME trees and selector combinations | https://hypothesis.readthedocs.io/en/latest/ | Bounded combinatorial tests | Hypothesis |
| Pin dev dependency | selected-dev | tech.ruff | MVP | Consistent Python style and static checks | https://docs.astral.sh/ruff/ | Lint and format | Ruff |
| Not a runtime dependency | selected-design | tech.flyb | MVP | Assemble CSV and prose into doc/design | https://github.com/flarebyte/baldrick-flying-buttress | Design documentation generation | flyb |

### 02 CLI commands

#### CLI commands

| command_or_option | contract | default | example | id | phase |
| --- | --- | --- | --- | --- | --- |
| generate | Read all generation settings from the plan; only --plan --out and --json-diagnostics are accepted | plan and output folder required | uv run --locked astrea generate --plan custom123.astrea-plan.json --out ./fixtures | cli.generate | MVP |
| plan | Print an editable plan template as JSON; --template core or stress; does not create email files | core template | uv run --locked astrea plan --template core > custom123.astrea-plan.json | cli.plan | MVP |
| generate --plan | Required .astrea-plan.json input; check settings and version before writing; reject generation-setting CLI overrides | none | uv run --locked astrea generate --plan custom123.astrea-plan.json --out ./fixtures | cli.planfile | MVP |
| plan --plan | Read and check an existing plan; print the full file list and settings as JSON; cannot combine with --template | plan required | uv run --locked astrea plan --plan custom123.astrea-plan.json | cli.preview | MVP |
| list fixtures/profiles/locales/packs | List IDs versions supported combinations and minimum file counts; --json supported | text | uv run --locked astrea list fixtures --json | cli.list | MVP |
| validate --input | Find exactly one .astrea-manifest.json file in the input folder; check its contents then check email files against it and fixture rules | none | uv run --locked astrea validate --input ./fixtures --json-diagnostics | cli.validate | MVP |
| --json-diagnostics | Write error code message affected field and limits as JSON to stderr; keep stdout for command results | false | --json-diagnostics | cli.diagnostics | MVP |
| --version | Print generator fixture catalog and JSON format versions | none | uv run --locked astrea --version | cli.version | MVP |

### 03 Plan settings

#### Plan settings

| field | id | rule | template_default |
| --- | --- | --- | --- |
| schema_version | plan.schema | Required JSON format version; reject unsupported versions | 1 |
| catalog_version | plan.catalog | Required fixture catalog version; reject unavailable versions | 1 |
| generator_version | plan.generator | Required generator version; reject incompatible versions | current release |
| seed | plan.seed | Required integer from 0 to 18446744073709551615; controls repeatable random choices | 0 |
| base_date | plan.date | Required UTC date and time; increment one minute per email file | 2025-01-15T12:00:00Z |
| count | plan.count | Required total .eml file count including all thread members; maximum 10000 | 100 |
| mode | plan.mode | Required allocation mode; coverage includes every selected case; weighted is Phase 2 | coverage |
| include_stress | plan.stress | Required boolean; true permits explicitly selected stress cases but does not select them | false |
| selection.packs | plan.packs | Required list of named fixture groups; combine groups and remove duplicates | [core] |
| selection.fixtures | plan.fixtures | Required list of fixture IDs; empty selects all fixtures in the chosen packs; nonempty narrows that selection | [] |
| selection.locales | plan.locales | Required list of locale codes; empty uses all declared language variants; unknown or incompatible selections fail | [] |
| selection.client_profile | plan.client | Required field; null uses each fixture default; a profile ID overrides it only when compatible | null |
| selection.provider_profile | plan.provider | Required field; null uses each fixture default; a profile ID overrides it only when compatible | null |
| fixture_parameters | plan.parameters | Required map from selected fixture IDs to settings such as depth mutation_id or encoding; reject unknown fields and unused fixture IDs | {} |
| fixture_parameters.<fixture_id>.depth | plan.depth | Optional nesting depth for the selected depth fixture; root depth 1; normal maximum 16; stress maximum 64 | 6 normal; 32 stress |
| limits.max_message_bytes | plan.messagebytes | Required serialized byte limit per email; users may lower it | 5242880 |
| limits.max_batch_bytes | plan.batchbytes | Required total serialized email byte limit; users may lower it | 268435456 |
| limits.max_depth | plan.maxdepth | Required overall depth ceiling; normal fixtures still limited to 16; users may lower it | 64 |
| limits.max_parts | plan.parts | Required total MIME part limit per email including containers; users may lower it | 1000 |
| limits.max_header_bytes | plan.headers | Required total header byte limit per email including nested headers; users may lower it | 65536 |
| messages | plan.messages | Optional computed file list in saved output plans; derive it from selections and validate it against them if present | absent in editable templates |

### 04 Safety and generation limits

#### Safety and generation limits

| area | id | rule | verification |
| --- | --- | --- | --- |
| Synthetic identities | constraint.identity | All addresses and message IDs use example.test; subdomains also end .test; no real users credentials phone numbers or payment details | Scan decoded headers bodies and assets against approved template values |
| Offline generation | constraint.network | All templates profiles and assets shipped locally; no SMTP IMAP HTTP DNS or filesystem reads outside configured plan and packaged assets | Network-denied integration generation |
| Inert content | constraint.links | HTML limited to passive tags and inline styling; no scripts events forms frames remote styles external images or data URIs; href values only https://example.test/... | Allowlist HTML validation and decoded URL checks |
| Attachments | constraint.assets | Reviewed PNG JPEG PDF TXT CSV only; no executables macros archives decompression bombs EICAR or exploit payloads | Asset inventory SHA-256 sizes media types dimensions and review metadata |
| Normal and stress cases | constraint.validity | Normal fixtures follow email and MIME standards; stress cases require explicit selection and include_stress: true in the plan; mark each file in batch.astrea-manifest.json | Normal emails have no deliberate format errors; stress entries list their planned errors or stress parameters |
| Count and bytes | constraint.resources | Max 10000 messages; max 5242880 serialized bytes per message; max 268435456 serialized bytes per batch | Estimate size before writing and count actual bytes while writing; never complete a partial batch |
| MIME structure | constraint.structure | Normal maximum depth 16; stress maximum depth 64; maximum 1000 MIME parts per email including containers and attached email roots | Count parts and depth without unlimited recursion; check limits while writing |
| Header budgets | constraint.headers | Max total raw headers across entire message 65536 bytes; max raw single header field 16384 bytes; valid lines at most 998 octets | Count header bytes before completing output; stress headers must still fit byte limits |
| Attachment budgets | constraint.attachments | Max 20 attachment leaves per message; max decoded attachment 2097152 bytes; images at most 2048 by 2048 pixels | Count and decoded size accounting; no expanding container formats |
| Depth convention | constraint.depth | Root depth is 1; each child part adds one level including an attached email root; the depth fixture uses one chain of nested containers | Check manifest part paths and depth against a separate part traversal |
| Repeatable files | constraint.reproducibility | Fix seed dates timezone offsets IDs boundaries header order wrapping encodings attachment bytes and file-writing settings | Compare checksums with saved reference files using exact Python dependency generator catalog and template versions |
| Locale integrity | constraint.locale | Use reviewed text for each language; record the language Faker actually uses for each field; do not silently replace a body with another language | Reject missing reviewed templates; manifest records fallback fields |
| Profile accuracy | constraint.profiles | Profiles contain example header sets with recorded versions; no real DKIM or ARC signatures and no promise of delivery | Mark authentication values as synthetic; require reviewed samples before claiming an exact vendor-version match |
| Expected test results | constraint.manifest | Derive expected file bytes and decoded values from fixture rules before generating the email; do not copy expectations from parser output | Compare files and parser results with independent expectations; keep repeated headers as ordered lists |
| Safe output paths | constraint.filesystem | Generated index-and-ID ASCII filenames; prohibit existing destination symlinks traversal and arbitrary attachment extraction | Test unsafe paths; remove only temporary files created by this run |
| Stress expectations | constraint.stress | Content contains no executable code or malware; stress structures may still crash weak parsers; never automatically open generated files | Manifest describes each stress case; run parser tests separately with time and memory limits and no network |
| Parser test results | constraint.parser | A parser may accept a stress email report a format error or reject it because of limits; it must not crash hang or use excessive memory | Check generator output separately from the behavior of the parser being tested |
| Output scope | constraint.scope | Generate a folder of .eml files and supporting JSON only; Maildir mbox mailbox export import and delivery are out of scope | No mailbox-format output options export/import commands account access or network delivery commands |
| Astrea JSON filenames | constraint.filenames | Plans use <name>.astrea-plan.json; manifests use <name>.astrea-manifest.json; future config files use <name>.astrea-<purpose>.<format> with the actual format extension | Check suffix and contents; reject invalid JSON or versions; validation requires exactly one manifest in the batch folder |

### 05 Generation and test rules

#### Generation and test rules

Plan the exact number of files and keep reply threads complete. Use the same seed, settings, and software versions to reproduce a batch. Derive expected test results from the fixture definitions, then compare the generated files and parser results with those expectations.

Write `.eml` files directly in one output folder with `batch.astrea-plan.json` and `batch.astrea-manifest.json`. Mark stress cases in the manifest. Content is passive, but difficult structures can still crash weak parsers. Enforce limits on files, bytes, parts, headers, attachments, and depth; complete the output folder only after all checks pass.

See [the complete generation rules](../design-meta/examples/contracts.md).

## 04 Payload examples

### 01 Generation plan example

#### Generation plan example

```json
{
  "schema_version": 1,
  "catalog_version": "1",
  "generator_version": "0.1.0-example",
  "seed": 42,
  "base_date": "2025-01-15T12:00:00Z",
  "mode": "coverage",
  "count": 1,
  "include_stress": false,
  "limits": {
    "max_message_bytes": 5242880,
    "max_batch_bytes": 268435456,
    "max_depth": 64,
    "max_parts": 1000,
    "max_header_bytes": 65536
  },
  "selection": {
    "packs": [
      "core"
    ],
    "fixtures": [
      "fixture.uk.plain"
    ],
    "locales": [
      "en_GB"
    ],
    "client_profile": null,
    "provider_profile": null
  },
  "fixture_parameters": {}
}
```

### 02 Generated-file manifest example

#### Generated-file manifest example

```json
{
  "schema_version": 1,
  "example_only": true,
  "generator_version": "0.1.0-example",
  "catalog_version": "1",
  "template_revision": "example",
  "seed": 42,
  "count": 1,
  "total_message_bytes": 0,
  "coverage": {
    "minimum_messages": 1,
    "fixture_counts": {
      "fixture.uk.plain": 1
    }
  },
  "assets": [],
  "messages": [
    {
      "index": 1,
      "path": "000001-fixture.uk.plain.eml",
      "fixture_id": "fixture.uk.plain",
      "occurrence": 0,
      "locale": "en_GB",
      "region": "region.uk",
      "script": "Latin",
      "effective_faker_locales": {
        "name": "en_GB"
      },
      "profiles": {
        "client": {
          "id": "client.thunderbird.v1",
          "revision": "1"
        },
        "provider": {
          "id": "provider.generic.v1",
          "revision": "1"
        }
      },
      "validity": "valid",
      "size_bytes": 0,
      "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
      "expectations": {
        "headers": {
          "ordered_names": [
            "Return-Path",
            "Received",
            "Received",
            "From",
            "To",
            "Date",
            "Message-ID",
            "Subject",
            "User-Agent",
            "Content-Language",
            "MIME-Version",
            "Content-Type",
            "Content-Transfer-Encoding"
          ],
          "absent": [
            "Bcc",
            "X-Mailer"
          ],
          "decoded_values": {
            "From": "Morgan Ellis <morgan@example.test>",
            "To": "Alex Lane <alex@example.test>",
            "Subject": "Meeting on Friday",
            "Message-ID": "<astrea-example-1@example.test>"
          },
          "counts": {
            "Received": 2,
            "Subject": 1
          }
        },
        "body_facts": [
          "Friday",
          "10:00"
        ],
        "mime": {
          "depth": 1,
          "node_count": 1,
          "nodes": [
            {
              "path": "1",
              "depth": 1,
              "media_type": "text/plain",
              "charset": "utf-8",
              "disposition": null,
              "content_id": null,
              "transfer_encoding": "7bit",
              "decoded_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
            }
          ]
        },
        "attachments": [],
        "thread": null,
        "stress": null
      },
      "seed_key": "fixture.uk.plain/en_GB/0/0"
    }
  ],
  "software_versions": {
    "python": "PIN_EXACT_PATCH",
    "uv_lock_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    "faker": "PIN_EXACT_VERSION"
  }
}
```

