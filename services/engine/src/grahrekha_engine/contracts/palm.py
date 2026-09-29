"""Palm feature contracts (docs/ARCHITECTURE.md §4.5). Units are palm lengths."""

from typing import Literal

from pydantic import Field

from grahrekha_engine.contracts import Contract

LineName = Literal["heart", "head", "life", "fate"]
Zone = Literal[
    "percussion",
    "under_index",
    "under_middle",
    "under_ring",
    "under_pinky",
    "thumb_index_edge",
    "wrist",
    "thenar",
    "hypothenar",
    "palm_centre",
]


class LineFeaturesV1(Contract):
    name: LineName
    present: bool
    source: Literal["model", "classical"] | None = None
    confidence: float = 0.0
    length: float = 0.0  # palm lengths
    start_zone: Zone | None = None
    end_zone: Zone | None = None
    # False when the endpoint lies within measurement noise of a zone boundary; rules
    # must not rely on an uncertain zone (test-retest, docs/eval/features-v1.md).
    start_zone_certain: bool = False
    end_zone_certain: bool = False
    curvature: float = 0.0  # max deviation from the chord / chord length (0 = straight)
    slope_deg: float = 0.0  # chord angle, y up, canonical left-palm layout
    breaks: int = 0
    gaps: list[float] = Field(default_factory=list)  # palm lengths
    sweep: float | None = None  # life line only: how far its arc reaches into the palm


class HandGeometryV1(Contract):
    palm_length_width_ratio: float
    finger_to_palm_ratio: float
    # Relative to the positives_v1 median, with a "medium" band as wide as measurement
    # noise, so a hand near the threshold is not flipped between classes by noise.
    palm_shape: Literal["square", "medium", "long"]
    finger_length: Literal["short", "medium", "long"]
    element: Literal["earth", "air", "fire", "water", "mixed"]  # "mixed" per Cheiro
    digit_ratio_2d4d: float  # from landmark joints; approximate (not crease-to-tip)
    index_vs_ring: Literal["index_longer", "ring_longer", "equal"]
    thumb_opening_deg: float


class PalmFeaturesV1(Contract):
    schema_version: Literal["palm_features.v1"] = "palm_features.v1"
    hand: Literal["left", "right"]  # physical hand, as declared or inferred
    mirrored: bool
    hand_geometry: HandGeometryV1
    lines: dict[LineName, LineFeaturesV1]
    head_life_joined: bool | None = None  # None when either line is absent
    pipeline: dict[str, str]


class GateIssueV1(Contract):
    code: str
    message: str


class GateReportV1(Contract):
    passed: bool
    reasons: list[GateIssueV1]
    warnings: list[GateIssueV1]
    metrics: dict[str, float]


class OverlayV1(Contract):
    """Everything needed to draw on the user's ORIGINAL photo (pixel coordinates)."""

    width: int
    height: int
    landmarks: list[tuple[float, float]]
    lines: dict[LineName, list[list[tuple[float, float]]]]  # line -> segments -> points


class PalmAnalysisV1(Contract):
    schema_version: Literal["palm_analysis.v1"] = "palm_analysis.v1"
    gate: GateReportV1
    features: PalmFeaturesV1 | None = None
    overlay: OverlayV1 | None = None
    feature_hash: str | None = None  # sha256 of the canonical features JSON
