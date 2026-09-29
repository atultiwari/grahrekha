# Multi-photo consistency (cross-camera), v0 segmenter

**Date:** 2026-09-30

**Setup:** 20 hands from `retest_v1` people. For each hand:
- **1 photo vs 1 photo:** a single rear-camera photo compared with a single front-camera photo.
- **3 photos vs 3 photos:** the median/majority of 3 rear photos compared with that of 3 front photos (`palm/aggregate.py`).

This is a **harder** test than Phase 1's same-camera retest.

**Reproduce:**

```bash
cd services/engine && uv run python -m grahrekha_engine.evaluation.multiphoto_eval ../../data
```

## Findings

- **Aggregating 3 photos helps where the noise is random.**
  - heart end zone: 0.68 → 0.90
  - fate present: 0.80 → 0.90
  - head start zone: 0.82 → 0.90
  - head present: 0.96 → 1.00
- **Hand-shape measures stay poor even with 3 photos** (0.45–0.55). Averaging removes random noise, so what remains is a **systematic difference between the front (selfie, wide-angle) and rear cameras**. Lens perspective changes finger and palm proportions.
- **Product rule:** capture with the rear camera only, and never compare hand shape across cameras.
- **Zone coverage drops slightly with aggregation** (0.33 → 0.27). The certainty rule for aggregated features requires a certain majority, which is deliberately strict.

## Results


Hands compared: 20

| Feature | 1 photo vs 1 photo | 3 photos vs 3 photos |
|---|---|---|
| heart.present | 0.93 | 0.95 |
| head.present | 0.96 | 1.00 |
| life.present | 0.93 | 0.95 |
| fate.present | 0.80 | 0.90 |
| heart.start_zone | 0.59 | 0.60 |
| head.start_zone | 0.82 | 0.90 |
| life.start_zone | 0.91 | 0.95 |
| fate.start_zone | 0.80 | 0.90 |
| heart.end_zone | 0.68 | 0.90 |
| head.end_zone | 0.62 | 0.70 |
| life.end_zone | 0.57 | 0.60 |
| fate.end_zone | 0.77 | 0.90 |
| head_life_joined | 0.71 | 0.70 |
| palm_shape | 0.50 | 0.55 |
| finger_length | 0.39 | 0.45 |
| element | 0.41 | 0.50 |
| index_vs_ring | 0.45 | 0.50 |

**Mean agreement:** 1 photo 0.70 → 3 photos 0.76 (target >= 0.85)
Zone coverage (certain endpoints): 1 photo 0.33, 3 photos 0.27
