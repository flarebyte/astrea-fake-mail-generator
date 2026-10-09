# astrea-fake-mail-generator
Fake email generator for providing testing fixtures

The Python CLI is currently specified in [doc/design-meta/examples](doc/design-meta/examples/overview.md). Start with the [generated specification](doc/design/specification.md) for fixture coverage, CLI commands, deterministic assertions, and bounded parser stress cases.

Regenerate the design documentation with:

```sh
flyb validate --config doc/design-meta
flyb generate markdown --config doc/design-meta
```

The proposed runtime command is `uv run --locked astrea`; implementation is not included yet.
