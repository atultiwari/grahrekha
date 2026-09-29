# Phase 1 report: palm engine prototype

**Date:** 2026-09-29
**Scope:** photo → quality gate → canonical palm frame → line detection → measured features → cited rules → `/lab` page.
**Detailed evidence:** [gate-v1.md](gate-v1.md), [lines-v0.md](lines-v0.md), [features-v1.md](features-v1.md).

## Exit criteria

| Criterion (IMPLEMENTATION-PLAN.md) | Target | Result | |
|---|---|---|---|
| Non-palm images rejected | ≥ 97% | **99.7%** (299/300) | ✅ |
| Real palms falsely rejected | ≤ 5% | **3.5%** adjudicated (9.7% raw: 10 images genuinely cropped) | ✅ |
| Line recall (heart/head/life) | ≥ 0.85 per line | **0.843**, class-agnostic (precision 0.934, F1 0.877). Per-line not measurable: no line-labelled data yet. | ❌ just short |
| Test–retest agreement (categorical) | ≥ 85% | **0.77** mean. Reliable subset: presence 0.88–0.97, life start zone 0.97, heart end zone 0.85. | ❌ |
| Engine latency p95 | < 2.5 s | **0.48 s** (CPU, laptop) | ✅ |
| Every fired rule traceable to a citation | yes | yes: verbatim quotes checked in CI against the source text | ✅ |
| Owner reviews 20 readings | yes | **pending** (owner action) | ⏳ |

## What we learned

1. **The quality gate is solid.** A single calibrated rule, MediaPipe's handedness label combined with landmark chirality, separates palm from back of hand. It works even when MediaPipe's left/right label is wrong (≈20% of phone photos).
2. **Line finding is good; line *completeness* is not.** The v0 segmenter finds lines precisely (precision 0.93) but truncates them:
   - **Life lines** stop before curving to the wrist.
   - **Heart lines** stop short of the index finger. As a result, 114 of 135 heart lines appear to end under the middle finger, which is a systematic bias.
3. **Consistent is not the same as correct.** The heart-line end zone is reproducible (0.85) but biased. The rule base now has `validity_blocker`s for exactly this case.
4. **Pose variation limits single-photo hand shape.** Different photos of the same hand vary about as much as different people do in palm shape, finger length and element. Only multi-photo capture can fix that.
5. **Cheiro's life-line chapter is health and lifespan material,** so there are no life-line rules (D-009).

## Built

| Area | What exists |
|---|---|
| Engine | Safe image decoding; MediaPipe gate (10 reasons with advice); canonical frame; v0 segmenter adapter; line tracing; classical fate-line detector; features with noise-aware classes and zone certainty; `/v1/palm/analyze`; `/v1/rules/evaluate` |
| Rules | 9 cited Cheiro rules; safe JSONLogic subset; CI lint (citations, health terms, reliability tiers, validity blockers) |
| Web | `/lab` page (upload/capture, overlay on the original photo, features, reading with "why") |
| Evaluation | Frozen splits; gate, line and test–retest evaluations, all reproducible from one command each |
| Quality | 180 engine tests (94% coverage), 51 TypeScript tests, strict types; CI with real models and a Docker smoke test |

## Deferred from Phase 1

These were deferred deliberately, and their order has been updated.

- **Live camera guide** (MediaPipe WASM in the browser, 1F.1). The upload/capture input works now; the live guide belongs with the multi-photo capture flow.
- **"Wrong line" editor** (1F.3). This should arrive together with the Phase 2 annotation pipeline, because its output is training data.
- **Playwright end-to-end test** (1F.4). The flow was verified manually in a browser. An automated test comes with the Phase 5 product UI.

## Recommendation: go to Phase 2 next

The plan says: *"If line recall misses the target: go to Phase 2 first and train our own model before building product UI on top."* Both misses (line completeness and consistency) are measurement problems. That makes Phase 2 the right next step:

1. **Line-labelled data.** Export the Roboflow sets (needs the owner's account) and annotate our own polylines.
2. **Our own segmenter.** Include a **fate** class and a connectivity-aware loss (clDice) to stop truncation.
3. **Multi-photo capture** (median of 2–3 photos per hand) to lift test–retest agreement.
4. **Re-run all three evaluations,** then lift the validity blockers where the numbers allow.

The astrology engine (Phase 3) is independent, and can run in parallel whenever you want.
