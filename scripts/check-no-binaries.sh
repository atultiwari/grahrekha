#!/usr/bin/env bash
# Blocks images, model weights, datasets, databases, keys and env files from being
# committed (docs/DECISIONS.md D-011, D-014). Synthetic test fixtures are the only
# exception. Fails CLOSED: any git error is a failure, never an "OK".
#
#   scripts/check-no-binaries.sh            # check all tracked files (CI)
#   scripts/check-no-binaries.sh --staged   # check staged files (pre-commit)
#   scripts/check-no-binaries.sh FILE...    # check the given paths (working tree)
#
# Portable to macOS bash 3.2: no mapfile, no associative arrays, no ${x,,}.
set -euo pipefail

MAX_BYTES=$((2 * 1024 * 1024))
# Lower-cased path is matched, so extensions are case-insensitive.
BLOCKED_EXT='\.(jpe?g|png|gif|bmp|tiff?|webp|avif|heic|heif|jp2|raw|dng|dcm|nii|mp4|mov|avi|mkv|webm|onnx|pth|pt|ckpt|safetensors|bin|pkl|pickle|gguf|task|tflite|h5|npy|npz|parquet|arrow|zip|tar|tgz|gz|xz|bz2|zst|rar|7z|db|sqlite3?|mat|pem|key|p12|pfx)$'
BLOCKED_PATH='(^|/)(node_modules|models/weights)/|^var/'
ALLOWED_DIR='(^|/)fixtures/synthetic/'
ALLOWED_FILES='^(apps/[^/]+/(public|assets)/.*\.(png|svg|ico|webp)|apps/web/src/app/(favicon\.ico|icon\.png|apple-icon\.png))$'
DATA_ALLOWED='^data/(README\.md|manifest\.yaml|checksums\.sha256)$'

mode=paths
[[ "${1:-}" == "--staged" ]] && mode=staged
[[ $# -eq 0 ]] && mode=tracked

list=$(mktemp)
trap 'rm -f "$list"' EXIT

# NUL-separated, unquoted names: safe for spaces, newlines and non-ASCII.
# Output goes to a file (not a pipe/process substitution) so git failures are caught.
case "$mode" in
  staged)
    git -c core.quotepath=off diff --cached --name-only --diff-filter=ACMR -z > "$list" \
      || { echo "check-no-binaries: git failed; refusing to pass" >&2; exit 2; } ;;
  tracked)
    git -c core.quotepath=off ls-files -z > "$list" \
      || { echo "check-no-binaries: git failed; refusing to pass" >&2; exit 2; } ;;
  paths)
    for p in "$@"; do printf '%s\0' "$p"; done > "$list" ;;
esac

blob_size() { # size of what will actually be committed
  if [[ "$mode" == paths ]]; then
    [[ -f "$1" ]] && wc -c < "$1" | tr -d ' ' || echo 0
  else
    git cat-file -s ":$1" 2>/dev/null || echo 0
  fi
}

count=0
checked=0
report=""
flag() { report="$report  - $1"$'\n'; count=$((count + 1)); }

while IFS= read -r -d '' f; do
  [[ -z "$f" ]] && continue
  checked=$((checked + 1))
  lower=$(printf '%s' "$f" | tr '[:upper:]' '[:lower:]')
  base=$(basename "$lower")

  if [[ "$lower" =~ $ALLOWED_DIR ]] || [[ "$f" =~ $ALLOWED_FILES ]]; then continue; fi

  if [[ ( "$base" == ".env" || "$base" == .env.* ) && "$base" != ".env.example" ]]; then
    flag "$f (env file)"; continue
  fi
  if [[ "$lower" =~ $BLOCKED_PATH ]]; then flag "$f (ignored/runtime/weights directory)"; continue; fi
  if [[ "$lower" =~ $BLOCKED_EXT ]]; then flag "$f (blocked file type)"; continue; fi
  if [[ "$f" == data/* && ! "$f" =~ $DATA_ALLOWED ]]; then flag "$f (data/ is git-ignored)"; continue; fi

  size=$(blob_size "$f")
  if (( size > MAX_BYTES )); then flag "$f (larger than 2 MB)"; fi
done < "$list"

if (( count > 0 )); then
  echo "Blocked files (see CONTRIBUTING.md: no real images, datasets, weights, keys or env files):" >&2
  printf '%s' "$report" >&2
  exit 1
fi
echo "check-no-binaries: OK ($checked files)"
