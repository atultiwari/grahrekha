# Palm features v1: reliability (Phase 1D)

**Date:** 2026-09-29

**Question:** does the same hand, photographed again, give the same features? Readings are only as trustworthy as the features they are built on.

**Data:** `retest_v1`, 20 groups of 3 photos of the same hand. Each group is the same person, hand and phone; only the background changes. The people in it are not used anywhere else.

**Reproduce:**

```bash
cd services/engine && uv run python -m grahrekha_engine.evaluation.retest_eval ../../data
```

## Where the noise comes from

| Measure | Same photo, re-measured (detector jitter) | Different photos of the same hand | Spread between people (IQR) |
|---|---|---|---|
| Palm length / width | 0.022 | 0.046 | 1.50–1.64 |
| Finger / palm length | 0.009 | 0.034 | 0.80–0.89 |

**Most of the within-hand noise is real pose variation** between photos (finger flexion, hand tilt), not landmark jitter. Averaging repeated detections would barely help.

The noise is **comparable to the differences between people**. So hand-shape classes (square/long palm, short/long fingers, element) **cannot be assigned reliably from a single photo**, whatever the thresholds.

## Mitigations built in

- **"Medium" band for palm shape and finger length.** Each gets a middle band as wide as the measurement noise, and element becomes "mixed" unless both are clear.
- **Zone certainty.** Each line endpoint's zone is flagged *certain* only if moving it by the measured endpoint noise (0.05 palm length) cannot change the zone. Rules may only use certain zones.

## Results (rules' view: zone counts only when certain)

| Feature | Pairwise agreement |
|---|---|
| heart.present | 0.88 |
| head.present | 0.97 |
| life.present | 0.90 |
| fate.present | 0.68 |
| heart.start_zone | 0.78 |
| head.start_zone | 0.80 |
| life.start_zone | 0.97 |
| fate.start_zone | 0.68 |
| heart.end_zone | 0.85 |
| head.end_zone | 0.77 |
| life.end_zone | 0.70 |
| fate.end_zone | 0.78 |
| head_life_joined | 0.72 |
| palm_shape | 0.57 |
| finger_length | 0.68 |
| element | 0.72 |
| index_vs_ring | 0.62 |

**Mean categorical agreement: 0.77** (target >= 0.85)
Zone coverage (endpoints with a certain zone): 0.32

| Length | Mean within-group coefficient of variation |
|---|---|
| heart.length | 0.03 |
| head.length | 0.10 |
| life.length | 0.07 |

Analysis latency (per photo, this machine): p50 0.45s, p95 0.47s

## Reliability tiers for the rule base (decision D-015)

| Tier | Features (pairwise agreement) | Use in rules |
|---|---|---|
| **Reliable** | head present (0.97), life start zone (0.97), life present (0.90), heart present (0.88), heart end zone (0.85); line lengths (within-hand CV 3–10%) | Yes. Length rules use buckets much wider than 10%. |
| **Moderate** | head start zone (0.80), heart start zone (0.78), fate end zone (0.78), head end zone (0.77) | Yes, but only when the zone is certain, and phrased softly |
| **Experimental** | head–life joined (0.72), element (0.72), life end zone (0.70), finger length (0.68), fate present (0.68), index vs ring (0.62), palm shape (0.57) | Not in production readings. Allowed only in the research/study arm, labelled experimental. |

## Next steps

- **Multiple photos per hand (Phase 5 product).** Ask for 2–3 photos and use the median of each feature. That reduces pose noise by about √3, which should move several experimental features into the moderate tier. Re-measure afterwards.
- **Capture guidance.** Ask for a flat hand, the camera parallel to the palm, and fingers relaxed and slightly apart. This targets the dominant noise source (pose).
- **Retest on the owner's own phone photos** once collected. `retest_v1` is small (20 groups).
