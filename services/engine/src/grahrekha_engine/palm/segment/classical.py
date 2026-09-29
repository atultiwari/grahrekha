"""Classical (non-learned) crease detection in the canonical palm frame.

Used where the v0 model has no class (the fate line) and later as a cross-check.
Frangi ridge filter (creases are dark valleys) -> minimal-cost path between anatomical
zones -> accept only if the path stays on strong ridges for most of its length.
"""

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray
from skimage.filters import frangi
from skimage.graph import MCP_Geometric

from grahrekha_engine.palm.image_io import RGBImage
from grahrekha_engine.palm.rectify import CANONICAL_SIZE, template_points
from grahrekha_engine.palm.segment.postprocess import LineTrace

_WORK = 512  # ridge filtering runs at half resolution for speed
_SCALE = CANONICAL_SIZE / _WORK


@dataclass(frozen=True)
class FateConfig:
    # Canonical-frame zones (template: wrist (500, 880), middle MCP (500, 320)).
    start_y: int = 845  # just above the wrist creases
    end_y: int = 430  # below the middle-finger mount
    x_range: tuple[int, int] = (430, 570)
    ridge_quantile: float = 0.90  # "on a ridge" = above this quantile of the palm's ridges
    # Fraction of the path that must be on a ridge. Calibrated on PLSU (lines_eval_v1):
    # at >= 0.85, 47/93 palms get a fate line and 81% of those paths lie mostly on an
    # annotated line (vs 61% at 0.70). Precision is favoured: reporting a fate line
    # that is not there is worse than "no clear fate line" (docs/eval/lines-v0.md).
    min_on_ridge: float = 0.85


def palm_mask(size: int = CANONICAL_SIZE) -> NDArray[np.bool_]:
    """Palm polygon (wrist, thumb base, knuckles) in the canonical frame at `size`."""
    polygon = template_points() * (size / CANONICAL_SIZE)
    mask = np.zeros((size, size), np.uint8)
    cv2.fillPoly(mask, [polygon.round().astype(np.int32)], 255)
    result: NDArray[np.bool_] = mask > 0
    return result


def ridge_map(image: RGBImage) -> NDArray[np.float32]:
    """Dark-crease ridge strength (Frangi), canonical resolution."""
    small = cv2.resize(image, (_WORK, _WORK), interpolation=cv2.INTER_AREA)
    lightness = cv2.cvtColor(small, cv2.COLOR_RGB2LAB)[:, :, 0]
    lightness = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lightness)
    ridge = frangi(
        lightness.astype(np.float64) / 255.0, sigmas=(1.0, 1.5, 2.0, 3.0), black_ridges=True
    )
    full = cv2.resize(ridge.astype(np.float32), (CANONICAL_SIZE, CANONICAL_SIZE))
    result: NDArray[np.float32] = full.astype(np.float32)
    return result


def detect_fate_line(image: RGBImage, config: FateConfig | None = None) -> LineTrace | None:
    cfg = config or FateConfig()
    ridge = cv2.resize(ridge_map(image), (_WORK, _WORK), interpolation=cv2.INTER_AREA)
    inside = palm_mask(_WORK)
    values = ridge[inside]
    if values.size == 0 or float(values.max()) <= 0:
        return None
    on_ridge_level = float(np.quantile(values, cfg.ridge_quantile))
    if on_ridge_level <= 0:
        return None

    strength = np.clip(ridge / (on_ridge_level * 2), 0, 1)
    cost = 1.0 / (strength + 0.05)
    cost[~inside] = 1e3

    x0, x1 = (round(v / _SCALE) for v in cfg.x_range)
    starts = [(round(cfg.start_y / _SCALE), x) for x in range(x0, x1 + 1, 3)]
    ends = [(round(cfg.end_y / _SCALE), x) for x in range(x0, x1 + 1, 3)]
    mcp = MCP_Geometric(cost, fully_connected=True)
    costs, _ = mcp.find_costs(starts, ends)
    best_end = min(ends, key=lambda p: costs[p])
    path = np.array(mcp.traceback(best_end))  # (y, x), from a start to the end

    on_ridge = float((ridge[path[:, 0], path[:, 1]] >= on_ridge_level).mean())
    if on_ridge < cfg.min_on_ridge:
        return None
    points = np.stack([path[:, 1], path[:, 0]], axis=1).astype(np.float64) * _SCALE
    approx = cv2.approxPolyDP(points.astype(np.float32).reshape(-1, 1, 2), 1.5, False)
    polyline = approx.reshape(-1, 2).astype(np.float64)
    length = float(np.linalg.norm(np.diff(polyline, axis=0), axis=1).sum())
    return LineTrace(segments=[polyline], gaps_px=[], confidence=on_ridge, length_px=length)
