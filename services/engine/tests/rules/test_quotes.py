"""Every rule's quote must appear in its public-domain source (no invented citations).

Gutenberg texts are clean, so quotes must match verbatim. The Jyotish sources are OCR
scans (archive.org), so quotes are lightly corrected ("Suu" -> "Sun") and must match the
OCR text at >= 90% character similarity after normalisation.
"""

import re
from difflib import SequenceMatcher
from pathlib import Path

import pytest

from grahrekha_engine.rules.model import load_rules

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data/raw"
VERBATIM = {
    "Cheiro, Palmistry for All (1916)": RAW / "B1-cheiro-palmistry-for-all/pg20480.txt",
}
OCR = {
    "Varahamihira, Brihat Jataka, tr. N. Chidambaram Iyer (1885)": (
        RAW / "B2-brihat-jataka-iyer-1885/b2488442x_djvu.txt"
    ),
    "Jataka Chandrika, tr. B. Suryanarain Rao (1900)": (
        RAW / "B3-jataka-chandrika-rao-1900/jataka-chandrika-1900_djvu.txt"
    ),
}
OCR_MIN_SIMILARITY = 0.9


def _normalise(text: str) -> str:
    text = re.sub(r"\s*\([^)]*Plate[^)]*\)", "", text)  # Cheiro's plate references
    return re.sub(r"\s+", " ", text).strip()


def _ocr_normalise(text: str) -> str:
    text = re.sub(r"-\s*\n\s*", "", text)  # words hyphenated across lines
    text = re.sub(r"\([a-z&\d]\)", "", text)  # footnote markers such as (a)
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _window_similarity(s: str, q: str, anchor: str, anchor_at: int) -> float:
    """Similarity of q to source windows aligned on anchor's longest match in s."""
    matcher = SequenceMatcher(None, s, anchor, autojunk=False)
    block = matcher.find_longest_match(0, len(s), 0, len(anchor))
    start = max(0, block.a - block.b - anchor_at - 20)
    window = s[start : start + len(q) + 40]
    offsets = range(0, max(1, len(window) - len(q) + 1))
    return max(SequenceMatcher(None, window[o : o + len(q)], q).ratio() for o in offsets)


def ocr_similarity(quote: str, source: str) -> float:
    """Best similarity of the quote to any same-length window of the source.

    Windows are aligned on the longest exact match of the whole quote and of each half,
    so a common opening phrase repeated elsewhere cannot hide the real passage.
    """
    q, s = _ocr_normalise(quote), _ocr_normalise(source)
    half = len(q) // 2
    anchors = [(q, 0), (q[:half], 0), (q[half:], half)]
    return max(_window_similarity(s, q, anchor, at) for anchor, at in anchors if anchor)


def test_ocr_similarity_tolerates_ocr_errors_but_not_inventions() -> None:
    source = "If  he  occupy  the  lOth  house,  the  per-\nson  will  live  in  comfort  (a)"
    assert (
        ocr_similarity("if he occupy the 10th house, the person will live in comfort", source) > 0.9
    )
    assert ocr_similarity("if he occupy the 10th house, the person will be a king", source) < 0.9


ALL_RULES = [rule for engine in ("palm", "astro") for rule in load_rules(ROOT / "rules" / engine)]


@pytest.mark.parametrize("rule", ALL_RULES, ids=lambda r: r.id)
def test_quote_is_in_source(rule) -> None:  # type: ignore[no-untyped-def]
    work = rule.source.work
    path = VERBATIM.get(work) or OCR.get(work)
    assert path is not None, f"unknown source work {work!r}"
    if not path.exists():
        pytest.skip(f"run scripts/fetch-data.sh --only B1,B2,B3 ({path.name})")
    assert rule.source.quote, "rules must quote their source"
    text = path.read_text(encoding="utf-8", errors="replace")
    if work in VERBATIM:
        assert _normalise(rule.source.quote).strip('"') in _normalise(text)
    else:
        similarity = ocr_similarity(rule.source.quote.strip('"'), text)
        assert similarity >= OCR_MIN_SIMILARITY, f"quote similarity {similarity:.2f}"
