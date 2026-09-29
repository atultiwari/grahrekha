#!/usr/bin/env bash
# Tests for scripts/check-no-binaries.sh. Run: bash scripts/tests/test-check-no-binaries.sh
# Must pass on macOS bash 3.2 and Linux bash 5.
set -uo pipefail
cd "$(dirname "$0")/../.."
root=$(pwd)
check="$root/scripts/check-no-binaries.sh"
fail=0

pass() { echo "ok   - $1"; }
flunk() { echo "FAIL - $1"; fail=1; }

expect() { # expected_exit description path...
  local expected=$1 desc=$2; shift 2
  "$check" "$@" >/dev/null 2>&1; local got=$?
  if [[ $got -eq $expected ]]; then pass "$desc"; else flunk "$desc (exit $got, want $expected)"; fi
}

# ---- explicit path mode
expect 1 "blocks a palm photo"                 data/raw/D1/hand.jpg
expect 1 "blocks an uppercase JPEG"            docs/Palm.JPG
expect 1 "blocks ONNX weights"                 services/engine/models/weights/x.onnx
expect 1 "blocks pickle weights"               ml/model.pkl
expect 1 "blocks GGUF weights"                 ml/model.gguf
expect 1 "blocks .bin weights"                 ml/pytorch_model.bin
expect 1 "blocks DICOM"                        ml/scan.dcm
expect 1 "blocks video"                        docs/demo.MP4
expect 1 "blocks AVIF images"                  docs/palm.avif
expect 1 "blocks private keys"                 deploy/server.pem
expect 1 "blocks xz archives"                  ml/data.tar.xz
expect 1 "blocks a SQLite database"            var/app.db
expect 1 "blocks anything under var/"          var/uploads/notes.txt
expect 1 "blocks anything under weights dirs"  services/engine/models/weights/meta.json
expect 1 "blocks node_modules"                 apps/web/node_modules/x/index.js
expect 1 "blocks .env.local"                   apps/web/.env.local
expect 1 "blocks uppercase .ENV"               .ENV
expect 1 "blocks mixed-case .Env.production"   apps/web/.Env.production
expect 1 "blocks anything in data/"            data/splits/eval.txt
expect 1 "blocks a zip archive"                ml/export.zip
expect 0 "allows data/README.md"               data/README.md
expect 0 "allows data/manifest.yaml"           data/manifest.yaml
expect 0 "allows data/checksums.sha256"        data/checksums.sha256
expect 0 "allows .env.example"                 .env.example
expect 0 "allows .envrc-style names (not env files)" .envrc
expect 0 "allows synthetic fixtures"           services/engine/tests/fixtures/synthetic/line.png
expect 0 "allows source code"                  services/engine/src/grahrekha_engine/main.py
expect 0 "allows web public icons"             apps/web/public/logo.png

# ---- git modes, each in a throwaway repo
tmp=$(mktemp -d)
new_repo() { rm -rf "$tmp/r"; mkdir -p "$tmp/r" && cd "$tmp/r" && git init -q && git config user.email t@t && git config user.name t; }
staged_exit() { "$check" --staged >/dev/null 2>&1; echo $?; }

new_repo; echo 'print(1)' > a.py; git add a.py
[[ $(staged_exit) -eq 0 ]] && pass "--staged passes clean changes" || flunk "--staged clean"

new_repo; mkdir data; echo x > data/palm.jpg; git add -f data/palm.jpg
[[ $(staged_exit) -eq 1 ]] && pass "--staged blocks a staged photo" || flunk "--staged photo"

new_repo; echo x > "é.jpg"; git add "é.jpg"
[[ $(staged_exit) -eq 1 ]] && pass "--staged blocks a non-ASCII filename (git quoting)" || flunk "--staged non-ASCII"

new_repo; echo x > "hand palm.JPG"; git add "hand palm.JPG"
[[ $(staged_exit) -eq 1 ]] && pass "--staged blocks a filename with spaces" || flunk "--staged spaces"

new_repo; name=$'nl\n.png'; echo x > "$name"; git add "$name"
[[ $(staged_exit) -eq 1 ]] && pass "--staged blocks a filename containing a newline" || flunk "--staged newline"

new_repo; echo SECRET=1 > .ENV; git add .ENV
[[ $(staged_exit) -eq 1 ]] && pass "--staged blocks an uppercase .ENV" || flunk "--staged .ENV"

new_repo; head -c 3000000 /dev/zero > big.txt; git add big.txt; : > big.txt
[[ $(staged_exit) -eq 1 ]] && pass "--staged measures the staged blob, not the working copy" || flunk "--staged size"

new_repo; mkdir -p var; echo x > var/notes.txt; git add -f var/notes.txt
[[ $(staged_exit) -eq 1 ]] && pass "--staged blocks force-added ignored dirs" || flunk "--staged var/"

new_repo; echo x > a.py; git add a.py; git commit -q -m init; mkdir d; echo x > d/p.webp; git add d/p.webp; git commit -q -m img
"$check" >/dev/null 2>&1; [[ $? -eq 1 ]] && pass "tracked mode blocks a committed image" || flunk "tracked image"

mkdir -p "$tmp/notrepo" && cd "$tmp/notrepo"
"$check" --staged >/dev/null 2>&1; rc=$?
[[ $rc -ne 0 ]] && pass "fails closed when git fails (not a repo)" || flunk "fail-open on git error"

cd "$root"; rm -rf "$tmp"
exit $fail
