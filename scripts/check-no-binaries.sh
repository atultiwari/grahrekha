#!/usr/bin/env bash
# Blocks images, model weights, datasets, databases and env files from being committed
# (docs/DECISIONS.md D-011, D-014). Synthetic test fixtures are the only exception.
#
#   scripts/check-no-binaries.sh            # check all tracked files (CI)
#   scripts/check-no-binaries.sh --staged   # check staged files (pre-commit)
#   scripts/check-no-binaries.sh FILE...    # check the given paths
set -euo pipefail

MAX_BYTES=$((2 * 1024 * 1024))
BLOCKED_EXT='\.(jpe?g|png|gif|bmp|tiff?|webp|heic|heif|raw|onnx|pth|pt|ckpt|safetensors|task|tflite|h5|npy|npz|parquet|zip|tar|tgz|gz|rar|7z|db|sqlite3?|mat)$'
ALLOWED_DIR='(^|/)fixtures/synthetic/'
ALLOWED_FILES='^(apps/[^/]+/(public|assets)/.*\.(png|svg|ico|webp)|apps/web/app/(favicon\.ico|icon\.png|apple-icon\.png))$'

# Portable to macOS bash 3.2 (no mapfile).
files=()
if [[ "${1:-}" == "--staged" ]]; then
  while IFS= read -r line; do files+=("$line"); done < <(git diff --cached --name-only --diff-filter=ACMR)
elif [[ $# -gt 0 ]]; then
  files=("$@")
else
  while IFS= read -r line; do files+=("$line"); done < <(git ls-files)
fi

violations=()
count=0
for f in ${files[@]+"${files[@]}"}; do
  [[ -z "$f" ]] && continue
  lower=$(printf '%s' "$f" | tr '[:upper:]' '[:lower:]')
  if [[ "$lower" =~ $ALLOWED_DIR ]] || [[ "$f" =~ $ALLOWED_FILES ]]; then continue; fi
  base=$(basename "$f")
  if [[ "$base" == .env* && "$base" != ".env.example" ]]; then
    violations+=("$f (env file)"); count=$((count + 1)); continue
  fi
  if [[ "$lower" =~ $BLOCKED_EXT ]]; then
    violations+=("$f (blocked file type)"); count=$((count + 1)); continue
  fi
  if [[ "$f" == data/* && "$f" != "data/README.md" && "$f" != "data/manifest.yaml" ]]; then
    violations+=("$f (data/ is git-ignored)"); count=$((count + 1)); continue
  fi
  if [[ -f "$f" ]]; then
    size=$(wc -c < "$f" | tr -d ' ')
    if (( size > MAX_BYTES )); then violations+=("$f (larger than 2 MB)"); count=$((count + 1)); fi
  fi
done

if (( count > 0 )); then
  echo "Blocked files (see CONTRIBUTING.md — no real images, datasets, weights or env files):" >&2
  printf '  - %s\n' "${violations[@]}" >&2
  exit 1
fi
echo "check-no-binaries: OK (${#files[@]} files)"
