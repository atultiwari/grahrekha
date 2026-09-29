import numpy as np
import pytest

from grahrekha_engine.palm.geometry import chirality, finger_spread, is_palm_facing, palm_length
from tests.palm.synthetic import detection, mirror_x, right_palm_points, rotate


def test_right_palm_has_negative_chirality() -> None:
    assert chirality(right_palm_points()) < 0


def test_mirroring_flips_chirality() -> None:
    assert chirality(mirror_x(right_palm_points())) > 0


@pytest.mark.parametrize("degrees", [0, 45, 90, 180, 270, -30])
def test_chirality_sign_is_rotation_invariant(degrees: float) -> None:
    assert chirality(rotate(right_palm_points(), degrees)) < 0


# Calibrated on 11K Hands + phone photos: palm-facing iff (label == right) == (chirality < 0).
@pytest.mark.parametrize(
    ("points_fn", "label", "expected"),
    [
        (right_palm_points, "right", True),  # right palm
        (lambda: mirror_x(right_palm_points()), "left", True),  # left palm
        (lambda: mirror_x(right_palm_points()), "right", False),  # right hand, back
        (right_palm_points, "left", False),  # left hand, back
    ],
)
def test_palm_facing_rule(points_fn, label, expected) -> None:  # type: ignore[no-untyped-def]
    assert is_palm_facing(detection(points_fn(), label)) is expected


def test_palm_length_scales_with_hand_size() -> None:
    small, big = palm_length(right_palm_points(0.5)), palm_length(right_palm_points(1.0))
    assert big == pytest.approx(2 * small)


def test_finger_spread_is_scale_invariant_and_detects_closed_fingers() -> None:
    open_hand = right_palm_points()
    assert finger_spread(open_hand) == pytest.approx(finger_spread(right_palm_points(0.3)))
    closed = open_hand.copy()
    closed[[8, 12, 16, 20]] = np.array([[560, 200], [530, 150], [500, 180], [470, 210]])
    assert finger_spread(closed) < finger_spread(open_hand)
