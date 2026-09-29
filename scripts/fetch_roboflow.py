#!/usr/bin/env python3
"""Fetch Roboflow Universe palm-line datasets (manifest D24) for internal R&D (D-014).

Usage: python3 scripts/fetch_roboflow.py [workspace/project/version:format ...]

The API key comes from ROBOFLOW_API_KEY (environment or the git-ignored .env.local) and
is never printed or written anywhere else. Each export is unzipped into
data/raw/D24-roboflow/<workspace>__<project>__v<version>/ and the zip is deleted.
Standard library only.
"""

import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/D24-roboflow"
LOG = ROOT / "data/fetch-log.tsv"
API = "https://api.roboflow.com"
# Chosen for per-line labels (research/02, 2026-09-30 review of all 11 D24 projects).
DEFAULT = [
    "cv2project-uu3kn/palmistry-zbcbn/2:coco-segmentation",
    "24rd021/palm-reading-itwlw/13:coco-segmentation",
    "palm-reading-test/palm-line-segmentation/1:coco-segmentation",
    "docseg/palmistry-kp/6:coco",
]
EXPORT_WAIT_S = 600
MAX_EXPORT_BYTES = 3 * 1024**3  # disk is tight; refuse anything larger


def api_key() -> str:
    key = os.environ.get("ROBOFLOW_API_KEY", "")
    env_file = ROOT / ".env.local"
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ROBOFLOW_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        sys.exit("ROBOFLOW_API_KEY is not set (environment or .env.local)")
    return key


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def export_link(spec: str, key: str) -> str:
    """Ask Roboflow to prepare an export and wait until it has a download link."""
    path, fmt = spec.rsplit(":", 1)
    url = f"{API}/{path}/{fmt}?{urllib.parse.urlencode({'api_key': key})}"
    deadline = time.monotonic() + EXPORT_WAIT_S
    while time.monotonic() < deadline:
        body = get_json(url)
        link = (body.get("export") or {}).get("link")
        if link:
            return str(link)
        time.sleep(10)  # export is still being generated
    raise TimeoutError(f"export not ready after {EXPORT_WAIT_S}s: {spec}")


def download(link: str) -> bytes:
    with urllib.request.urlopen(link, timeout=600) as response:
        size = int(response.headers.get("Content-Length") or 0)
        if size > MAX_EXPORT_BYTES:
            raise ValueError(f"export is {size / 1e9:.1f} GB, above the {MAX_EXPORT_BYTES / 1e9:.0f} GB cap")
        return response.read()


def fetch(spec: str, key: str) -> None:
    path, fmt = spec.rsplit(":", 1)
    workspace, project, version = path.split("/")
    dest = OUT / f"{workspace}__{project}__v{version}"
    if (dest / ".done").exists():
        print(f"skip (done): {spec}")
        return
    data = download(export_link(spec, key))
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.namelist():  # refuse path traversal from the archive
            target = (dest / member).resolve()
            if not target.is_relative_to(dest.resolve()):
                raise ValueError(f"unsafe path in archive: {member}")
        archive.extractall(dest)
    (dest / ".done").touch()
    source = f"https://universe.roboflow.com/{workspace}/{project}/dataset/{version} ({fmt})"
    with LOG.open("a") as log:
        log.write(f"D24\t{dest.relative_to(ROOT)}\t{len(data)}\t-\t{source}\t{time.strftime('%FT%TZ', time.gmtime())}\n")
    print(f"ok: {spec} -> {dest.relative_to(ROOT)} ({len(data) / 1e6:.0f} MB)")


def main() -> None:
    key = api_key()
    failures = 0
    for spec in sys.argv[1:] or DEFAULT:
        try:
            fetch(spec, key)
        except (urllib.error.URLError, ValueError, TimeoutError, zipfile.BadZipFile) as error:
            failures += 1
            # str(HTTPError/URLError) holds the status or reason, never the URL (which
            # carries the API key), so it is safe to print.
            print(f"FAILED: {spec}: {type(error).__name__}: {error}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
