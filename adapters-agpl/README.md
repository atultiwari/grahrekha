# adapters-agpl (AGPL-3.0, optional)

This folder is **licensed separately under the GNU AGPL v3.0** (see [LICENSE](LICENSE)). It is **not** covered by the repository's Apache-2.0 licence.

## Why it exists

Some useful libraries are AGPL:
- Swiss Ephemeris (`pyswisseph`)
- PyJHora
- kerykeion
- Ultralytics YOLO

We want to **measure** whether they beat the permissive defaults before deciding to license them. That's decision [D-011](../docs/DECISIONS.md).

## How it stays separate

- Core (`services/engine`) **never imports** anything from here. A test in `services/engine/tests/test_agpl_boundary.py` enforces this.
- Providers plug in through Python entry points. Core asks for them by name, for example `load_provider("grahrekha.ephemeris", "swisseph")`.
- The package is installed only when explicitly requested with `uv sync --extra agpl`.
- A deployment that enables it is an AGPL combined work. That is fine for R&D and an open demo. Any closed or paid deployment must leave it out, or obtain licences.

## Status

- `validate_astro.py`: validates the default (MIT) astrology engine against Swiss Ephemeris. It runs in CI. Results: [docs/eval/astro-validation.md](../docs/eval/astro-validation.md).
- **No production provider here yet.** The MIT engine meets the accuracy targets, so none is needed for now (D-005).
