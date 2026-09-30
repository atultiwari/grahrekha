# Model card: grahrekha-lines-v2

| | |
|---|---|
| **Task** | Palm-line semantic segmentation: background, heart, head, life, fate |
| **Architecture** | Same as v1: U-Net (segmentation_models_pytorch), ResNet-34 encoder |
| **Input** | Canonical palm frame (`palm/rectify.py`), 512×512 RGB, ImageNet normalisation |
| **Training** | Fine-tuned from v1 (`--init-from v1`) for 15 epochs at lr 1e-4, on PLSU (`lines_v1/train`) plus Roboflow phone and web photos (`lines_v2/train`). Best epoch 10. |
| **Training code** | `ml/src/grahrekha_ml/train_lines.py`, `build_roboflow_dataset.py` |
| **Status** | **RESEARCH ONLY.** Must not ship in production (D-006). The weights are built locally and not distributed. |

## Training data and licences

Everything in the v1 card applies, plus:

| Data | Use | Licence | Production-clear? |
|---|---|---|---|
| Roboflow Universe `24rd021/palm-reading-itwlw` v13 | 506 phone photos with per-line polygons (80% train, 20% `eval_phone`) | CC BY 4.0 (image provenance undocumented) | ⚠️ Needs a provenance audit |
| Roboflow `cv2project-uu3kn/palmistry-zbcbn` v2 | 1,083 photos, heart/head/life polygons | CC BY 4.0 (provenance undocumented) | ⚠️ Same |
| Roboflow `palm-reading-test/palm-line-segmentation` v1 | 118 photos | CC BY 4.0 (provenance undocumented) | ⚠️ Same |

**Attribution (CC BY 4.0):** the Roboflow Universe project owners listed above.

**Leakage guard:** 109 Roboflow images were near-duplicates of PLSU eval images and were dropped. So the Roboflow sets reuse the same public hand photos (11K Hands).

## Evaluation

Full details: `docs/eval/lines-v2.md`.

- **Phone photos** (68 held out, human line identities): recall for heart, head, life and fate is 0.983 / 0.966 / 0.871 / 0.694 (v1: 0.968 / 0.959 / 0.82 / 0.342). Fate false alarms went up: 10 of 28 palms without a fate line (v1: 4).
- **PLSU** (93): per-line results match v1, except fate recall 0.577 (v1 0.645). Heart end-zone agreement is 92% (v1 88%).
- **Consistency:** test–retest agreement 0.80 (same as v1). Cross-camera agreement 0.68 → 0.73 (v1 0.70 → 0.74).

## Known limitations

- **Fate over-detection on phone photos.** There are no fate rules yet; revisit before adding any.
- **Life-line end zone flips between photos** (cross-camera 0.50). The end zone is not usable for rules.
- **Photo provenance.** The training images come from public datasets with undocumented provenance, so the model is not production-clear.
