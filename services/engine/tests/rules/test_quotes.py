"""Every rule's quote must appear verbatim in its public-domain source (no invented citations)."""

import re
from pathlib import Path

import pytest

from grahrekha_engine.rules.model import load_rules

ROOT = Path(__file__).resolve().parents[4]
SOURCES = {
    "Cheiro, Palmistry for All (1916)": ROOT / "data/raw/B1-cheiro-palmistry-for-all/pg20480.txt"
}


def _normalise(text: str) -> str:
    text = re.sub(r"\s*\([^)]*Plate[^)]*\)", "", text)  # Cheiro's plate references
    return re.sub(r"\s+", " ", text).strip()


@pytest.mark.parametrize("rule", load_rules(ROOT / "rules/palm"), ids=lambda r: r.id)
def test_quote_is_verbatim_in_source(rule) -> None:  # type: ignore[no-untyped-def]
    path = SOURCES.get(rule.source.work)
    assert path is not None, f"unknown source work {rule.source.work!r}"
    if not path.exists():
        pytest.skip(f"run scripts/fetch-data.sh --only B1 ({path.name})")
    assert rule.source.quote, "rules must quote their source"
    assert _normalise(rule.source.quote).strip('"') in _normalise(path.read_text())
