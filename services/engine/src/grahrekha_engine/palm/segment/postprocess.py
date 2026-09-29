"""Turn a line-probability map into an ordered line trace (docs/ARCHITECTURE.md §4.4).

hysteresis threshold -> drop specks -> skeletonise -> longest path per component
(removes side spurs) -> link nearby fragments of the same line, recording the gaps
(a "broken" line is meaningful in palmistry, so fragments are kept, not merged).
"""

from collections import deque
from dataclasses import dataclass, field

import cv2
import numpy as np
from numpy.typing import NDArray
from skimage.filters import apply_hysteresis_threshold
from skimage.morphology import remove_small_objects, skeletonize

Polyline = NDArray[np.float64]  # (N, 2) ordered x, y points
_NEIGHBOURS = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)]


@dataclass(frozen=True)
class PostprocessConfig:
    high: float = 0.5  # a line must reach this probability somewhere...
    low: float = 0.3  # ...and extends while above this
    min_component_px: int = 150  # specks smaller than this (area) are dropped
    min_path_px: float = 40.0  # skeleton paths shorter than this are dropped
    max_gap_px: float = 120.0  # fragments closer than this are the same, broken line
    simplify_px: float = 1.0  # output polyline tolerance


@dataclass(frozen=True)
class LineTrace:
    segments: list[Polyline]  # ordered fragments, in canvas pixels
    gaps_px: list[float] = field(default_factory=list)  # distance between fragments
    confidence: float = 0.0  # mean probability along the traced path
    length_px: float = 0.0  # traced length, excluding gaps


def _longest_path(skeleton: NDArray[np.bool_]) -> list[tuple[int, int]]:
    """Longest geodesic path through a skeleton component (double BFS), as (y, x)."""
    pixels = set(zip(*np.nonzero(skeleton), strict=True))
    if not pixels:
        return []

    def bfs(
        start: tuple[int, int],
    ) -> tuple[tuple[int, int], dict[tuple[int, int], tuple[int, int]]]:
        parents: dict[tuple[int, int], tuple[int, int]] = {start: start}
        queue, last = deque([start]), start
        while queue:
            last = queue.popleft()
            y, x = last
            for dy, dx in _NEIGHBOURS:
                n = (y + dy, x + dx)
                if n in pixels and n not in parents:
                    parents[n] = last
                    queue.append(n)
        return last, parents

    far, _ = bfs(next(iter(sorted(pixels))))
    end, parents = bfs(far)
    path = [end]
    while path[-1] != far:
        path.append(parents[path[-1]])
    return path


def _length(poly: Polyline) -> float:
    return float(np.linalg.norm(np.diff(poly, axis=0), axis=1).sum()) if len(poly) > 1 else 0.0


@dataclass(frozen=True)
class _Fragment:
    points: Polyline
    confidence: float
    length: float


def _fragments(prob: NDArray[np.float32], cfg: PostprocessConfig) -> list[_Fragment]:
    mask = apply_hysteresis_threshold(prob, cfg.low, cfg.high)
    # max_size removes objects <= the value (skimage 0.26+), i.e. area < min_component_px.
    mask = remove_small_objects(mask, max_size=cfg.min_component_px - 1)
    count, labels = cv2.connectedComponents(mask.astype(np.uint8), connectivity=8)
    fragments = []
    for label in range(1, count):
        path = _longest_path(skeletonize(labels == label))
        if len(path) < 2:
            continue
        ys, xs = np.array(path).T
        raw = np.stack([xs, ys], axis=1).astype(np.float64)
        # Measure along the simplified polyline: summing the skeleton's pixel staircase
        # overstates curve length by ~5% (e.g. 990px measured for a 942px arc).
        points = _simplify(raw, cfg.simplify_px)
        length = _length(points)
        if length < cfg.min_path_px:
            continue
        fragments.append(_Fragment(points, float(prob[ys, xs].mean()), length))
    return fragments


def _simplify(points: Polyline, tolerance: float) -> Polyline:
    approx = cv2.approxPolyDP(points.astype(np.float32).reshape(-1, 1, 2), tolerance, False)
    result: Polyline = approx.reshape(-1, 2).astype(np.float64)
    return result


def trace_line(
    prob: NDArray[np.float32], config: PostprocessConfig | None = None
) -> LineTrace | None:
    cfg = config or PostprocessConfig()
    fragments = sorted(_fragments(prob, cfg), key=lambda f: f.length * f.confidence, reverse=True)
    if not fragments:
        return None

    chain = [fragments[0]]
    gaps: list[float] = []
    remaining = fragments[1:]
    linked = True
    while linked and remaining:
        linked = False
        head, tail = chain[0].points[0], chain[-1].points[-1]
        best: tuple[float, int, bool, bool] | None = None  # gap, index, at_tail, reverse
        for i, frag in enumerate(remaining):
            start, end = frag.points[0], frag.points[-1]
            options = [
                (float(np.linalg.norm(start - tail)), i, True, False),
                (float(np.linalg.norm(end - tail)), i, True, True),
                (float(np.linalg.norm(end - head)), i, False, False),
                (float(np.linalg.norm(start - head)), i, False, True),
            ]
            candidate = min(options)
            if candidate[0] <= cfg.max_gap_px and (best is None or candidate < best):
                best = candidate
        if best is not None:
            gap, index, at_tail, reverse = best
            frag = remaining.pop(index)
            points = frag.points[::-1] if reverse else frag.points
            piece = _Fragment(points, frag.confidence, frag.length)
            if at_tail:
                chain.append(piece)
                gaps.append(gap)
            else:
                chain.insert(0, piece)
                gaps.insert(0, gap)
            linked = True

    total = sum(f.length for f in chain)
    return LineTrace(
        segments=[f.points for f in chain],
        gaps_px=gaps,
        confidence=sum(f.confidence * f.length for f in chain) / total,
        length_px=total,
    )
