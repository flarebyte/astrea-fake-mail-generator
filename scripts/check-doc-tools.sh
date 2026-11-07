#!/bin/sh
# Report every requirement and fail if any are missing.
set -u
missing=0
for tool in sh python3 gh flyb; do
    if command -v "$tool" >/dev/null 2>&1; then
        printf '%s=true\n' "$tool"
    else
        printf '%s=false\n' "$tool"
        missing=1
    fi
done
if command -v gh >/dev/null 2>&1 && gh flarebyte script --help >/dev/null 2>&1; then
    printf 'gh-flarebyte-script=true\n'
else
    printf 'gh-flarebyte-script=false\n'
    missing=1
fi
exit "$missing"
