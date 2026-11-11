.DEFAULT_GOAL := help

.PHONY: help doc-design check-tools install-tools-help thoth-meta thoth-python thoth-python-test

# gh flarebyte owns Python scripts, tests, formatting, lint, coverage, and builds.
help: ## List the workflows provided by this Makefile.
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

doc-design: ## Validate specifications and regenerate design Markdown.
	sh scripts/generate-design.sh

check-tools: ## Check tools required for documentation generation.
	@sh scripts/check-doc-tools.sh

install-tools-help: ## Show installation guidance for documentation tools.
	@printf '%s\n' \
	  'Python 3: https://www.python.org/downloads/' \
	  'GitHub CLI: https://cli.github.com/' \
	  'gh flarebyte: gh extension install flarebyte/gh-flarebyte' \
	  'flyb: https://github.com/flarebyte/baldrick-flying-buttress'

thoth-meta: thoth-python thoth-python-test ## Refresh all Python code metadata.

thoth-python: ## Refresh Python source metadata.
	thoth run --config pipeline-python-maat.thoth.cue

thoth-python-test: ## Refresh Python test metadata.
	thoth run --config pipeline-python-test-maat.thoth.cue
