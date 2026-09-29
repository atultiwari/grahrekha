import pytest

from grahrekha_engine.contracts.palm import HandGeometryV1, LineFeaturesV1, PalmFeaturesV1
from grahrekha_engine.palm.aggregate import aggregate_features


def _f(
    length: float, end: str, certain: bool, shape: str, joined: bool | None, present: bool = True
) -> PalmFeaturesV1:
    geometry = HandGeometryV1(
        palm_length_width_ratio=1.5,
        finger_to_palm_ratio=0.8,
        palm_shape=shape,
        finger_length="short",
        element="earth",
        digit_ratio_2d4d=0.98,
        index_vs_ring="equal",
        thumb_opening_deg=50,
    )
    lines = {n: LineFeaturesV1(name=n, present=False) for n in ("heart", "head", "life", "fate")}
    lines["heart"] = LineFeaturesV1(
        name="heart",
        present=present,
        source="model",
        length=length if present else 0.0,
        end_zone=end if present else None,
        end_zone_certain=certain,
    )
    return PalmFeaturesV1(
        hand="left",
        mirrored=False,
        hand_geometry=geometry,
        lines=lines,
        head_life_joined=joined,
        pipeline={"engine": "x"},
    )


def test_needs_at_least_one_photo() -> None:
    with pytest.raises(ValueError):
        aggregate_features([])


def test_single_photo_is_returned_unchanged_apart_from_provenance() -> None:
    one = _f(0.6, "under_middle", True, "square", True)
    out = aggregate_features([one])
    assert out.lines["heart"] == one.lines["heart"]
    assert out.pipeline["photos"] == "1"


def test_continuous_features_take_the_median() -> None:
    out = aggregate_features(
        [
            _f(0.5, "under_middle", True, "square", True),
            _f(0.9, "under_middle", True, "square", True),
            _f(0.6, "under_middle", True, "square", True),
        ]
    )
    assert out.lines["heart"].length == pytest.approx(0.6)


def test_categorical_features_take_the_majority() -> None:
    out = aggregate_features(
        [
            _f(0.6, "under_middle", True, "square", True),
            _f(0.6, "between_index_middle", True, "long", False),
            _f(0.6, "under_middle", True, "square", True),
        ]
    )
    assert out.lines["heart"].end_zone == "under_middle"
    assert out.hand_geometry.palm_shape == "square"
    assert out.head_life_joined is True


def test_zone_is_certain_only_with_a_certain_majority() -> None:
    mixed = aggregate_features(
        [
            _f(0.6, "under_middle", True, "square", True),
            _f(0.6, "under_middle", False, "square", True),
            _f(0.6, "between_index_middle", True, "square", True),
        ]
    )
    assert mixed.lines["heart"].end_zone == "under_middle"
    assert (
        mixed.lines["heart"].end_zone_certain is False
    )  # only 1 of 3 photos certain for the majority zone


def test_ties_are_uncertain_not_guessed() -> None:
    tie = aggregate_features(
        [
            _f(0.6, "under_middle", True, "square", True),
            _f(0.6, "between_index_middle", True, "long", None),
        ]
    )
    assert tie.lines["heart"].end_zone_certain is False
    assert (
        tie.hand_geometry.palm_shape == "medium"
    )  # tie between classes -> the neutral middle class
    assert tie.head_life_joined is None


def test_a_line_is_present_only_if_most_photos_see_it() -> None:
    out = aggregate_features(
        [
            _f(0.6, "under_middle", True, "square", True),
            _f(0, "under_middle", False, "square", True, present=False),
            _f(0, "under_middle", False, "square", True, present=False),
        ]
    )
    assert out.lines["heart"].present is False
