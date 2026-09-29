# Model card: grahrekha-lines-v1

| | |
|---|---|
| **Task** | Palm-line semantic segmentation: background, heart, head, life, fate |
| **Architecture** | U-Net (segmentation_models_pytorch) with a ResNet-34 encoder |
| **Input** | Canonical palm frame (`palm/rectify.py`), 512×512 RGB, ImageNet normalisation |
| **Training code** | `ml/src/grahrekha_ml/train_lines.py` |
| **Loss** | Cross-entropy (ignore index 255) + Dice + clDice (topology-preserving) |
| **Status** | **RESEARCH ONLY.** Must not ship in production (D-006). |

## Training data and licences

| Data | Use | Licence | Production-clear? |
|---|---|---|---|
| PLSU (Pham Van et al., 2020), 858 palms from `lines_train_v1` | Human-drawn line masks | **None stated** | ❌ Needs permission from the authors (Sun* Inc.) |
| Line identity labels | Derived automatically from v0 (palm-line-reader) predictions | v0 weights were trained on scraped photos | ❌ Research only |
| ResNet-34 ImageNet weights (torchvision) | Encoder initialisation | BSD-3-Clause (weights: ImageNet terms) | ⚠️ Check ImageNet terms for commercial use |
| PLSU source images (11K Hands) | Palm photos | Academic fair use | ❌ |

**Path to a production model:** retrain on licence-cleared data (Roboflow CC BY sets after a provenance audit, owner-collected consented photos, synthetic data), with identities annotated by humans rather than derived from v0.

## Intended use

- R&D and the open-source research demo: line tracing for evidence-based evaluation of palmistry claims.
- **Not** for identifying people.
- **Not** for health or medical inference (D-009).

## Evaluation

See `docs/eval/lines-v1.md`. That covers per-line recall and precision against derived labels, class-agnostic PLSU scores, heart end-zone agreement with human annotation, and test–retest consistency.

## Known limitations

- **Training images are mostly scanner-like** 11K Hands photos with the palm base often cropped. Performance on phone photos must be checked separately (test–retest on D3).
- **Line-identity labels come partly from v0,** so identity errors in v0 can be learned.
- **The fate line is rare** (22% of training palms), so fate performance is the least certain.
