import type { PalmAnalysisV1, PalmFeaturesV1 } from "@grahrekha/contracts";

const absent = (name: "heart" | "head" | "life" | "fate") => ({
  name,
  present: false,
  source: null,
  confidence: 0,
  length: 0,
  start_zone: null,
  end_zone: null,
  start_zone_certain: false,
  end_zone_certain: false,
  curvature: 0,
  slope_deg: 0,
  breaks: 0,
  gaps: [],
  sweep: null,
});

export function featuresFixture(): PalmFeaturesV1 {
  return {
    schema_version: "palm_features.v1",
    hand: "left",
    mirrored: false,
    hand_geometry: {
      palm_length_width_ratio: 1.5,
      finger_to_palm_ratio: 0.8,
      palm_shape: "medium",
      finger_length: "medium",
      element: "mixed",
      digit_ratio_2d4d: 0.98,
      index_vs_ring: "equal",
      thumb_opening_deg: 50,
    },
    lines: { heart: absent("heart"), head: absent("head"), life: absent("life"), fate: absent("fate") },
    head_life_joined: null,
    pipeline: { engine: "0.1.0" },
  };
}

export function analysisFixture(): PalmAnalysisV1 {
  return {
    schema_version: "palm_analysis.v1",
    gate: { passed: true, reasons: [], warnings: [], metrics: { sharpness: 20 } },
    features: featuresFixture(),
    overlay: { width: 800, height: 600, landmarks: [[10, 20]], lines: { heart: [[[1, 2], [3, 4]]] } },
    feature_hash: "f".repeat(64),
  };
}
