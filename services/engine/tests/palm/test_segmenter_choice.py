from pathlib import Path

from grahrekha_engine.config import Settings
from grahrekha_engine.palm.pipeline import LINE_MODELS, resolve_segmenter


def _install(models: Path, segmenter: str) -> None:
    path = models / LINE_MODELS[segmenter]
    path.parent.mkdir(parents=True)
    path.write_bytes(b"onnx")


def test_auto_prefers_v1_when_its_weights_are_installed(tmp_path: Path) -> None:
    _install(tmp_path, "v1")
    assert resolve_segmenter("auto", tmp_path) == "v1"


def test_auto_prefers_the_newest_installed_model(tmp_path: Path) -> None:
    _install(tmp_path, "v1")
    _install(tmp_path, "v2")
    assert resolve_segmenter("auto", tmp_path) == "v2"


def test_every_model_version_is_stamped_on_features() -> None:
    from grahrekha_engine.palm.pipeline import pipeline_ids

    assert pipeline_ids("v2")["segmenter"] == "grahrekha-lines-v2"
    assert pipeline_ids("v2")["fate"] == "grahrekha-lines-v2"
    assert pipeline_ids("v1")["segmenter"] == "grahrekha-lines-v1"
    assert pipeline_ids("v0")["fate"] == "classical-f1"


def test_auto_falls_back_to_v0_without_v1_weights(tmp_path: Path) -> None:
    assert resolve_segmenter("auto", tmp_path) == "v0"


def test_explicit_choice_is_kept_even_if_missing(tmp_path: Path) -> None:
    # A missing explicit model must fail loudly later (503), not silently switch.
    assert resolve_segmenter("v1", tmp_path) == "v1"
    assert resolve_segmenter("v0", tmp_path) == "v0"


def test_default_setting_is_auto() -> None:
    assert Settings(shared_secret="s").segmenter == "auto"
