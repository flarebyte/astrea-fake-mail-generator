package flyb

source: "astrea-design-meta"
name: "astrea-design-meta"
modules: ["core"]

reports: [{
 title: "Astrea fake email generator specification"
 filepath: "../design/specification.md"
 description: "Python CLI specification for reproducible inert email batches and bounded parser stress fixtures."
 sections: [
{ title: "01 Product and delivery", sections: [
{ title: "01 Intent and scope", notes: ["astrea.overview"] },
{ title: "02 CLI features", notes: ["astrea.features"] },
{ title: "03 Regional delivery order", notes: ["astrea.regions"] }
] },
{ title: "02 Fixture coverage", sections: [
{ title: "01 Fixture and use-case catalog", notes: ["astrea.fixtures"] },
{ title: "02 Client and provider profiles", notes: ["astrea.profiles"] }
] },
{ title: "03 Implementation contracts", sections: [
{ title: "01 Technology choices", notes: ["astrea.tech"] },
{ title: "02 CLI command contract", notes: ["astrea.cli"] },
{ title: "03 Safety and determinism constraints", notes: ["astrea.constraints"] },
{ title: "04 Generation and assertion contracts", notes: ["astrea.contracts"] }
] },
{ title: "04 Payload examples", sections: [
{ title: "01 Resolved plan example", notes: ["astrea.plan"] },
{ title: "02 Assertion manifest example", notes: ["astrea.manifest"] }
] }
]
}]

notes: [
{
	name: "astrea.overview",
	title: "Intent and scope",
	markdown: """
Astrea is a proposed Python CLI for reproducible batches of inert `.eml` messages. Use `uv run --locked astrea` with seeded plans and machine-readable assertion manifests.

The MVP prioritizes UK and US English, European Latin-script content, synthetic Gmail/Outlook/Thunderbird header profiles, plain text, HTML, safe attachments, nested MIME, and opt-in bounded parser stress cases. Later phases expand regional and non-Latin-script coverage.

See [intent, source conventions, and standards references](../design-meta/examples/overview.md). The CLI is specified here and has not been implemented.
""",
	labels: ["design", "md"]
},
{
	name: "astrea.tech",
	title: "Technology choices",
	filepath: "examples/tech.csv",
	arguments: ["format-csv=table"],
	labels: ["design", "csv"]
},
{
	name: "astrea.features",
	title: "CLI features",
	filepath: "examples/features.csv",
	arguments: ["format-csv=table"],
	labels: ["design", "csv"]
},
{
	name: "astrea.fixtures",
	title: "Fixture and use-case catalog",
	filepath: "examples/fixtures.csv",
	arguments: ["format-csv=table"],
	labels: ["design", "csv"]
},
{
	name: "astrea.regions",
	title: "Regional delivery order",
	filepath: "examples/regions.csv",
	arguments: ["format-csv=table"],
	labels: ["design", "csv"]
},
{
	name: "astrea.profiles",
	title: "Client and provider profiles",
	filepath: "examples/profiles.csv",
	arguments: ["format-csv=table"],
	labels: ["design", "csv"]
},
{
	name: "astrea.cli",
	title: "CLI command contract",
	filepath: "examples/cli.csv",
	arguments: ["format-csv=table"],
	labels: ["design", "csv"]
},
{
	name: "astrea.constraints",
	title: "Safety and determinism constraints",
	filepath: "examples/constraints.csv",
	arguments: ["format-csv=table"],
	labels: ["design", "csv"]
},
{
	name: "astrea.contracts",
	title: "Generation and assertion contracts",
	markdown: """
Plan exact message counts and complete thread groups before writing. Pin the toolchain, catalog, profiles, templates, and assets; derive independent component seeds and stable byte serialization. Record raw and semantic expectations independently of parser results.

Keep ordinary output in `valid/` and explicitly selected parser stress cases in `stress/`. Stress content remains inert while structures may crash vulnerable parsers. Enforce byte, node, header, attachment, and depth limits and publish only a completely validated new directory.

See [the complete packaging, planning, serialization, mutation, manifest, and acceptance contracts](../design-meta/examples/contracts.md).
""",
	labels: ["design", "md"]
},
{
	name: "astrea.plan",
	title: "Resolved plan example",
	filepath: "examples/plan.example.json",
	labels: ["design", "json"]
},
{
	name: "astrea.manifest",
	title: "Assertion manifest example",
	filepath: "examples/manifest.example.json",
	labels: ["design", "json"]
}
]

relationships: []

argumentRegistry: {
	version: "1"
	arguments: [{
		name: "format-csv"
		valueType: "enum"
		scopes: ["note"]
		allowedValues: ["table", "raw"]
		defaultValue: "table"
	}]
}
