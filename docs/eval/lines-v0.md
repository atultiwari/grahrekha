# Line detection v0: evaluation (Phase 1C)

**Date:** 2026-09-29

**Pipeline:** quality gate → canonical palm frame → v0 segmenter (heart / head / life) → post-processing into ordered traces → classical fate-line detector.

**Data:** PLSU held-out split `lines_eval_v1` (100 images). PLSU marks lines **without saying which line is which**, so this is a *class-agnostic* score: did we find the palm's lines? Per-line accuracy needs line-labelled data (Roboflow sets or our own annotation, Phase 2).

**Metric:** tolerance-based precision and recall on 1-px skeletons. A pixel counts as matched if the other set has a pixel within the tolerance. This is the standard way to score thin curvilinear structures.

**Reproduce:**

```bash
cd services/engine && uv run python -m grahrekha_engine.evaluation.lines_eval ../../data
```

## Headline (2.5% of palm length ≈ 12 px on a typical photo)

| Output | Precision | Recall | F1 |
|---|---|---|---|
| Raw model (p > 0.5) | 0.964 | 0.789 | 0.856 |
| Traced lines (post-processed) | 0.950 | 0.815 | 0.867 |
| **Traced + classical fate line** (shipped config) | **0.934** | **0.843** | **0.877** |

- 93 of 100 images passed the quality gate. The 7 rejections are PLSU images with the palm base cropped, matching the gate findings.
- Heart, head and life were all traced on 87 of 93 palms, and two of the three on the other 6.
- A fate line was reported on 47 of 93 palms.

**Against the Phase 1 target:** per-line recall ≥ 0.85. The class-agnostic recall is **0.843**, just short.

## What the errors are

The misses were inspected visually on the lowest-recall cases.

1. **Fate lines.** The v0 model has no fate class. The classical detector (Frangi ridge filter + minimal-cost path from wrist to middle finger) recovers some of them.
2. **Truncated life lines.** The model often stops before the life line curves down to the wrist.
3. **An occasional missed heart line.**

## Calibration of the fate-line detector

The detector reports a fate line only if at least 85% of its path lies on strong ridges. The table checks, against the PLSU annotations, whether the reported path lies on an annotated line.

| Threshold | Fate lines reported | Share whose path lies mostly (>80%) on an annotated line |
|---|---|---|
| 0.70 | 87/93 | 61% |
| 0.80 | 66/93 | 71% |
| **0.85** | **47/93** | **81%** |
| 0.90 | 23/93 | 83% |

Confidence correlates with correctness (r = 0.54). Precision is favoured on purpose: claiming a fate line that is not there is worse than saying "no clear fate line".

## Known limits and next steps (Phase 2)

- **Life-line truncation:** the largest recall gap. Plan: train our own segmenter with a connectivity-aware loss (clDice), and add a fate class.
- **Line identity is not evaluated.** PLSU has no per-line labels. Line-labelled data is needed: Roboflow export (needs the owner's account) or our own annotation.
- **The fate detector can follow a neighbouring crease.** About 19% of reported paths are not mostly on an annotated line.
- **Prototype weights only.** The v0 weights were trained on scraped photos and must not ship (D-006).

## Raw report

### Generated output: Line detection evaluation (PLSU, class-agnostic)

Images: 100; passed the quality gate: 93

| Output | Tolerance | Precision | Recall | F1 |
|---|---|---|---|---|
| raw model (p>0.5) | 1.5% of palm length | 0.939 | 0.753 | 0.823 |
| raw model (p>0.5) | 2.5% of palm length | 0.964 | 0.789 | 0.856 |
| traced lines | 1.5% of palm length | 0.921 | 0.778 | 0.832 |
| traced lines | 2.5% of palm length | 0.950 | 0.815 | 0.867 |
| traced + classical fate line | 1.5% of palm length | 0.902 | 0.808 | 0.842 |
| traced + classical fate line | 2.5% of palm length | 0.934 | 0.843 | 0.877 |

Lines traced per palm: 0: 0, 1: 0, 2: 6, 3: 87
Fate line reported (classical): 47/93
