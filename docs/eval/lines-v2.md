# Line detection v2: fine-tuned on phone photos (Phase 2b)

**Date:** 2026-09-30
**Decision:** v2 is the default where installed (`ENGINE_SEGMENTER=auto` picks the newest installed model). `ENGINE_SEGMENTER=v1` is still available.
**Model card:** `services/engine/models/cards/grahrekha-lines-v2.md`.

## Why v2

v1 was trained on PLSU only. That means:
- the photos are scanner-like 11K Hands images;
- line identities were derived partly from v0.

Real users send phone photos. Four Roboflow Universe sets (D24, fetched with the owner's key) add human-labelled lines on phone and web photos. From these we also built the first test set with **human line identities on phone photos**.

## Data (`ml/src/grahrekha_ml/build_roboflow_dataset.py`)

| Step | Count |
|---|---|
| Written to `lines_v2/train` | 817 |
| Held out as `lines_v2/eval_phone` (20% of the phone set, by file name) | 68 (fate line on 40) |
| Rejected by the quality gate | 444 |
| **Near-duplicates of PLSU eval images (dropped, leakage guard)** | **109** |
| Augmentation copies within a set (dropped) | 269 |

Conversion problems found and fixed before training:
- **EXIF rotation.**
  - Roboflow polygons are in the raw pixel frame, but 48 of 120 phone photos carry an EXIF rotation.
  - Reading EXIF-rotated pixels left 159 labels empty or misaligned.
  - The builder now reads raw pixels.
- **Spurs.**
  - Skeletons of jagged polygon outlines grew side spurs.
  - Labels are now pruned and redrawn at PLSU's stroke width (6.4 px at 512).
- **Classes.**
  - Minor creases (marriage, sun, girdle, etc.) become IGNORE, so the model is neither rewarded nor penalised on them.

The `docseg/palmistry-kp` keypoint set (7,112 images) was downloaded but **not used**. It marks a fate line on 7,094 of 7,112 images, which looks forced, and its images are small (320 px). It needs a quality check first.

## Training

Fine-tuned from v1:

```bash
cd ml && uv run python -m grahrekha_ml.train_lines ../data --run v2 --epochs 15 \
    --init-from v1 --extra-train lines_v2/train --lr 1e-4
cd ml && uv run python -m grahrekha_ml.export_onnx --run v2
```

- Best epoch 10 (PLSU validation Dice: heart 0.78, head 0.75, life 0.73, fate 0.45).
- About 8.5 min per epoch on MPS.

## Results

### Phone photos, human line identities (`eval_phone`, 68 palms)

Raw model output (p > 0.5), tolerance 2.5% of palm length:

```bash
cd ml && uv run python -m grahrekha_ml.eval_canonical ../data \
    --model ../services/engine/models/weights/M9-grahrekha-lines-v2/model.onnx
```

| Line | Recall v1 → **v2** | Precision v1 → **v2** | Missed v1 → v2 | False alarms v1 → v2 |
|---|---|---|---|---|
| heart | 0.968 → **0.983** | 0.945 → **0.952** | 0 → 0 | 0 → 0 |
| head | 0.959 → **0.966** | 0.869 → **0.924** | 1 → 0 | 0 → 0 |
| life | 0.820 → **0.871** | 0.928 → 0.925 | 1 → 0 | 0 → 0 |
| fate | 0.342 → **0.694** | 0.849 → 0.835 | 15 → **3** | 4 → **10** |

This is the headline result: v2 finds fate lines on phone photos about **twice as often**, with better life and head tracing. The cost is more fate false alarms: 10 of the 28 palms without an annotated fate line.

### PLSU (same 93 held-out palms as before, full pipeline)

| Measure | v1 | **v2** |
|---|---|---|
| Per-line recall (heart / head / life / fate) | 0.976 / 0.947 / 0.945 / 0.645 | 0.970 / 0.952 / 0.944 / 0.577 |
| Fate missed / false alarms | 4 / 15 | 6 / 14 |
| **Heart end-zone agreement** | 88% (81/92) | **92% (85/92)** |
| Class-agnostic traced + fate, P / R | 0.973 / 0.921 | 0.974 / 0.916 |

Note: PLSU's fate labels come partly from v0-derived identities (`lines-v1.md`). The phone set's labels are fully human.

### Consistency

| Measure | v1 | v2 | Target |
|---|---|---|---|
| Test–retest mean categorical agreement | 0.80 | 0.80 | ≥ 0.85 |
| Cross-camera, 1 photo → 3 photos (20 hands) | 0.70 → 0.74 | 0.68 → 0.73 | ≥ 0.85 |

**Per feature, cross-camera, 1 photo (v1 → v2):**
- **Better:**
  - line presence: heart, head and life are now always found (1.00);
  - head start-zone 0.66 → 0.73;
  - life start-zone 0.68 → 0.70.
- **Worse:**
  - heart end-zone 0.86 → 0.75 (3 photos: 0.95 → 0.85);
  - fate presence 0.82 → 0.70;
  - head–life join 0.86 → 0.75.

## Reading the trade-off

- **Accuracy against human labels:** v2 is better where it matters (phone photos) and equal on PLSU, apart from fate recall on 20 palms. Heart end-zone accuracy improves further.
- **Cross-camera consistency:** slightly lower. It rests on only 20 hands, and no rule-relevant feature crosses a threshold because of it. Heart end-zone rules still require a *certain* zone, and multi-photo aggregation raises heart end-zone agreement to 0.85.
- **Fate:** v2 is more sensitive and less specific on phone photos. **No fate rules exist yet.** Before adding any, calibrate the fate threshold on `eval_phone` (for example, require p > 0.6, or a minimum fate length).

## Next

1. **Calibrate the fate threshold** on `eval_phone`.
2. **Check `docseg/palmistry-kp` quality.** Sample 50 images and look at whether the fate lines are real. If they are, 7k more line-keypoint images become available.
3. **Evaluate on the owner's own consented photos** once collected. This is the truest test.
