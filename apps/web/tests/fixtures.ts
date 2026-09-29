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

export function chartFixture() {
  return {
    schema_version: "astro_chart.v1",
    provider: "jyotishganit-0.1.3",
    ayanamsa: "true-chitrapaksha",
    timezone: "Asia/Kolkata",
    utc_offset_hours: 5.5,
    time_confidence: "exact",
    lagna_sign: "Leo",
    lagna_degree: 12.5,
    navamsa_lagna_sign: "Aries",
    planets: [
      {
        planet: "Moon",
        longitude: 100.5,
        sign: "Cancer",
        degree_in_sign: 10.5,
        navamsa_sign: "Scorpio",
        nakshatra: "Pushya",
        pada: 3,
        house: 12,
        retrograde: false,
      },
    ],
    moon_nakshatra: "Pushya",
    moon_nakshatra_uncertain: false,
    mahadashas: [{ lord: "Jupiter", start: "2020-01-01", end: "2036-01-01" }],
    current_mahadasha: "Jupiter",
    current_antardasha: "Saturn",
  } as const;
}

export function placesFixture() {
  return {
    schema_version: "places_response.v1",
    attribution: "GeoNames, geonames.org (CC BY 4.0)",
    places: [
      {
        geoname_id: 1253405,
        name: "Varanasi",
        region: "Uttar Pradesh",
        country: "IN",
        latitude: 25.31668,
        longitude: 83.01041,
        timezone: "Asia/Kolkata",
        population: 1164404,
      },
    ],
  } as const;
}

export function readingFixture() {
  return {
    schema_version: "astro_reading.v1",
    chart: chartFixture(),
    features: {
      schema_version: "astro_features.v1",
      time_confidence: "exact",
      moon_nakshatra_uncertain: false,
      lagna_sign: "Leo",
      planets: {
        Moon: { sign: "Cancer", house: 12, navamsa_sign: "Scorpio", retrograde: false },
      },
      mahadasha: { lord: "Jupiter", houses_ruled: [5, 8] },
      antardasha: { lord: "Saturn", houses_ruled: [6, 7] },
    },
    rules: {
      rulebase_version: "abc123",
      fired: [
        {
          id: "astro.jc.mahadasha_lord_rules_trikona",
          domain: "life_path_timing",
          polarity: "positive",
          strength: 2,
          statement: { en: "Supportive period." },
          source: { work: "Jataka Chandrika", locator: "Stanza V", edition: null, quote: "Lords of the 5th and 9th houses are always good" },
          status: "extracted",
          mapping_note: null,
          validity_blocker: null,
        },
      ],
    },
  } as const;
}
