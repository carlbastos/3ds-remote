#!/bin/sh
# Usage: tools/release.sh X.Y.Z
# Bumps VERSION, commits, tags vX.Y.Z and pushes; the "build" workflow then publishes the release.
set -e
cd "$(dirname "$0")/.."
new="$1"
echo "$new" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || { echo "usage: $0 X.Y.Z" >&2; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "working tree not clean" >&2; exit 1; }
[ "$(git rev-parse --abbrev-ref HEAD)" = main ] || { echo "not on main" >&2; exit 1; }
git rev-parse -q --verify "refs/tags/v$new" >/dev/null && { echo "tag v$new already exists" >&2; exit 1; }

old="$(cat VERSION)"
if [ "$old" != "$new" ]; then
  echo "$new" > VERSION
  git commit -q -m "Release v$new" VERSION
fi
git tag -a "v$new" -m "3ds-remote v$new"
git push -q origin main "v$new"
echo "pushed v$new (was $old); follow the build with: gh run watch"
