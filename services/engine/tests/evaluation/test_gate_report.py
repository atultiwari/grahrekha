from grahrekha_engine.evaluation.gate_eval import Outcome, pct, report
from grahrekha_engine.palm.gate import GateConfig


def _o(
    expect: str, passed: bool, codes: tuple[str, ...] = (), source: str = "S", sl: str = "x"
) -> Outcome:
    return Outcome("p", source, expect, sl, passed, codes, {})


def test_pct_formats_counts_and_handles_empty() -> None:
    assert pct(1, 4) == "25.0% (1/4)"
    assert pct(0, 0) == "n/a"


def test_report_computes_headline_rates_and_breakdowns() -> None:
    pos = [
        _o("palm", True),
        _o("palm", False, ("BLURRY",)),
        _o("palm", False, ("BLURRY", "CROPPED")),
    ]
    neg = [_o("NO_HAND", False, ("NO_HAND",), "feet"), _o("NO_HAND", True, (), "feet")]
    text = report(pos, neg, GateConfig())

    assert "| Negatives rejected | 50.0% (1/2) | >= 97% |" in text
    assert "| Positives falsely rejected | 66.7% (2/3) | <= 5% |" in text
    assert "- `BLURRY`: 2" in text
    assert "- `CROPPED`: 1" in text
    assert "- feet: rejected 50.0% (1/2)" in text
    assert '"min_sharpness": 4.0' in text
