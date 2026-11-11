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

# Use gh arrow global mappings to follow the reserve working tree.
RESERVE_PYTHON := github:flarebyte:baldrick-reserve:shared/python/all/pipeline-python-maat.thoth.cue
RESERVE_PYTHON_TEST := github:flarebyte:baldrick-reserve:shared/python/all/pipeline-python-test-maat.thoth.cue

.PHONY: reserve-check reserve-sync reserve-check-python reserve-check-python-test reserve-sync-python reserve-sync-python-test

reserve-check: reserve-check-python reserve-check-python-test ## Check drift against globally mapped reserve.
reserve-sync: reserve-sync-python reserve-sync-python-test ## Replace listed configs from globally mapped reserve.

# Managed mapping: $(RESERVE_PYTHON) -> pipeline-python-maat.thoth.cue
reserve-check-python:
	@set -eu; staged=$$(mktemp); trap 'rm -f "$$staged"' EXIT HUP INT TERM; \
	gh arrow cat '$(RESERVE_PYTHON)' > "$$staged"; \
	test ! -L pipeline-python-maat.thoth.cue; \
	diff -u ./pipeline-python-maat.thoth.cue "$$staged"

reserve-sync-python:
	gh arrow cp '$(RESERVE_PYTHON)' ./pipeline-python-maat.thoth.cue --force

# Managed mapping: $(RESERVE_PYTHON_TEST) -> pipeline-python-test-maat.thoth.cue
reserve-check-python-test:
	@set -eu; staged=$$(mktemp); trap 'rm -f "$$staged"' EXIT HUP INT TERM; \
	gh arrow cat '$(RESERVE_PYTHON_TEST)' > "$$staged"; \
	test ! -L pipeline-python-test-maat.thoth.cue; \
	diff -u ./pipeline-python-test-maat.thoth.cue "$$staged"

reserve-sync-python-test:
	gh arrow cp '$(RESERVE_PYTHON_TEST)' ./pipeline-python-test-maat.thoth.cue --force
