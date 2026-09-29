# Line detection: per-line evaluation and the v1 segmenter (Phase 2)

**Date:** 2026-09-30 (in progress; v1 results are added when training completes)

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

*Pending: training in progress.*
