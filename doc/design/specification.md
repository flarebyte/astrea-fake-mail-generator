# Astrea fake email generator specification

Python CLI specification for reproducible inert email batches and bounded parser stress fixtures.

## 01 Product and delivery

### 01 Intent and scope

#### Intent and scope

Astrea is a proposed Python CLI for reproducible batches of inert `.eml` messages. Use `uv run --locked astrea` with seeded plans and machine-readable assertion manifests.

The MVP establishes representative multilingual coverage with UK and US English, several European Latin-script languages, Japanese, and Arabic RTL. It also covers synthetic Gmail/Outlook/Thunderbird header profiles, plain text, HTML, safe attachments, nested MIME, and opt-in bounded parser stress cases. Later releases broaden regional and language coverage as reviewed templates become available.

See [intent, source conventions, and standards references](../design-meta/examples/overview.md). The CLI is specified here and has not been implemented.

### 02 CLI features

#### CLI features

| acceptance | contract | feature | id | phase | priority |
| --- | --- | --- | --- | --- | --- |
| Count of manifest entries equals count of .eml files | Generate exact requested count into new directory; default 100 | Batch .eml generation | feature.batch | MVP | must |
| Same canonical plan and pinned toolchain yield identical .eml bytes and manifest | Seed defaults to 0; derive separate per-message per-component SHA-256 namespaces | Deterministic seeds | feature.seed | MVP | must |
| Saving and replaying plan reproduces checksums | Versioned JSON plan with exact fixture allocations and resolved profiles | Replayable batch plan | feature.plan | MVP | must |
| Reject count below minimum; manifest summary gives exact per-fixture counts | One instance of every selected fixture before cycling sorted IDs | Coverage mode | feature.coverage | MVP | must |
| Exact count and allocations independent of iteration order | Integer weights with largest-remainder allocation and stable ID ties | Weighted allocation | feature.weighted | Phase 2 | should |
| Core pack includes en_GB en_US fr_FR de_DE es_ES it_IT ja_JP ar_EG; assert script encoding and text direction; later packs broaden coverage | Build representative multilingual coverage from the MVP across Latin scripts Japanese and Arabic RTL; expand locale breadth in subsequent releases | Regional and script coverage | feature.locale | MVP | must |
| Each manifest lists both IDs revisions and ordered expected headers | Separate versioned client profile and provider profile with compatibility registry | Client and provider profiles | feature.profiles | MVP | must |
| Assert header multiplicity ordering encoding and controlled values; Bcc absent from wire by default | From To Cc Reply-To Date Message-ID Subject MIME-Version plus optional trace list and threading headers | Rich predictable headers | feature.headers | MVP | must |
| Decoded body and charset match manifest | ASCII UTF-8 LF-to-CRLF normalization and explicit transfer encoding | Plain text | feature.text | MVP | must |
| No scripts forms remote assets tracking or active URLs | HTML-only and multipart/alternative plain then HTML with escaped synthetic values | HTML and alternatives | feature.html | MVP | must |
| Decoded attachment hashes match packaged assets | PNG JPEG PDF TXT CSV with predictable names sizes media types and SHA-256 | Safe attachments | feature.attachments | MVP | must |
| Every cid reference resolves exactly once within related subtree | multipart/related with HTML referencing deterministic Content-ID | CID inline images | feature.inline | MVP | must |
| Manifest preorder part paths types and tree depth equal serialized tree | Support simple trees and explicit depth parameter with fixed node budget | Linear and nested MIME | feature.nesting | MVP | must |
| Every referenced generated ID exists and timestamps follow thread order | Deterministic Message-ID In-Reply-To References and message/rfc822 attachments | Threads and forwarded email | feature.threading | MVP | must |
| Decoded values correct; raw encodings explicitly asserted | 7bit quoted-printable base64; RFC 2047 subjects and RFC 2231 filenames | Encoding variety | feature.encoding | MVP | must |
| Reject unsupported charset/text combinations; no silent transliteration | ISO-8859-1 Windows-1252 ISO-2022-JP GB18030 where representable; UTF-8 international headers separate profile | Legacy and international encoding | feature.legacy | Phase 2 | should |
| Manifest provides positive presence and negative absence assertions without relying solely on parser output | Versioned manifest.json containing raw hashes semantic expectations and structural paths | Assertion manifest | feature.manifest | MVP | must |
| Each mutation has stable ID exact offsets expected defects and recommended parser outcome | Explicit --include-stress plus stress fixture selection; deterministic bounded raw-byte mutations | Parser stress fixtures | feature.stress | MVP | must |
| Over-budget request fails before publishing destination | Enforce count byte node depth header and attachment caps before and during streaming writes | Resource limits | feature.limits | MVP | must |
| Generation succeeds with network denied and assets packaged locally | No sending DNS network reads remote resources shell execution or real inbox samples | Offline and inert output | feature.offline | MVP | must |
| Client can import mailbox; stress files remain separate | Export valid corpus as Maildir with exact bytes and deterministic flags | Mailbox directory export | feature.maildir | Phase 2 | should |
| Detect tampering; stress validation checks planned anomalies without recursive unbounded parsing | Verify manifest hashes safe assets required headers plan coverage and normal MIME invariants | Corpus validation | feature.validate | MVP | must |
| Usage/config 2; IO/validation 1; success 0 | Stable error codes JSON diagnostics option and exit status | Machine-readable diagnostics | feature.errors | MVP | must |
| JSON catalog and plan stable for same inputs | List profiles fixtures locales and limits; plan without writing .eml | Catalog and preview | feature.inspect | MVP | must |
| Document transformations and preserve original .eml hashes | Optional importer-friendly adapter with explicit From-line escaping | mbox export | feature.mbox | Later | could |

### 03 Regional coverage roadmap

#### Regional coverage roadmap

| assertions | content_focus | delivery_stage | id | locales | phase | region | scripts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Locale recorded; deterministic offset from fixed dates; £ encoded correctly | GBP receipts DD/MM/YYYY prose British spelling fixed Europe/London winter offset; DST expansion later | 1 | region.uk | en_GB | MVP | United Kingdom | Latin |
| No OS locale reliance; date prose and wire Date checked separately | USD receipts MM/DD/YYYY prose US spelling America/New_York | 1 | region.us | en_US | MVP | United States | Latin |
| NFC accents preserved in subjects bodies display names and filenames | EUR receipts accents umlauts apostrophes and localized business prose | 1 | region.europe.latin | fr_FR;de_DE;es_ES;it_IT | MVP | Europe Latin scripts | Latin |
| Reviewed Japanese body; encoded subject and display name preserve Japanese characters | UTF-8 Japanese notifications mixed-script display names and subjects | 1 | region.asia.japan | ja_JP | MVP | Japan | Japanese |
| HTML dir=rtl; bidi code points recorded; RFC 2047 subject and RFC 2231 filename; output paths remain ASCII | RTL appointment reminder mixed-script text and Unicode attachment filename | 1 | region.rtl.arabic | ar_EG | MVP | Arabic-language baseline (Egypt locale) | Arabic |
| Script and normalization cases recorded; reviewed localized templates required | Broader diacritics Greek and Cyrillic coverage | 2 | region.europe.expanded | pt_PT;nl_NL;pl_PL;sv_SE;el_GR;uk_UA | Phase 2 | Europe broader coverage | Latin;Greek;Cyrillic |
| Geography independent of script; template locale and effective Faker locale both recorded | INR SGD IDR VND dates Vietnamese combining-mark edge cases | 2 | region.asia.latin | en_IN;en_SG;id_ID;vi_VN | Phase 2 | Asia Latin and English baseline | Latin |
| UTF-8 first; reviewed translations and fonts not assumed on recipient client | CJK wide characters mixed-script names local currency and no-space wrapping | 2 | region.asia.nonlatin | ja_JP;zh_CN;zh_TW;ko_KR;hi_IN;th_TH | Phase 2 | Asia additional scripts | Japanese;Han;Hangul;Devanagari;Thai |
| No real street addresses payment details or reachable contacts | BRL MXN AUD ZAR local business fixtures | 3 | region.world.latin | pt_BR;es_MX;en_AU;en_ZA | Phase 3 | Rest of world Latin and English | Latin |
| Explicit dir attributes and bidi code points in manifest; filenames remain generated ASCII | RTL body mixed-direction subjects and filenames | 3 | region.world.rtl | ar_EG;he_IL | Phase 3 | Middle East and additional RTL coverage | Arabic;Hebrew |
| Unsupported locale rejected; provider fallback disclosed and never relabeled as translated content | Add locales only with reviewed content and fixture assertions | 4 | region.world.expanded | reviewed-locale-registry | Later | Additional regions | Multiple |

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
| Default depth 6; requested normal depth 2..16; exact preorder paths and node count | client.generic.v1 | feature.nesting | fixture.uk.nested | en_GB | mixed chain with final alternative(plain;html) | core | MVP | provider.generic.v1 | Nested MIME parser traversal | valid |
| Multiple To and Cc mailboxes; Reply-To; Bcc in envelope manifest only; folded header | client.generic.v1 | feature.headers | fixture.us.recipients | en_US | text/plain | core | MVP | provider.generic.v1 | Team announcement with recipient variants | valid |
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

| assertions | fidelity | id | illustrative_headers | kind | phase | valid_pairings |
| --- | --- | --- | --- | --- | --- | --- |
| Common RFC headers always present | Standards baseline | client.generic.v1 | No client-specific X headers | client | MVP | provider.generic.v1;provider.gmail.v1;provider.outlook.v1 |
| Assert absence of X-Mailer; stable MIME template | Synthetic webmail approximation; not a claim Gmail always emits this layout | client.gmail-web.v1 | No X-Mailer; MIME multipart alternative template | client | MVP | provider.gmail.v1 |
| Versioned placeholder X-Mailer and deterministic synthetic threading fields | Illustrative subset; verify against sanitized samples before claiming version fidelity | client.outlook-desktop.v1 | X-Mailer;Thread-Index;Thread-Topic | client | MVP | provider.outlook.v1;provider.generic.v1 |
| Synthetic User-Agent version and locale-derived Content-Language | Illustrative desktop subset; not a full header fingerprint | client.thunderbird.v1 | User-Agent;Content-Language | client | MVP | provider.generic.v1;provider.gmail.v1;provider.outlook.v1 |
| Versioned synthetic value and raw header casing | Illustrative subset | client.apple-mail.v1 | X-Mailer;Mime-Version | client | Phase 2 | provider.generic.v1 |
| Two fixed trace hops using reserved IPs and .test domains | Synthetic delivery trace | provider.generic.v1 | Return-Path;Received | provider | MVP | client.generic.v1;client.outlook-desktop.v1;client.thunderbird.v1;client.apple-mail.v1 |
| Placeholder values and example.test authentication identity | Synthetic provider-style shape; no real signatures or authentication claims | provider.gmail.v1 | Received;X-Received;Authentication-Results;X-Google-Smtp-Source | provider | MVP | client.gmail-web.v1;client.generic.v1;client.thunderbird.v1 |
| Stable synthetic internal/external and SCL cases labeled in manifest | Synthetic provider-style shape; verify exact values against sanitized samples | provider.outlook.v1 | Received;Authentication-Results;X-MS-Exchange-Organization-AuthAs;X-MS-Exchange-Organization-SCL | provider | MVP | client.outlook-desktop.v1;client.generic.v1;client.thunderbird.v1 |
| Opaque seeded placeholder value | Illustrative subset | provider.yahoo.v1 | Received;X-YMail-OSG | provider | Phase 2 | client.generic.v1 |
| Reserved-domain identity and trace ordering | Illustrative subset | provider.fastmail.v1 | Received;Authentication-Results | provider | Phase 2 | client.generic.v1;client.thunderbird.v1 |
| Reject uncontrolled raw headers outside stress mutation layer | No fetched or unreviewed provider dumps | provider.custom.v1 | Reviewed versioned local profile | provider | Later | compatibility-registry |

## 03 Implementation contracts

### 01 Technology choices

#### Technology choices

| constraint | decision | id | phase | rationale | reference | role | technology |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pin exact Python patch for byte-identical golden fixtures | selected | tech.python | MVP | Typed Python package with console entry point astrea | https://docs.python.org/3/ | Runtime | Python 3.12+ |
| Dependency setup may use network; fixture generation must be offline | selected | tech.uv | MVP | Use pyproject.toml and uv.lock; uv run --locked astrea | https://docs.astral.sh/uv/concepts/projects/run/ | Environment and invocation | uv |
| Validate all choices and bounds before writes | selected | tech.argparse | MVP | Subcommands and stable help without a CLI framework dependency | https://docs.python.org/3/library/argparse.html | CLI parsing | argparse (stdlib) |
| Fix CRLF folding header order encodings and boundaries; raw mutation layer for malformed cases | selected | tech.email | MVP | EmailMessage and BytesGenerator with explicit policy | https://docs.python.org/3/library/email.html | MIME construction and serialization | email (stdlib) |
| Pin version; never use uncontrolled email/url/phone/address providers; record provider fallback | selected | tech.faker | MVP | Seeded locale providers supplement curated body templates | https://faker.readthedocs.io/en/stable/ | Localized synthetic names and organizations | Faker |
| Faker lorem is not a substitute for natural localized sentences; no external template execution | selected | tech.templates | MVP | Small reviewed templates for receipts newsletters conversations and notifications | https://docs.python.org/3/library/html.html | Realistic body content | Curated UTF-8 templates plus html.escape (stdlib) |
| No remote downloads; PDFs have no JavaScript actions links forms or embedded files; images have bounded dimensions | selected | tech.assets | MVP | Reviewed inert assets reused byte-for-byte with checksums | project-owned-assets | Attachments | Packaged PNG JPEG PDF TXT CSV assets |
| Reject unknown fields; UTF-8 output; canonical serialization | selected | tech.json | MVP | Versioned JSON schema and typed internal domain model | https://docs.python.org/3/library/json.html | Batch plans and manifest | json and dataclasses (stdlib) |
| Never use process-dependent hash() or global random state | selected | tech.hashlib | MVP | SHA-256 of canonical input and fixture namespace | https://docs.python.org/3/library/hashlib.html | Identity seeds and checksums | hashlib (stdlib) |
| Reject existing destinations symlinks and path traversal; clean only own staging files | selected | tech.pathlib | MVP | Staging directory and atomic rename on same filesystem | https://docs.python.org/3/library/pathlib.html | Safe output publication | pathlib and tempfile (stdlib) |
| Deterministic names and flags; no IMAP or SMTP delivery | selected | tech.maildir | Phase 2 | Maildir export from valid .eml bytes | https://docs.python.org/3/library/mailbox.html | Optional mailbox packaging | mailbox (stdlib) |
| Test dependencies pinned in uv.lock; independently inspect raw output | selected-dev | tech.pytest | MVP | CLI error tests golden bytes manifest consistency and safety checks | https://docs.pytest.org/en/stable/ | Regression and integration checks | pytest |
| Hard bounds and replayable examples; no unbounded fuzzing | candidate-dev | tech.hypothesis | Phase 2 | Exercise MIME trees and selector combinations | https://hypothesis.readthedocs.io/en/latest/ | Bounded combinatorial tests | Hypothesis |
| Pin dev dependency | selected-dev | tech.ruff | MVP | Consistent Python style and static checks | https://docs.astral.sh/ruff/ | Lint and format | Ruff |
| Not a runtime dependency | selected-design | tech.flyb | MVP | Assemble CSV and prose into doc/design | https://github.com/flarebyte/baldrick-flying-buttress | Design documentation generation | flyb |

### 02 CLI command contract

#### CLI command contract

| command_or_option | contract | default | example | id | phase |
| --- | --- | --- | --- | --- | --- |
| generate | Publish new output directory with valid/ stress/ manifest.json plan.json and assets.json | core pack; 100 messages; seed 0 | uv run --locked astrea generate --out ./fixtures --count 100 --seed 42 | cli.generate | MVP |
| --pack | Repeatable additive packs; stable resolved fixture order; stress requires separate gate | core | --pack core | cli.pack | MVP |
| --fixture | Repeatable IDs narrow pack selection; incompatible filters fail instead of dropping cases | all fixtures in selected packs | --fixture fixture.uk.plain | cli.fixture | MVP |
| --count | Positive integer counts wire messages including thread members; max 10000 | 100 | --count 24 | cli.count | MVP |
| --locale | Repeatable locales expand declared variants only; unknown or incompatible selection fails | catalog-defined fixture locale | --locale en_GB | cli.locale | MVP |
| --client-profile | Override only when compatible with selected provider and required fixture features | fixture default | --client-profile client.thunderbird.v1 | cli.client | MVP |
| --provider-profile | Validate both profile pairing and fixture header constraints | fixture default | --provider-profile provider.generic.v1 | cli.provider | MVP |
| --seed | Unsigned 64-bit integer; per-component deterministic derivation | 0 | --seed 42 | cli.seed | MVP |
| --base-date | RFC 3339 UTC instant; deterministic per-index time increments and thread order | 2025-01-15T12:00:00Z | --base-date 2025-01-15T12:00:00Z | cli.date | MVP |
| --mode | Coverage mode ensures selected cases; weighted added Phase 2 | coverage | --mode coverage | cli.mode | MVP |
| --depth | Root MIME node depth 1; valid range depends on fixture; maximum 64 | 6 for nested normal; 32 for stress depth | --depth 8 | cli.depth | MVP |
| --include-stress | Required for --pack stress or any stress fixture; gate alone never selects stress | false | --pack stress --include-stress | cli.stress | MVP |
| plan | Emit resolved plan JSON to stdout; dry run with no output writes | same options as generate | uv run --locked astrea plan --count 24 --seed 42 | cli.plan | MVP |
| generate --plan | Read strict schema-versioned resolved JSON plan; only --out and --json-diagnostics may accompany | none | uv run --locked astrea generate --plan batch-plan.json --out ./fixtures | cli.planfile | MVP |
| list fixtures/profiles/locales/packs | Catalog includes IDs phase revisions compatibility and minimum message counts; --json supported | text | uv run --locked astrea list fixtures --json | cli.list | MVP |
| validate --input | Check corpus consistency safety and declared assertions using bounded inspection | none | uv run --locked astrea validate --input ./fixtures --json-diagnostics | cli.validate | MVP |
| --max-message-bytes/--max-batch-bytes/--max-parts/--max-header-bytes | Optional lower limits only; increasing hard caps rejected | hard caps | --max-message-bytes 1048576 | cli.limits | MVP |
| --json-diagnostics | Structured error code field context and actionable message on stderr; stdout remains machine-readable | false | --json-diagnostics | cli.diagnostics | MVP |
| export --format maildir --input --out | New Maildir containing valid corpus; reject stress inclusion; no network import | valid messages only | uv run --locked astrea export --format maildir --input ./fixtures --out ./mailbox | cli.export | Phase 2 |
| --version | Print generator catalog and manifest schema versions | none | uv run --locked astrea --version | cli.version | MVP |

### 03 Safety and determinism constraints

#### Safety and determinism constraints

| area | id | rule | verification |
| --- | --- | --- | --- |
| Synthetic identities | constraint.identity | All addresses and message IDs use example.test; subdomains also end .test; no real users credentials phone numbers or payment details | Scan decoded headers bodies and assets against controlled source values |
| Offline generation | constraint.network | All templates profiles and assets shipped locally; no SMTP IMAP HTTP DNS or filesystem reads outside configured plan and packaged assets | Network-denied integration generation |
| Inert content | constraint.links | HTML limited to passive tags and inline styling; no scripts events forms frames remote styles external images or data URIs; href values only https://example.test/... | Allowlist HTML validation and decoded URL checks |
| Attachments | constraint.assets | Reviewed PNG JPEG PDF TXT CSV only; no executables macros archives decompression bombs EICAR or exploit payloads | Asset inventory SHA-256 sizes media types dimensions and review metadata |
| Normal and stress separation | constraint.validity | Core output RFC 5322/MIME-compatible; malformed and structurally adversarial cases only selected explicitly and stored in stress/ | Normal corpus has no planned parse defects; stress IDs and defects manifest-marked |
| Count and bytes | constraint.resources | Max 10000 messages; max 5242880 serialized bytes per message; max 268435456 serialized bytes per batch | Plan conservative estimate and streaming byte accounting; never publish partial destination |
| MIME structure | constraint.structure | Normal max depth 16; stress max depth 64; max 1000 total MIME nodes per message including embedded message roots | Iterative tree traversal and bounded serialization |
| Header budgets | constraint.headers | Max total raw headers across entire message 65536 bytes; max raw single header field 16384 bytes; valid lines at most 998 octets | Byte-level accounting before publish; oversized stress line remains inside byte caps |
| Attachment budgets | constraint.attachments | Max 20 attachment leaves per message; max decoded attachment 2097152 bytes; images at most 2048 by 2048 pixels | Count and decoded size accounting; no expanding container formats |
| Depth convention | constraint.depth | Root depth 1; every contained MIME entity increases depth including message/rfc822 embedded root; depth fixture uses linear chain | Manifest tree depth and node paths checked by independent bounded traversal |
| Deterministic bytes | constraint.reproducibility | Fix seed dates timezone offsets IDs boundaries header order folding transfer encodings asset bytes and serialization policy | Golden hashes on pinned Python patch dependencies generator revision catalog and templates |
| Locale integrity | constraint.locale | Use curated localized prose; explicit effective Faker locale per field; no environment locale or silent body fallback | Reject missing reviewed templates; manifest records fallback fields |
| Profile fidelity | constraint.profiles | Profiles describe synthetic header shapes with pinned revision; no real DKIM ARC signatures or claims of deliverability | Authentication placeholders marked synthetic; sanitized evidence required before exact-version fidelity |
| Independent expectations | constraint.manifest | Planner establishes semantic and raw assertions before serialization; parser output never supplies sole expected result | Compare bytes and bounded parser output to plan assertions; preserve duplicate headers as arrays |
| Safe output paths | constraint.filesystem | Generated index-and-ID ASCII filenames; prohibit existing destination symlinks traversal and arbitrary attachment extraction | Negative path checks; only own staging files cleaned on failure |
| Stress expectations | constraint.stress | Safe refers to inert content; intentionally stressful structure can exhaust or crash weak parsers; never open with a desktop client automatically | Manifest recommends isolated parser subprocess with timeout memory cap and no network |
| Downstream parser outcome | constraint.parser | Stress acceptance is bounded success rejection or documented defect; never promise every parser crashes or emits identical defect names | Separate generator assertions from suggested parser resource/defect expectations |
| Product boundary | constraint.scope | Create local fixtures and packaging; no mail sending account login inbox scraping live provider API or existing-mail anonymization | CLI catalog has no network delivery commands |

### 04 Generation and assertion contracts

#### Generation and assertion contracts

Plan exact message counts and complete thread groups before writing. Pin the toolchain, catalog, profiles, templates, and assets; derive independent component seeds and stable byte serialization. Record raw and semantic expectations independently of parser results.

Keep ordinary output in `valid/` and explicitly selected parser stress cases in `stress/`. Stress content remains inert while structures may crash vulnerable parsers. Enforce byte, node, header, attachment, and depth limits and publish only a completely validated new directory.

See [the complete packaging, planning, serialization, mutation, manifest, and acceptance contracts](../design-meta/examples/contracts.md).

## 04 Payload examples

### 01 Resolved plan example

#### Resolved plan example

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
    "max_depth": 16,
    "max_parts": 1000,
    "max_header_bytes": 65536
  },
  "messages": [
    {
      "index": 1,
      "fixture_id": "fixture.uk.plain",
      "occurrence": 0,
      "thread_member_index": 0,
      "locale": "en_GB",
      "client_profile": "client.thunderbird.v1",
      "provider_profile": "provider.generic.v1",
      "validity": "valid",
      "parameters": {}
    }
  ]
}
```

### 02 Assertion manifest example

#### Assertion manifest example

```json
{
  "schema_version": 1,
  "example_only": true,
  "generator_version": "0.1.0-example",
  "catalog_version": "1",
  "template_revision": "example",
  "toolchain": {
    "python": "PIN_EXACT_PATCH",
    "uv_lock_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    "faker": "PIN_EXACT_VERSION"
  },
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
      "path": "valid/000001-fixture.uk.plain.eml",
      "fixture_id": "fixture.uk.plain",
      "occurrence": 0,
      "seed_namespace": "fixture.uk.plain/en_GB/0/0",
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
          "multiplicity": {
            "Received": 2,
            "Subject": 1
          },
          "absent": [
            "Bcc",
            "X-Mailer"
          ],
          "decoded_values": {
            "From": "Morgan Ellis <morgan@example.test>",
            "To": "Alex Lane <alex@example.test>",
            "Subject": "Meeting on Friday",
            "Message-ID": "<astrea-example-1@example.test>"
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
      }
    }
  ]
}
```

