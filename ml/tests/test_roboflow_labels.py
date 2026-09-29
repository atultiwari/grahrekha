import numpy as np

from grahrekha_ml.labels import FATE, HEAD, HEART, IGNORE, LIFE
from grahrekha_ml.roboflow_labels import (
    class_for,
    dhash,
    hamming,
    is_holdout,
    normalise_width,
    rasterize,
)


def test_class_names_from_all_sets_map_to_our_classes() -> None:
    assert class_for("Heart-Line") == HEART and class_for("heart_line") == HEART
    assert class_for("head line") == HEAD and class_for("head") == HEAD
    assert class_for("Life-Line") == LIFE and class_for("fate_line") == FATE
    for minor in ("marriage_line", "solar_line", "girdle of venus", "family ring", "property_line"):
        assert class_for(minor) == IGNORE  # real creases, just not ours
    for junk in ("0", "Palm-Reading", "Palm-Lines", "object"):
        assert class_for(junk) is None


def test_rasterize_fills_polygons_with_class_priority() -> None:
    square = [[10.0, 10.0, 30.0, 10.0, 30.0, 30.0, 10.0, 30.0]]
    anns = [(FATE, square), (HEART, square), (IGNORE, [[40.0, 40.0, 50.0, 40.0, 50.0, 50.0]])]
    label = rasterize(anns, (64, 64))
    assert label[20, 20] == HEART  # a named line beats fate where they overlap
    assert label[42, 45] == IGNORE and label[0, 0] == 0


def test_normalise_width_redraws_blobs_as_thin_lines() -> None:
    label = np.zeros((100, 100), np.uint8)
    label[40:60, 10:90] = HEAD  # a 20-px-wide blob
    thin = normalise_width(label, width=5)
    rows = np.nonzero((thin == HEAD).any(axis=1))[0]
    assert 3 <= len(rows) <= 7  # about 5 px thick
    assert (thin == HEAD)[:, 20:80].any(axis=0).all()  # still spans the line
    ignored = np.zeros((100, 100), np.uint8)
    ignored[10:20, 10:90] = IGNORE
    assert (normalise_width(ignored, width=5) == IGNORE).sum() == (ignored == IGNORE).sum()


def test_dhash_finds_near_duplicates_only() -> None:
    rng = np.random.default_rng(0)
    image = (rng.random((128, 128, 3)) * 255).astype(np.uint8)
    brighter = np.clip(image.astype(int) + 10, 0, 255).astype(np.uint8)
    other = (rng.random((128, 128, 3)) * 255).astype(np.uint8)
    assert hamming(dhash(image), dhash(brighter)) <= 4
    assert hamming(dhash(image), dhash(other)) > 16


def test_holdout_is_deterministic_and_about_a_fifth() -> None:
    names = [f"img_{i}.jpg" for i in range(1000)]
    held = [n for n in names if is_holdout(n)]
    assert held == [n for n in names if is_holdout(n)]
    assert 150 < len(held) < 250


def test_prune_spurs_removes_short_side_branches_but_keeps_the_line() -> None:
    from grahrekha_ml.roboflow_labels import prune_spurs

    skeleton = np.zeros((60, 100), bool)
    skeleton[30, 10:90] = True  # the line
    skeleton[22:30, 50] = True  # an 8-px spur
    pruned = prune_spurs(skeleton, length=12)
    assert not pruned[22:28, 50].any()  # spur gone
    assert pruned[30, 10:90].sum() >= 78  # line kept (end pixels regrown)


def test_normalise_width_has_no_spurs_from_jagged_polygons() -> None:
    label = np.zeros((120, 200), np.uint8)
    label[55:65, 10:190] = HEAD  # a 10-px-wide annotated line
    label[50:55, 60:63] = HEAD  # a 5-px jag in the annotation outline
    thin = normalise_width(label, width=5)
    assert not (thin[48:55, 55:70] == HEAD).any()
