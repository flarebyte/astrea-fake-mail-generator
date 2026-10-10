package flyb

source: "astrea-design-meta"
name: "astrea-design-meta"
modules: ["core"]

reports: [{
 title: "Astrea fake email generator specification"
 filepath: "../design/specification.md"
 description: "Python CLI that generates repeatable folders of safe .eml test files, including optional parser stress cases."
 sections: [
{ title: "01 Product and delivery", sections: [
{ title: "01 Intent and scope", notes: ["astrea.overview"] },
{ title: "02 Glossary", notes: ["astrea.glossary"] },
{ title: "03 CLI features", notes: ["astrea.features"] },
{ title: "04 Regional coverage roadmap", notes: ["astrea.regions"] }
] },
{ title: "02 Fixture coverage", sections: [
{ title: "01 Fixture and use-case catalog", notes: ["astrea.fixtures"] },
{ title: "02 Client and provider profiles", notes: ["astrea.profiles"] }
] },
{ title: "03 Implementation rules", sections: [
{ title: "01 Technology choices", notes: ["astrea.tech"] },
{ title: "02 CLI commands", notes: ["astrea.cli"] },
{ title: "03 Safety and generation limits", notes: ["astrea.constraints"] },
{ title: "04 Generation and test rules", notes: ["astrea.contracts"] }
] },
{ title: "04 Payload examples", sections: [
{ title: "01 Generation plan example", notes: ["astrea.plan"] },
{ title: "02 Generated-file manifest example", notes: ["astrea.manifest"] }
] }
]
}]

notes: [
{
	name: "astrea.overview",
	title: "Intent and scope",
	markdown: """
Astrea is a proposed Python CLI that generates a folder of fake `.eml` email files for tests. Use `uv run --locked astrea`. Mailbox formats, import/export, and sending email are out of scope.

A fixture defines a test case. `batch.astrea-plan.json` records what to generate. `batch.astrea-manifest.json` lists the generated files and their expected headers, text, parts, and attachments so tests can check them.

The MVP establishes representative multilingual coverage with UK and US English, several European Latin-script languages, Japanese, and Arabic RTL. It also covers synthetic Gmail/Outlook/Thunderbird header profiles, plain text, HTML, safe attachments, nested MIME, and opt-in bounded parser stress cases. Later releases broaden regional and language coverage as reviewed templates become available.

See [intent, source conventions, and standards references](../design-meta/examples/overview.md). The CLI is specified here and has not been implemented.
""",
	labels: ["design", "md"]
},
{
 name: "astrea.glossary",
 title: "Glossary",
 filepath: "examples/glossary.csv",
 arguments: ["format-csv=table"],
 labels: ["design", "csv"]
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
	title: "Regional coverage roadmap",
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
	title: "CLI commands",
	filepath: "examples/cli.csv",
	arguments: ["format-csv=table"],
	labels: ["design", "csv"]
},
{
	name: "astrea.constraints",
	title: "Safety and generation limits",
	filepath: "examples/constraints.csv",
	arguments: ["format-csv=table"],
	labels: ["design", "csv"]
},
{
	name: "astrea.contracts",
	title: "Generation and test rules",
	markdown: """
Plan the exact number of files and keep reply threads complete. Use the same seed, settings, and software versions to reproduce a batch. Derive expected test results from the fixture definitions, then compare the generated files and parser results with those expectations.

Write `.eml` files directly in one output folder with `batch.astrea-plan.json` and `batch.astrea-manifest.json`. Mark stress cases in the manifest. Content is passive, but difficult structures can still crash weak parsers. Enforce limits on files, bytes, parts, headers, attachments, and depth; complete the output folder only after all checks pass.

See [the complete generation rules](../design-meta/examples/contracts.md).
""",
	labels: ["design", "md"]
},
{
	name: "astrea.plan",
	title: "Generation plan example",
	filepath: "examples/example.astrea-plan.json",
	labels: ["design", "json"]
},
{
	name: "astrea.manifest",
	title: "Generated-file manifest example",
	filepath: "examples/example.astrea-manifest.json",
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
