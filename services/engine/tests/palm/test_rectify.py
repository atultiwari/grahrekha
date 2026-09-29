import numpy as np
import pytest

from grahrekha_engine.palm.rectify import (
    CANONICAL_SIZE,
    TEMPLATE_INDICES,
    rectify,
    template_points,
)
from tests.palm.synthetic import detection, right_palm_points


def _pose(
    points: np.ndarray, degrees: float, scale: float, shift: tuple[float, float], mirror: bool
) -> np.ndarray:
    p = points.copy()
    if mirror:
        p[:, 0] = -p[:, 0]
    t = np.radians(degrees)
    r = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    out: np.ndarray = (p @ r.T) * scale + np.array(shift)
    return out


def _landmarks_from_template(
    degrees: float, scale: float, shift: tuple[float, float], mirror: bool
) -> np.ndarray:
    """A full 21-point array whose template landmarks are an exact similarity of the template."""
    full = np.zeros((21, 2))
    full[list(TEMPLATE_INDICES)] = template_points()
    return _pose(full, degrees, scale, shift, mirror)


@pytest.mark.parametrize(
    ("degrees", "scale", "mirror"),
    [(0, 1.0, False), (35, 0.6, False), (-120, 0.4, True), (90, 1.3, True)],
)
def test_recovers_known_pose_exactly(degrees: float, scale: float, mirror: bool) -> None:
    pts = _landmarks_from_template(degrees, scale, (400, 300), mirror)
    image = np.zeros((1200, 1200, 3), np.uint8)
    result = rectify(image, detection(pts, "left" if not mirror else "right"))

    assert result.fit_rms_px < 1e-6
    assert result.mirrored is mirror
    np.testing.assert_allclose(
        result.to_canonical(pts[list(TEMPLATE_INDICES)]), template_points(), atol=1e-6
    )


def test_round_trip_between_original_and_canonical() -> None:
    result = rectify(np.zeros((1000, 1000, 3), np.uint8), detection(right_palm_points()))
    pts = right_palm_points()
    np.testing.assert_allclose(result.to_original(result.to_canonical(pts)), pts, atol=1e-6)


def test_right_palm_is_mirrored_into_the_left_palm_frame() -> None:
    result = rectify(np.zeros((1000, 1000, 3), np.uint8), detection(right_palm_points()))
    assert result.mirrored
    canonical = result.to_canonical(right_palm_points())
    # Thumb base ends up left of the wrist in the canonical (left-palm) layout.
    assert canonical[1, 0] < canonical[0, 0]


def test_warped_image_places_pixels_at_template_positions() -> None:
    pts = _landmarks_from_template(20, 0.7, (500, 450), False)
    image = np.zeros((1000, 1000, 3), np.uint8)
    x, y = np.round(pts[9]).astype(int)
    image[y - 3 : y + 4, x - 3 : x + 4] = 255  # bright marker at the middle-finger MCP
    result = rectify(image, detection(pts, "left"))

    assert result.image.shape == (CANONICAL_SIZE, CANONICAL_SIZE, 3)
    ys, xs = np.nonzero(result.image[:, :, 0] > 128)
    tx, ty = template_points()[list(TEMPLATE_INDICES).index(9)]
    assert abs(xs.mean() - tx) < 2 and abs(ys.mean() - ty) < 2


def test_fit_residual_reports_unusual_hand_shapes() -> None:
    pts = _landmarks_from_template(0, 1.0, (300, 300), False)
    pts[17] += np.array([150.0, 0.0])  # pinky knuckle far out of place
    result = rectify(np.zeros((1000, 1000, 3), np.uint8), detection(pts, "left"))
    assert result.fit_rms_px > 20
