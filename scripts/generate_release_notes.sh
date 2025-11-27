#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 OLD_TAG NEW_TAG"
  exit 1
}

if [ "$#" -ne 2 ]; then
  usage
fi

OLD_TAG=$1
NEW_TAG=$2
RELEASE_FILE="docs/RELEASE_NOTES.md"

if ! git rev-parse -q --verify "refs/tags/$OLD_TAG" >/dev/null; then
  echo "Error: tag '$OLD_TAG' not found." >&2
  exit 1
fi

if ! git rev-parse -q --verify "refs/tags/$NEW_TAG" >/dev/null; then
  echo "Error: tag '$NEW_TAG' not found." >&2
  exit 1
fi

release_date=$(git log -1 --pretty=format:%ad --date=short "$NEW_TAG")
commits=$(git log --pretty=format:"- %h %s" "$OLD_TAG..$NEW_TAG")

if [ -z "$commits" ]; then
  echo "No commits found between '$OLD_TAG' and '$NEW_TAG'. Nothing to update." >&2
  exit 0
fi

if [ ! -f "$RELEASE_FILE" ]; then
  printf '# Release Notes\n\n' >"$RELEASE_FILE"
fi

tmp_file=$(mktemp)
trap 'rm -f "$tmp_file"' EXIT

{
  printf '# Release Notes\n\n'
  printf '%s - %s\n' "$NEW_TAG" "$release_date"
  printf '%s\n' "$commits"
  printf '\n'
  if [ -s "$RELEASE_FILE" ]; then
    sed '1d' "$RELEASE_FILE" | sed '1{/^$/d;}' || true
  fi
} >"$tmp_file"

mv "$tmp_file" "$RELEASE_FILE"
