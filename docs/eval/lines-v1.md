# Line detection: per-line evaluation and the v1 segmenter (Phase 2)

**Date:** 2026-09-30

## Per-line ground truth

PLSU held-out masks (93 palms that pass the gate) are **human-drawn and complete**. Line identity (heart / head / life / fate) is derived automatically in `ml/src/grahrekha_ml/labels.py`:
1. The skeleton is split at junctions.
2. Each branch takes the class v0 supports along it.
3. An unsupported, central, near-vertical branch is the fate line.
4. Anything else is *ignored*.

**Caveat:** because identity comes partly from v0, these labels flatter v0 slightly. The line *extents* are human-drawn, though.

**Reproduce:**

```bash
cd ml && uv run python -m grahrekha_ml.per_line_eval ../data --segmenter v0
```

Tolerance: 2.5% of palm length.

## v0 baseline (per line)

| Line | Palms with line | Missed | False alarms | Recall | Precision |
|---|---|---|---|---|---|
| heart | 92 | 0 | 0 | 0.932 | 0.989 |
| head | 92 | 0 | 1 | 0.893 | 0.919 |
| life | 87 | 0 | 1 | 0.924 | 0.943 |
| fate | 20 | 10 | 37 | 0.277 | 0.233 |

The classical fate detector (used with v0) is poor when scored per line. It raises a false alarm on 37 of the 73 palms without an annotated fate line, and recovers only 28% of annotated fate lines.

## Where heart lines end (correction to Phase 1)

In Phase 1, the traced heart lines mostly ended "under the middle finger", and I blamed v0 truncation. The human-drawn lines show otherwise.

**Where the index-side end falls** (932 PLSU palms, canonical x):

| Percentile | x |
|---|---|
| p5 | 410 |
| p25 | 438 |
| p50 | 458 |
| p75 | 476 |
| p95 | 506 |

The index–middle gap centre is at 437. Heart lines **naturally end around the gap between the index and middle fingers**, which Cheiro treats as its own variant. The zones now include `between_index_middle`, defined anatomically as the gap centre ± a quarter of the knuckle spacing, i.e. [405.5, 468.5).

**Share of human-drawn ends in each zone:**

| Zone | Share |
|---|---|
| under index | 4% |
| between index and middle | 61% |
| under middle | 35% |

**Heart end-zone agreement** between the v0 trace and the human line: **72%** (66/92). `per_line_eval` prints this (index-side end of the trace vs of the human mask, same `zone_of`). The main confusion is human "between" versus v0 "under middle" (18), a mild shortfall rather than wholesale truncation.

**Target for approving heart end-zone rules:** ≥ 85% agreement.

## v1 (our own segmenter)

**Model:**
- U-Net with a ResNet-34 encoder, working in the canonical palm frame, with 5 classes (background, heart, head, life, fate).
- Trained for 30 epochs on MPS with CE + Dice + clDice loss. Fate palms were oversampled ×3 and the fate class weighted ×3.
- Best epoch 26 (validation Dice: heart 0.78, head 0.75, life 0.74, fate 0.45).
- Model card: `services/engine/models/cards/grahrekha-lines-v1.md`.
- The weights (`M9-grahrekha-lines-v1`, 98 MB ONNX) are built locally and **not distributed**, because PLSU has no licence. The engine's `ENGINE_SEGMENTER=auto` (the default) uses v1 when it is installed and v0 otherwise.
- The first run never learned fate (Dice 0). It is archived as `ml/runs/v1-abandoned-no-fate`.

**Reproduce:**

```bash
cd ml && uv run python -m grahrekha_ml.train_lines ../data --run v1 --epochs 30
cd ml && uv run python -m grahrekha_ml.export_onnx --run v1
cd ml && uv run python -m grahrekha_ml.per_line_eval ../data --segmenter v1
cd services/engine && uv run python -m grahrekha_engine.evaluation.lines_eval ../../data --segmenter v1
```

### Per line (same 93 held-out palms, tolerance 2.5%)

| Line | Recall v0 → **v1** | Precision v0 → **v1** | Missed v0 → v1 | False alarms v0 → v1 |
|---|---|---|---|---|
| heart | 0.932 → **0.976** | 0.989 → **0.982** | 0 → 0 | 0 → 1 |
| head | 0.893 → **0.947** | 0.919 → **0.944** | 0 → 0 | 1 → 1 |
| life | 0.924 → **0.945** | 0.943 → **0.925** | 0 → 1 | 1 → 3 |
| fate | 0.277 → **0.645** | 0.233 → **0.810** | 10 → 4 | 37 → 15 |

**Heart end-zone agreement:** 72% (66/92) → **88% (81/92)**, which clears the 85% target. The remaining confusions:
- human "under middle" vs v1 "between": 6 cases, with v1 now slightly overshooting;
- human "between" vs v1 "under index": 2 cases.

### Class-agnostic (comparable with Phase 1, `docs/eval/lines-v0.md`)

| Output (tolerance 2.5%) | v0 P / R / F1 | **v1 P / R / F1** |
|---|---|---|
| raw model (p > 0.5) | 0.964 / 0.789 / 0.856 | **0.971 / 0.931 / 0.947** |
| traced lines | 0.950 / 0.815 / 0.867 | **0.982 / 0.884 / 0.924** |
| traced + fate line | 0.934 / 0.843 / 0.877 | **0.973 / 0.921 / 0.942** |

Recall with the fate line is **0.921**, meeting the Phase 1 target (≥ 0.85) that v0 missed. v1 reports a fate line on 31/93 palms (v0: 47/93); PLSU annotates one on 20.

### Consistency (same-hand photos)

| Measure | v0 | v1 | Target |
|---|---|---|---|
| Test–retest mean categorical agreement (`retest_eval`) | 0.77 | **0.80** | ≥ 0.85 |
| Cross-camera multi-photo mean, 1 photo → 3 photos (`multiphoto_eval`, 20 hands) | 0.70 → 0.76 | 0.70 → 0.74 | ≥ 0.85 |

**Per feature (cross-camera, 1 photo):**
- **Better with v1:** heart end-zone 0.68 → **0.86** (3 photos: 0.95); head–life join 0.71 → 0.86; head end-zone 0.62 → 0.68.
- **Worse with v1:** head start-zone 0.82 → 0.66; life start-zone 0.91 → 0.68; life end-zone 0.57 → 0.48. v1 traces lines further towards the thumb edge and the wrist, so their endpoints now sit near zone boundaries (`thumb_index_edge` vs palm centre; `wrist`) and flip between photos.
- **Unchanged:** hand shape (0.39–0.50), because it comes from landmarks, not lines. The front/rear camera difference remains the main problem there (use the rear camera).

## Decision

- **v1 becomes the default where it is installed** (`ENGINE_SEGMENTER=auto`). It is better on every accuracy measure against human-drawn lines, and on test–retest.
- **Heart end-zone rules:** the validity blockers now say they are valid only with v1.
- **Head and life start-zone features:** their cross-camera consistency fell with v1. They should stay in the "unreliable" tier until the zone boundaries are revisited with the owner's own consented photos.
- **Still short of the consistency target (0.85):** the next levers are rear-camera-only capture, multi-photo aggregation by default, and zone boundaries that leave a margin around typical endpoints.

