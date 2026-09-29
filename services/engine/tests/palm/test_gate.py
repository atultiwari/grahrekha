import cv2
import numpy as np
import pytest

from grahrekha_engine.palm.gate import GateConfig, evaluate_gate
from grahrekha_engine.palm.geometry import finger_to_palm_ratio
from grahrekha_engine.palm.image_io import RGBImage
from tests.palm.synthetic import detection, mirror_x, right_palm_points

RNG = np.random.default_rng(0)


def textured(size: int = 1000, mean: int = 150, noise: int = 40) -> RGBImage:
    """A sharp, mid-brightness image: stands in for a well-lit palm with visible creases."""
    return np.clip(RNG.normal(mean, noise, (size, size, 3)), 0, 255).astype(np.uint8)


def reasons(result) -> set[str]:  # type: ignore[no-untyped-def]
    return {r.code for r in result.reasons}


def test_good_palm_passes() -> None:
    result = evaluate_gate(textured(), [detection(right_palm_points())])
    assert result.passed, result.reasons
    assert result.reasons == []
    assert result.metrics["palm_length_ratio"] > 0


def test_no_hand() -> None:
    result = evaluate_gate(textured(), [])
    assert not result.passed and reasons(result) == {"NO_HAND"}


def test_multiple_hands() -> None:
    dets = [detection(right_palm_points()), detection(mirror_x(right_palm_points()), "left")]
    assert "MULTIPLE_HANDS" in reasons(evaluate_gate(textured(), dets))


def test_back_of_hand() -> None:
    back = detection(mirror_x(right_palm_points()), "right")
    assert "BACK_OF_HAND" in reasons(evaluate_gate(textured(), [back]))


def test_hand_too_small() -> None:
    tiny = detection(right_palm_points(scale=0.25))
    assert "HAND_TOO_SMALL" in reasons(evaluate_gate(textured(), [tiny]))


def test_cropped_when_key_landmarks_leave_the_frame() -> None:
    shifted = detection(right_palm_points(offset=(0, 200)))  # wrist at y=1100 in a 1000px image
    assert "CROPPED" in reasons(evaluate_gate(textured(), [shifted]))


def test_implausibly_short_fingers_are_not_a_palm() -> None:
    # MediaPipe fits a hand skeleton onto foot soles; toes are short relative to the sole.
    pts = right_palm_points()
    for mcp, tip in ((5, 8), (9, 12), (13, 16), (17, 20)):
        for j in range(mcp + 1, tip + 1):
            pts[j] = pts[mcp] + (pts[j] - pts[mcp]) * 0.35
    assert "NOT_A_PALM" in reasons(evaluate_gate(textured(), [detection(pts)]))


def test_finger_to_palm_ratio_of_a_normal_hand() -> None:
    assert finger_to_palm_ratio(right_palm_points()) > 0.8


def test_wrist_point_slightly_outside_frame_is_tolerated() -> None:
    # MediaPipe's wrist point sits below the palm heel; 30px out with a ~380px palm is fine.
    result = evaluate_gate(textured(), [detection(right_palm_points(offset=(0, 130)))])
    assert "CROPPED" not in reasons(result)


def test_fingers_closed() -> None:
    pts = right_palm_points()
    pts[[8, 12, 16, 20]] = np.array([[560, 200], [530, 150], [500, 180], [470, 210]])
    assert "FINGERS_CLOSED" in reasons(evaluate_gate(textured(), [detection(pts)]))


def test_blurry() -> None:
    blurred: RGBImage = cv2.GaussianBlur(textured(), (0, 0), sigmaX=12).astype(np.uint8)
    assert "BLURRY" in reasons(evaluate_gate(blurred, [detection(right_palm_points())]))


@pytest.mark.parametrize(("mean", "code"), [(15, "TOO_DARK"), (250, "OVEREXPOSED")])
def test_exposure(mean: int, code: str) -> None:
    image = textured(mean=mean, noise=5)
    assert code in reasons(evaluate_gate(image, [detection(right_palm_points())]))


def test_declared_hand_disagreement_is_a_warning_not_a_rejection() -> None:
    result = evaluate_gate(textured(), [detection(right_palm_points())], declared_hand="left")
    assert result.passed
    assert "HANDEDNESS_UNCERTAIN" in {w.code for w in result.warnings}


def test_thresholds_are_configurable() -> None:
    strict = GateConfig(min_palm_length_ratio=0.9)
    assert "HAND_TOO_SMALL" in reasons(
        evaluate_gate(textured(), [detection(right_palm_points())], config=strict)
    )


def test_every_reason_has_user_facing_advice() -> None:
    result = evaluate_gate(textured(), [])
    assert all(r.message for r in result.reasons)
