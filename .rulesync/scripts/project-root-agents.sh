#!/bin/sh
set -eu

source_file=.rulesync/rules/overview.md
target_file=AGENTS.md
tmp_file=$(mktemp)
trap 'rm -f "$tmp_file"' EXIT

awk '
NR == 1 && $0 == "---" { frontmatter = 1; next }
frontmatter && $0 == "---" { frontmatter = 0; next }
!frontmatter && !started && $0 == "" { next }
!frontmatter { started = 1; print }
' "$source_file" > "$tmp_file"

test -s "$tmp_file"

if [ "${1:-}" = "--check" ]; then
  cmp -s "$target_file" "$tmp_file"
else
  mv "$tmp_file" "$target_file"
  trap - EXIT
fi
