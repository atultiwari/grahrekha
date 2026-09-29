import numpy as np
import pytest

from grahrekha_engine.palm.features import hand_geometry, line_features, zone_of
from grahrekha_engine.palm.rectify import PALM_UNIT_PX
from grahrekha_engine.palm.segment.postprocess import LineTrace
from tests.palm.synthetic import right_palm_points


def _trace(
    points: list[tuple[float, float]], gaps: list[float] | None = None, conf: float = 0.8
) -> LineTrace:
    arr = np.array(points, dtype=float)
    length = float(np.linalg.norm(np.diff(arr, axis=0), axis=1).sum())
    return LineTrace(segments=[arr], gaps_px=gaps or [], confidence=conf, length_px=length)


@pytest.mark.parametrize(
    ("point", "zone"),
    [
        ((780, 480), "percussion"),
        ((390, 470), "under_index"),
        ((437, 470), "between_index_middle"),
        ((500, 470), "under_middle"),
        ((600, 470), "under_ring"),
        ((700, 470), "under_pinky"),
        ((360, 480), "thumb_index_edge"),
        ((500, 860), "wrist"),
        ((380, 700), "thenar"),
        ((680, 700), "hypothenar"),
        ((520, 650), "palm_centre"),
    ],
)
def test_zones_follow_the_canonical_palm_layout(point: tuple[int, int], zone: str) -> None:
    assert zone_of(np.array(point, dtype=float)) == zone


def test_heart_line_is_oriented_from_percussion_to_index() -> None:
    f = line_features("heart", _trace([(395, 460), (600, 480), (790, 500)]))
    assert f.start_zone == "percussion"
    assert f.end_zone == "under_index"
    assert f.length == pytest.approx(397 / PALM_UNIT_PX, rel=0.02)


def test_life_line_runs_top_down_and_reports_its_sweep() -> None:
    tight = line_features("life", _trace([(370, 480), (400, 650), (420, 820)]))
    wide = line_features("life", _trace([(370, 480), (520, 650), (430, 830)]))
    assert tight.start_zone == "thumb_index_edge" and tight.end_zone == "wrist"
    assert wide.sweep is not None and tight.sweep is not None
    assert wide.sweep > tight.sweep


def test_straight_vs_curved_and_breaks() -> None:
    straight = line_features("head", _trace([(380, 520), (560, 540), (720, 560)]))
    curved = line_features("head", _trace([(380, 520), (540, 620), (660, 760)]))
    broken = line_features("head", _trace([(380, 520), (720, 560)], gaps=[60.0]))
    assert straight.curvature < curved.curvature
    assert broken.breaks == 1 and straight.breaks == 0
    assert broken.gaps == [pytest.approx(60 / PALM_UNIT_PX, abs=1e-3)]  # rounded to 3 dp


def test_absent_line() -> None:
    f = line_features("fate", None)
    assert not f.present and f.length == 0 and f.start_zone is None


def test_hand_geometry_from_original_landmarks() -> None:
    g = hand_geometry(right_palm_points())
    assert g.palm_shape in ("square", "long")
    assert g.finger_length in ("short", "long")
    assert g.element in ("earth", "air", "fire", "water")
    assert 0.8 < g.digit_ratio_2d4d < 1.3
    assert g.index_vs_ring in ("index_longer", "ring_longer", "equal")
    assert 0 < g.thumb_opening_deg < 120


def test_element_follows_benham_cheiro_quadrants() -> None:
    from grahrekha_engine.palm.features import element_of

    assert element_of("square", "short") == "earth"
    assert element_of("square", "long") == "air"
    assert element_of("long", "short") == "fire"
    assert element_of("long", "long") == "water"


def test_head_and_life_joined_at_the_start() -> None:
    from grahrekha_engine.palm.features import head_life_joined

    life = _trace([(370, 480), (400, 650), (420, 820)])
    joined_head = _trace([(375, 490), (560, 540), (720, 560)])
    separate_head = _trace([(470, 560), (600, 580), (720, 590)])
    assert head_life_joined(joined_head, life) is True
    assert head_life_joined(separate_head, life) is False
    assert head_life_joined(None, life) is None


@pytest.mark.parametrize(
    ("ratio", "shape"),
    [(1.40, "square"), (1.50, "square"), (1.57, "medium"), (1.64, "long"), (1.80, "long")],
)
def test_palm_shape_has_a_noise_aware_middle_band(ratio: float, shape: str) -> None:
    from grahrekha_engine.palm.features import classify_palm_shape

    assert classify_palm_shape(ratio) == shape


@pytest.mark.parametrize(
    ("ratio", "length"),
    [(0.75, "short"), (0.78, "short"), (0.84, "medium"), (0.90, "long"), (0.95, "long")],
)
def test_finger_length_has_a_noise_aware_middle_band(ratio: float, length: str) -> None:
    from grahrekha_engine.palm.features import classify_finger_length

    assert classify_finger_length(ratio) == length


def test_element_is_mixed_unless_both_traits_are_clear() -> None:
    from grahrekha_engine.palm.features import element_of

    assert element_of("medium", "short") == "mixed"
    assert element_of("square", "medium") == "mixed"


@pytest.mark.parametrize(
    ("ratio", "comparison"),
    [(0.94, "ring_longer"), (0.98, "equal"), (1.03, "equal"), (1.06, "index_longer")],
)
def test_index_vs_ring_needs_a_difference_beyond_measurement_noise(
    ratio: float, comparison: str
) -> None:
    from grahrekha_engine.palm.features import compare_index_ring

    assert compare_index_ring(ratio) == comparison


def test_zone_certainty_depends_on_distance_to_a_boundary() -> None:
    from grahrekha_engine.palm.features import zone_is_certain

    assert zone_is_certain(np.array([512.0, 470.0]))  # middle of "under_middle"
    assert not zone_is_certain(np.array([470.0, 470.0]))  # at the gap/middle boundary


def test_line_features_flag_uncertain_endpoints() -> None:
    f = line_features("heart", _trace([(470, 470), (600, 480), (790, 500)]))
    assert f.start_zone_certain is True  # deep in the percussion
    assert f.end_zone_certain is False  # right at the gap/middle boundary
