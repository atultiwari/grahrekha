#!/usr/bin/env bash
# Fetch R&D datasets and model weights (see docs/RESOURCES-REGISTRY.md, D-014).
# Everything lands in git-ignored folders. Each item is extracted, then its archive
# is deleted to save disk. Re-runs skip items that already have a .done marker.
#
# Usage: scripts/fetch-data.sh --tier 1 [--only D2,M1]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW="$ROOT/data/raw"
WEIGHTS="$ROOT/services/engine/models/weights"
LOG="$ROOT/data/fetch-log.tsv"   # id \t file \t bytes \t sha256 \t url \t date
TIER=1
ONLY=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tier) TIER="$2"; shift 2 ;;
    --only) ONLY="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$RAW" "$WEIGHTS"
touch "$LOG"

want() { [[ -z "$ONLY" || ",$ONLY," == *",$1,"* ]]; }
done_marker() { [[ -f "$1/.done" ]]; }

CHECKSUMS="$ROOT/data/checksums.sha256"

file_size() { # GNU stat first: on Linux, `stat -f` means "filesystem status" and succeeds with junk
  stat -c%s "$1" 2>/dev/null || stat -f%z "$1"
}

sha256_of() { # portable: shasum (macOS, Perl) or sha256sum (Debian/Alpine coreutils)
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  else sha256sum "$1" | cut -d' ' -f1; fi
}

record() { # id file url — verifies against data/checksums.sha256 when an entry exists
  local key bytes sha expected
  key="$1/$(basename "$2")"
  bytes=$(file_size "$2")
  sha=$(sha256_of "$2")
  expected=$(awk -v k="$key" '$2 == k {print $1}' "$CHECKSUMS" 2>/dev/null || true)
  if [[ -n "$expected" && "$expected" != "$sha" ]]; then
    echo "CHECKSUM MISMATCH for $key: expected $expected, got $sha. Deleting download." >&2
    rm -f "$2"; exit 1
  fi
  [[ -z "$expected" ]] && echo "note: no pinned checksum for $key (new item?) sha256=$sha" >&2
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "${2#$ROOT/}" "$bytes" "$sha" "$3" "$(date -u +%FT%TZ)" >> "$LOG"
}

curl_get() { # url out
  curl -fL --retry 3 --retry-delay 5 -C - -o "$2" "$1"
}

gdrive_get() { # id out [resourcekey]
  local url="https://drive.usercontent.google.com/download?id=$1&export=download&confirm=t"
  [[ -n "${3:-}" ]] && url="$url&resourcekey=$3"
  curl_get "$url" "$2"
  # Drive sometimes returns an HTML quota/interstitial page instead of the file.
  if file "$2" | grep -qi html; then
    echo "Drive returned HTML for $1 (quota?). Retry later or use gdown." >&2
    rm -f "$2"; return 1
  fi
}

hf_get() { # repo out_dir [include-pattern]
  local args=(download "$1" --repo-type dataset --local-dir "$2")
  [[ -n "${3:-}" ]] && args+=(--include "$3")
  uvx --from huggingface_hub hf "${args[@]}"
}

extract() { # archive dest — detects the real format (some sources mislabel .tar.gz as .zip)
  mkdir -p "$2"
  case "$(file -b "$1")" in
    Zip*)
      # Python's zipfile copes with non-ASCII member names that trip macOS unzip.
      python3 -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])' "$1" "$2" ;;
    gzip*) tar -xzf "$1" -C "$2" ;;
    *) echo "not an archive, keeping as-is: $1" >&2; return 0 ;;
  esac
  rm -f "$1"
}

item() { # id dir -> prints dir path, returns 1 if already done or not wanted
  local id="$1" dir="$2"
  want "$id" || return 1
  if done_marker "$dir"; then echo "skip $id (done)" >&2; return 1; fi
  mkdir -p "$dir"; echo "==> $id → ${dir#$ROOT/}" >&2
}

finish() { touch "$1/.done"; }

# ---------------------------------------------------------------- Tier 1
if [[ "$TIER" -ge 1 ]]; then

  d="$RAW/D1-11k-hands"
  if item D1 "$d"; then
    gdrive_get 1KcMYcNJgtK1zZvfl_9sTqnyBUTri2aP2 "$d/Hands.zip" \
      || curl_get "https://huggingface.co/datasets/Zicara/Hands_11k/resolve/main/Hands.zip" "$d/Hands.zip"
    record D1 "$d/Hands.zip" "gdrive:1KcMYcNJgtK1zZvfl_9sTqnyBUTri2aP2"
    gdrive_get 1RC86-rVOR8c93XAfM9b9R45L7C2B0FdA "$d/HandInfo.csv"
    record D1 "$d/HandInfo.csv" "gdrive:1RC86-rVOR8c93XAfM9b9R45L7C2B0FdA"
    extract "$d/Hands.zip" "$d"; finish "$d"
  fi

  d="$RAW/D2-plsu"
  if item D2 "$d"; then
    gdrive_get 1B4uj-b4RuUNkC_oeCsRkuih4rjuQ6tHH "$d/PLSU.zip"
    record D2 "$d/PLSU.zip" "gdrive:1B4uj-b4RuUNkC_oeCsRkuih4rjuQ6tHH"
    extract "$d/PLSU.zip" "$d"; finish "$d"
  fi

  d="$RAW/D3-axondata-palm-recognition"
  if item D3 "$d"; then
    hf_get AxonData/palm-recognition-dataset "$d"
    echo -e "D3\t${d#$ROOT/}\t-\t-\thf:AxonData/palm-recognition-dataset\t$(date -u +%FT%TZ)" >> "$LOG"
    finish "$d"
  fi

  d="$RAW/D4-human-palm-images"
  if item D4 "$d"; then
    u="https://www.kaggle.com/api/v1/datasets/download/feyiamujo/human-palm-images"
    curl_get "$u" "$d/archive.zip"; record D4 "$d/archive.zip" "$u"
    extract "$d/archive.zip" "$d"; finish "$d"
  fi

  d="$RAW/D5-palmprint-crease"
  if item D5 "$d"; then
    u="https://www.kaggle.com/api/v1/datasets/download/tmtrnhelloworld/palmprint-v1i-crease"
    curl_get "$u" "$d/archive.zip"; record D5 "$d/archive.zip" "$u"
    extract "$d/archive.zip" "$d"; finish "$d"
  fi

  d="$RAW/D6-quickdraw-hand"
  if item D6 "$d"; then
    u="https://storage.googleapis.com/quickdraw_dataset/full/simplified/hand.ndjson"
    curl_get "$u" "$d/hand.ndjson"; record D6 "$d/hand.ndjson" "$u"; finish "$d"
  fi

  d="$RAW/D7-imagenette2-320"
  if item D7 "$d"; then
    u="https://s3.amazonaws.com/fast-ai-imageclas/imagenette2-320.tgz"
    curl_get "$u" "$d/imagenette2-320.tgz"; record D7 "$d/imagenette2-320.tgz" "$u"
    extract "$d/imagenette2-320.tgz" "$d"; finish "$d"
  fi

  d="$RAW/D8-oxford-pets-test"
  if item D8 "$d"; then
    hf_get timm/oxford-iiit-pet "$d" "data/test*"
    echo -e "D8\t${d#$ROOT/}\t-\t-\thf:timm/oxford-iiit-pet (data/test*)\t$(date -u +%FT%TZ)" >> "$LOG"
    finish "$d"
  fi

  d="$RAW/D9-lfw-sample"
  if item D9 "$d"; then
    hf_get 0xmoose/lfw-sample "$d"
    echo -e "D9\t${d#$ROOT/}\t-\t-\thf:0xmoose/lfw-sample\t$(date -u +%FT%TZ)" >> "$LOG"
    finish "$d"
  fi

  d="$RAW/D10-dfu-feet"
  if item D10 "$d"; then
    u="https://www.kaggle.com/api/v1/datasets/download/laithjj/diabetic-foot-ulcer-dfu"
    curl_get "$u" "$d/archive.zip"; record D10 "$d/archive.zip" "$u"
    extract "$d/archive.zip" "$d"; finish "$d"
  fi

  d="$RAW/D11-hand-seg-wild"
  if item D11 "$d"; then
    gdrive_get 1hHUvINGICvOGcaDgA5zMbzAIUv7ewDd3 "$d/hof.zip"; record D11 "$d/hof.zip" "gdrive:1hHUvINGICvOGcaDgA5zMbzAIUv7ewDd3"
    gdrive_get 1EwjJx-V-Gq7NZtfiT6LZPLGXD2HN--qT "$d/eyth.zip"; record D11 "$d/eyth.zip" "gdrive:1EwjJx-V-Gq7NZtfiT6LZPLGXD2HN--qT"
    extract "$d/hof.zip" "$d/hof"; extract "$d/eyth.zip" "$d/eyth"; finish "$d"
  fi

  d="$RAW/B1-cheiro-palmistry-for-all"
  if item B1 "$d"; then
    u="https://www.gutenberg.org/cache/epub/20480/pg20480.txt"
    curl_get "$u" "$d/pg20480.txt"; record B1 "$d/pg20480.txt" "$u"; finish "$d"
  fi

  # Jyotish sources chosen for astrology rules (research/04-jyotish-sources.md): OCR text only.
  d="$RAW/B2-brihat-jataka-iyer-1885"
  if item B2 "$d"; then
    u="https://archive.org/download/b2488442x/b2488442x_djvu.txt"
    curl_get "$u" "$d/b2488442x_djvu.txt"; record B2 "$d/b2488442x_djvu.txt" "$u"; finish "$d"
  fi

  d="$RAW/B3-jataka-chandrika-rao-1900"
  if item B3 "$d"; then
    u="https://archive.org/download/Astrology_Books_by_B_Suryanarayana_Row/Jataka%20Chandrika%20-%20B%20Suryanarayana%20Row%201900_djvu.txt"
    curl_get "$u" "$d/jataka-chandrika-1900_djvu.txt"; record B3 "$d/jataka-chandrika-1900_djvu.txt" "$u"; finish "$d"
  fi

  # ---- models
  d="$WEIGHTS/A1-de421"
  if item A1 "$d"; then
    u="https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp"
    curl_get "$u" "$d/de421.bsp"; record A1 "$d/de421.bsp" "$u"; finish "$d"
  fi

  # GeoNames changes daily, so A2 has no pinned checksum; the log records what was fetched.
  d="$WEIGHTS/A2-geonames"
  if item A2 "$d"; then
    u="https://download.geonames.org/export/dump/cities5000.zip"
    a="https://download.geonames.org/export/dump/admin1CodesASCII.txt"
    curl_get "$u" "$d/cities5000.zip"; record A2 "$d/cities5000.zip" "$u"
    curl_get "$a" "$d/admin1CodesASCII.txt"; record A2 "$d/admin1CodesASCII.txt" "$a"
    extract "$d/cities5000.zip" "$d"; finish "$d"
  fi

  d="$WEIGHTS/M1-mediapipe"
  if item M1 "$d"; then
    u="https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
    curl_get "$u" "$d/hand_landmarker.task"; record M1 "$d/hand_landmarker.task" "$u"; finish "$d"
  fi

  d="$WEIGHTS/M2-palm-line-reader"
  if item M2 "$d"; then
    base="https://raw.githubusercontent.com/samuelwbarber/palm-line-reader/bc48939f4deee6d8ff842bfde499396dab9c4830"  # pinned commit
    for f in models/student_fp16.onnx models/student_fp32.onnx models/student_int8.onnx models/model_meta.json \
             docs/example1_input.png docs/example2_input.png docs/example3_input.png docs/example4_input.png; do
      out="$d/$(basename "$f")"; curl_get "$base/$f" "$out"; record M2 "$out" "$base/$f"
    done
    finish "$d"
  fi

  d="$WEIGHTS/M3-yeonsumia"
  if item M3 "$d"; then
    base="https://raw.githubusercontent.com/yeonsumia/palmistry/17610c3f031ee312d3352116eefff9b833e9cafb"  # pinned commit
    curl_get "$base/code/checkpoint/checkpoint_aug_epoch70.pth" "$d/checkpoint_aug_epoch70.pth"
    record M3 "$d/checkpoint_aug_epoch70.pth" "$base/code/checkpoint/checkpoint_aug_epoch70.pth"
    mkdir -p "$RAW/M3-yeonsumia-samples"
    for f in hand1 hand6 hand48 hand70; do
      curl_get "$base/code/input/$f.jpg" "$RAW/M3-yeonsumia-samples/$f.jpg" || true
    done
    finish "$d"
  fi
fi

echo "All requested items done. Log: ${LOG#$ROOT/}"
