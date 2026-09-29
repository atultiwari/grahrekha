"""Combine features from several photos of the same hand (Phase 2, D-015).

Pose varies between photos about as much as hands vary between people for some
measures (docs/eval/features-v1.md), so readings should rest on 2-3 photos:
- continuous values: median;
- categories (zones, classes, presence): strict majority; a tie is never guessed
  (zones become uncertain, palm/finger classes the neutral "medium", joins unknown);
- a zone is certain only if a strict majority of photos agree on it AND were certain.
"""

from collections import Counter
from collections.abc import Callable, Sequence
from statistics import median

from grahrekha_engine.contracts.palm import (
    HandGeometryV1,
    LineFeaturesV1,
    LineName,
    PalmFeaturesV1,
)
from grahrekha_engine.palm.features import element_of

LINES: tuple[LineName, ...] = ("heart", "head", "life", "fate")


def _majority[T](values: Sequence[T]) -> T | None:
    """Strict majority value, or None on a tie / no majority."""
    if not values:
        return None
    (top, count), *rest = Counter(values).most_common()
    if rest and rest[0][1] == count:
        return None
    return top if count * 2 > len(values) or not rest else None


def _mode_or[T](values: Sequence[T], fallback: T) -> T:
    winner = _majority(values)
    return fallback if winner is None else winner


def _zone(
    lines: Sequence[LineFeaturesV1],
    zone_of: Callable[[LineFeaturesV1], object],
    certain_of: Callable[[LineFeaturesV1], bool],
) -> tuple[object, bool]:
    zones = [zone_of(line) for line in lines]
    winner = _majority(zones)
    if winner is None:
        # Tie: keep the most common zone for display, but never treat it as certain.
        return Counter(zones).most_common(1)[0][0], False
    agreeing_certain = sum(1 for line in lines if zone_of(line) == winner and certain_of(line))
    return winner, agreeing_certain * 2 > len(lines)


def _aggregate_line(name: LineName, photos: Sequence[LineFeaturesV1]) -> LineFeaturesV1:
    present = [p for p in photos if p.present]
    if len(present) * 2 <= len(photos):
        return LineFeaturesV1(name=name, present=False)
    start_zone, start_certain = _zone(
        present, lambda p: p.start_zone, lambda p: p.start_zone_certain
    )
    end_zone, end_certain = _zone(present, lambda p: p.end_zone, lambda p: p.end_zone_certain)
    typical = min(present, key=lambda p: abs(p.length - median(q.length for q in present)))
    sweeps = [p.sweep for p in present if p.sweep is not None]
    return LineFeaturesV1(
        name=name,
        present=True,
        source=_mode_or([p.source for p in present], typical.source),
        confidence=round(median(p.confidence for p in present), 3),
        length=round(median(p.length for p in present), 3),
        start_zone=start_zone,
        end_zone=end_zone,
        start_zone_certain=start_certain,
        end_zone_certain=end_certain,
        curvature=round(median(p.curvature for p in present), 3),
        slope_deg=round(median(p.slope_deg for p in present), 1),
        breaks=round(median(p.breaks for p in present)),
        gaps=list(typical.gaps),
        sweep=round(median(sweeps), 3) if sweeps else None,
    )


def _aggregate_geometry(photos: Sequence[HandGeometryV1]) -> HandGeometryV1:
    palm_shape = _mode_or([g.palm_shape for g in photos], "medium")
    finger_length = _mode_or([g.finger_length for g in photos], "medium")
    return HandGeometryV1(
        palm_length_width_ratio=round(median(g.palm_length_width_ratio for g in photos), 3),
        finger_to_palm_ratio=round(median(g.finger_to_palm_ratio for g in photos), 3),
        palm_shape=palm_shape,
        finger_length=finger_length,
        element=element_of(palm_shape, finger_length),
        digit_ratio_2d4d=round(median(g.digit_ratio_2d4d for g in photos), 3),
        index_vs_ring=_mode_or([g.index_vs_ring for g in photos], "equal"),
        thumb_opening_deg=round(median(g.thumb_opening_deg for g in photos), 1),
    )


def aggregate_features(photos: Sequence[PalmFeaturesV1]) -> PalmFeaturesV1:
    if not photos:
        raise ValueError("at least one photo is required")
    joins = [p.head_life_joined for p in photos if p.head_life_joined is not None]
    return PalmFeaturesV1(
        hand=_mode_or([p.hand for p in photos], photos[0].hand),
        mirrored=_mode_or([p.mirrored for p in photos], photos[0].mirrored),
        hand_geometry=photos[0].hand_geometry
        if len(photos) == 1
        else _aggregate_geometry([p.hand_geometry for p in photos]),
        lines={
            name: photos[0].lines[name]
            if len(photos) == 1
            else _aggregate_line(name, [p.lines[name] for p in photos])
            for name in LINES
        },
        head_life_joined=_majority(joins) if len(joins) * 2 > len(photos) else None,
        pipeline=photos[0].pipeline | {"photos": str(len(photos))},
    )
