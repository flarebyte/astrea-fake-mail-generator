# astrea-fake-mail-generator
Generate fake `.eml` email files for tests.

The Python CLI is currently specified in [doc/design-meta/examples](doc/design-meta/examples/overview.md). Start with the [generated specification](doc/design/specification.md) for fixture coverage, CLI commands, expected test results, and optional parser stress cases with fixed limits.

Output is an ordinary folder of `.eml` files plus a saved generation plan and a JSON index of expected test results. Maildir, mbox, mailbox import/export, and sending email are out of scope. See the [glossary](doc/design-meta/examples/glossary.csv) for definitions.

Regenerate the design documentation with:

```sh
flyb validate --config doc/design-meta
flyb generate markdown --config doc/design-meta
```

The proposed runtime command is `uv run --locked astrea`; implementation is not included yet.
