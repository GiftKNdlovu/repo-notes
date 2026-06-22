#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/python ]; then
  echo "Missing .venv. Create it with: uv venv --python python3.12 && . .venv/bin/activate && uv pip install -e '.[dev]'" >&2
  exit 1
fi

TMPDIR_CHECK="$(mktemp -d)"
cleanup() {
  if [ -f "$TMPDIR_CHECK/AGENTS.md" ]; then
    cp "$TMPDIR_CHECK/AGENTS.md" AGENTS.md
  else
    rm -f AGENTS.md
  fi

  if [ -f "$TMPDIR_CHECK/.repo-notes-cache.json" ]; then
    cp "$TMPDIR_CHECK/.repo-notes-cache.json" .repo-notes-cache.json
  else
    rm -f .repo-notes-cache.json
  fi

  rm -rf "$TMPDIR_CHECK"
}
trap cleanup EXIT

[ -f AGENTS.md ] && cp AGENTS.md "$TMPDIR_CHECK/AGENTS.md"
[ -f .repo-notes-cache.json ] && cp .repo-notes-cache.json "$TMPDIR_CHECK/.repo-notes-cache.json"

. .venv/bin/activate

python -m compileall -q src tests
ruff check src tests
python -m pytest tests -q
python -m repo_notes . --format json --output /tmp/repo-notes-smoke.json --no-cache --quiet
python -m json.tool /tmp/repo-notes-smoke.json >/dev/null
python -m repo_notes . --agents --output /tmp/repo-notes-smoke.md --no-cache --quiet

echo "repo-notes checks passed"
