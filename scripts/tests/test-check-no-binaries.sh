#!/usr/bin/env bash
# Tests for scripts/check-no-binaries.sh. Run: bash scripts/tests/test-check-no-binaries.sh
set -uo pipefail
cd "$(dirname "$0")/../.."
check=scripts/check-no-binaries.sh
fail=0

expect() { # expected_exit description path...
  local expected=$1 desc=$2; shift 2
  "$check" "$@" >/dev/null 2>&1; local got=$?
  if [[ $got -eq $expected ]]; then echo "ok   - $desc"; else echo "FAIL - $desc (exit $got, want $expected)"; fail=1; fi
}

expect 1 "blocks a palm photo"               data/raw/D1/hand.jpg
expect 1 "blocks an uppercase JPEG"          docs/Palm.JPG
expect 1 "blocks ONNX weights"               services/engine/models/weights/x.onnx
expect 1 "blocks a SQLite database"          var/app.db
expect 1 "blocks .env.local"                 apps/web/.env.local
expect 1 "blocks anything in data/"          data/splits/eval.txt
expect 1 "blocks a zip archive"              ml/export.zip
expect 0 "allows data/README.md"             data/README.md
expect 0 "allows data/manifest.yaml"         data/manifest.yaml
expect 0 "allows .env.example"               .env.example
expect 0 "allows synthetic fixtures"         services/engine/tests/fixtures/synthetic/line.png
expect 0 "allows source code"                services/engine/src/grahrekha_engine/main.py
expect 0 "allows web public icons"           apps/web/public/logo.png

# --staged mode inside a throwaway git repo (exercises the no-mapfile code path).
tmp=$(mktemp -d); root=$(pwd)
(
  cd "$tmp" && git init -q && mkdir -p src data
  echo 'print(1)' > src/a.py && git add src/a.py
  "$root/$check" --staged >/dev/null 2>&1
) && echo "ok   - --staged passes clean changes" || { echo "FAIL - --staged clean"; fail=1; }
(
  cd "$tmp" && echo x > data/palm.jpg && git add -f data/palm.jpg
  ! "$root/$check" --staged >/dev/null 2>&1
) && echo "ok   - --staged blocks a staged photo" || { echo "FAIL - --staged photo"; fail=1; }
rm -rf "$tmp"

exit $fail
