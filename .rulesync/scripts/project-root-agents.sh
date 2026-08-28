#!/bin/sh
set -eu

source_file=.rulesync/rules/overview.md
target_file=AGENTS.md
tmp_file=$(mktemp "${target_file}.tmp.XXXXXX")
trap 'rm -f "$tmp_file"' EXIT

awk '
NR == 1 && $0 == "---" { frontmatter = 1; next }
frontmatter && $0 == "---" { frontmatter = 0; next }
!frontmatter && !started && $0 == "" { next }
!frontmatter { started = 1; print }
' "$source_file" > "$tmp_file"

test -s "$tmp_file"

case "${1:-write}" in
  write)
    mv "$tmp_file" "$target_file"
    ;;
  --check)
    cmp -s "$target_file" "$tmp_file"
    ;;
  *)
    echo "usage: $0 [--check]" >&2
    exit 2
    ;;
esac
