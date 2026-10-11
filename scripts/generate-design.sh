#!/bin/sh
set -eu
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo_dir"
python3 scripts/validate-specs.py
flyb validate --config doc/design-meta
flyb generate markdown --config doc/design-meta
