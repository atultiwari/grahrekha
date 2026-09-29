# Resources Registry

This is one list of every external dataset, model, repository, tool and text we may use, so the owner can review them all in one pass.

**Policy:** [D-014](DECISIONS.md). During R&D we may use anything internally. It stays git-ignored in `data/` or `services/engine/models/weights/` and is never redistributed. **Before any production use, an item's status must be `cleared`.**

**How to use this file:** fill in the **Owner decision** column with one of:

| Code | Meaning |
|---|---|
| `use` | Use in R&D |
| `skip` | Don't use |
| `later` | Revisit later |
| `seek-permission` | Needed for production; contact the owner of the resource |
| `cleared` | Licence or permission settled for production |

**Full direct download URLs** for every item (Tier 1–3 and all models) are in [`data/manifest.yaml`](../data/manifest.yaml). That file is committed, so sources never need to be searched for again, even after archives are deleted.

**Checked on:** 2026-09-29. Sizes are exact byte counts from HEAD requests unless marked *(unverified)*.

**Download methods:**
- Google Drive files are public: `gdown --id <ID>`.
- Kaggle public datasets download without an account via `https://www.kaggle.com/api/v1/datasets/download/<owner>/<slug>` (`curl -L`).
- Roboflow needs an account and an API key.

> ⚠️ **Disk:** about 29 GB free at the time of writing. Tier 1 is about 4.4 GB compressed. Download → extract → delete archive, so the peak stays under about 9 GB.

---

## 1. Datasets

**Purpose codes:**
- **P**: positive palm photos
- **L**: palm-line labels
- **N**: negatives for the quality gate
- **S**: hand segmentation

### Tier 1: essential (~4.4 GB)

| # | Item | Purpose | Source | Size | Login | Licence (production) | Notes | Owner decision |
|---|---|---|---|---|---|---|---|---|
| D1 | **11K Hands** `Hands.zip` + `HandInfo.csv` | P, N (dorsal) | Drive `1KcMYcNJgtK1zZvfl_9sTqnyBUTri2aP2`, CSV `1RC86-rVOR8c93XAfM9b9R45L7C2B0FdA`; HF mirror `Zicara/Hands_11k` | 633 MB | No | Academic fair use only | 11,076 images, 1600×1200, white background, scanner-like. The `aspectOfHand` column splits palmar and dorsal. | |
| D2 | **PLSU** palm-line segmentation | L | Drive `1B4uj-b4RuUNkC_oeCsRkuih4rjuQ6tHH` (via link.sun-asterisk.vn/palmlinedataset) | 162 MB | No | **None stated.** Email Sun* Inc. | 1,039 image/mask pairs. Masks are **binary** (no per-line class). Drawn on 11K Hands images. | |
| D3 | **AxonData palm-recognition** (HF sample) | P (smartphone) | `huggingface.co/datasets/AxonData/palm-recognition-dataset` | 910 MB | No | CC BY-NC (sample of a commercial set) | 30 users × left/right × front and rear camera × 3 shots. **Real phone photos.** Good for test–retest. | |
| D4 | **feyiamujo/human-palm-images** (Kaggle) | P | Kaggle API URL | 969 MB | No | **CC BY 4.0** ✅ | 800 DSLR palms, 400 subjects (Nigeria), darker skin tones. Best candidate for production use. | |
| D5 | **palmprint-v1i-crease** (Kaggle) | L | `tmtrnhelloworld/palmprint-v1i-crease` | 358 MB | No | CC0 (but derived from MPD, which is academic) | Palmprint region crops with crease labels. Classes *(unverified)*. | |
| D6 | QuickDraw `hand.ndjson` | N (drawings) | `storage.googleapis.com/quickdraw_dataset/full/simplified/hand.ndjson` | 128 MB | No | CC BY 4.0 | Render the strokes to images | |
| D7 | Imagenette2-320 | N (objects) | `s3.amazonaws.com/fast-ai-imageclas/imagenette2-320.tgz` | 342 MB | No | ImageNet terms (research) | ~13k images | |
| D8 | Oxford-IIIT Pets (test parquet) | N (animals, paws) | HF `timm/oxford-iiit-pet` | 413 MB | No | CC BY-SA 4.0 | No dedicated paw dataset exists | |
| D9 | LFW sample | N (faces) | HF `0xmoose/lfw-sample` | 1 MB | No | Research | 100 faces | |
| D10 | Diabetic foot ulcer (DFU) photos | N (feet) | Kaggle `laithjj/diabetic-foot-ulcer-dfu` | 135 MB | No | *(unverified)* | Clinical foot photos. The safest foot set without a login. | |
| D11 | HOF + EYTH (Hand Segmentation in the Wild) | S, N (hard cases) | Drive `1hHUvINGICvOGcaDgA5zMbzAIUv7ewDd3`, `1EwjJx-V-Gq7NZtfiT6LZPLGXD2HN--qT` | 57 MB | No | Unclear | Hands over faces, hands in the wild, with masks | |

### Tier 2: optional, larger

| # | Item | Purpose | Source | Size | Login | Licence | Notes | Owner decision |
|---|---|---|---|---|---|---|---|---|
| D12 | 11K Hands skin masks | S | Drive `0B6CktEG1p54Wa2VzdktNY2Q0YlU` (resourcekey `0-s91SAvu-RqXKlirv3eYtnw`) | 1.69 GB | No | Academic | | |
| D13 | HaGRID sample 30k (384p) | P ("palm" gesture), N | HF `cj-mills/hagrid-sample-30k-384p` | 1.01 GB | No | CC BY-SA 4.0 variant | Palm-facing hands in the wild, low resolution | |
| D14 | BMPD (Birjand mobile palmprint) | P (mobile) | Kaggle `mahdieizadpanah/…bmpd` | 1.79 GB | No | Unknown | | |
| D15 | SMPD (Sapienza mobile palmprint) | P (mobile) | Kaggle | 6.37 GB | No | Unknown | Large | |
| D16 | Tongji contactless: ROI crops / originals | P | Drive `1KZCXi6zAk5mZ1nQHFdeYHboAII3DOjls` / `15hEsOm0fZKUHpFNChPSjwiRfMczxcnVQ` | 98 MB / 4.95 GB | No | No terms stated | Camera rig, not a phone | |
| D17 | UniDataPro open-palm-hand-images | P, N (`back_*`) | HF `UniDataPro/open-palm-hand-images` | 181 MB | No | CC BY-NC-ND | High-resolution sample of a paid set, so a **possible vendor** | |
| D18 | COCO val2017 | N | `images.cocodataset.org/zips/val2017.zip` | 816 MB | No | CC BY (per image) | | |
| D19 | Oxford Pets full | N | `thor.robots.ox.ac.uk/pets/images.tar.gz` | 792 MB | No | CC BY-SA | | |
| D20 | CelebA-HQ one shard | N (faces) | HF `korexyz/celeba-hq-256x256` | 461 MB | No | Research only | | |
| D21 | QuickDraw `foot.npy` | N | Google Cloud Storage | 159 MB | No | CC BY 4.0 | | |
| D22 | EgoHands (Kaggle mirror) | S | `henrikvendelbo/egohands-public` | 327 MB | No | CC BY 4.0 | Egocentric view, low priority | |
| D23 | Palm-Astro-Application data | L | `github.com/lakshay102/Palm-Astro-Application` | 17 MB | No | None | 14 phone photos with masks | |

### Tier 3: the owner must log in or request access

| # | Item | Why it matters | Access | Owner decision |
|---|---|---|---|---|
| D24 | **Roboflow Universe palm-line sets**: `docseg/palmistry-kp` (7,112, keypoints), `cv2project-uu3kn/palmistry-zbcbn` (1,083, segmentation), `24rd021/palm-reading-itwlw` (506, 7 line classes incl. marriage/sun), `palmlinesdetection` (403), `palmveda/lines-ermuj` (63, 8 lines) | **The only sources with per-line classes** (heart/head/life/fate and more) | Free Roboflow account + API key, or the Export button. Mostly CC BY 4.0. | |
| D25 | MPD (Tongji Mobile Palmprint): 16k smartphone images | Closest to real user photos | Baidu Pan `pan.baidu.com/s/1L3i9ghI9sY9yIVeTSEFswg`, code `ofaj` | |
| D26 | IITD Touchless Palmprint | Benchmarking | Application form + email | |

---

## 2. Pretrained models and weights

| # | Item | What | Source | Size | Licence | Notes | Owner decision |
|---|---|---|---|---|---|---|---|
| M1 | **MediaPipe `hand_landmarker.task`** | 21 landmarks + handedness | `storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task` | 7.8 MB | Apache-2.0 ✅ | Core of the quality gate | |
| M2 | **palm-line-reader** `student_fp16/fp32/int8.onnx` + `model_meta.json` | 4-class line segmentation (bg/heart/head/life), 512², Dice 0.81 | raw.githubusercontent.com/samuelwbarber/palm-line-reader/main/models/ | 11 / 22 / 6 MB | Code MIT; **weights trained on scraped Reddit photos** | Prototype v0 segmenter. Samples in `docs/example*.png`. | |
| M3 | **yeonsumia** `checkpoint_aug_epoch70.pth` | Binary palm-line U-Net (trained on PLSU) | raw.githubusercontent.com/yeonsumia/palmistry/main/code/checkpoint/ | 55 MB | Repo Apache-2.0; model code is GPL-derived; weights from PLSU (no licence) | Baseline for comparison, plus sample hand photos (~13 MB) | |
| M4 | Diff-Palm `ema_0.9999.pt` | Synthetic palmprint diffusion model (128 px) | Drive `1vQya0fgrSh-PkFsDBi0OM89_rfSiO3u6` | 87 MB | Code Apache-2.0; weights trained on research data | For synthetic pretraining data | |
| M5 | PCE-Palm checkpoints | Crease-energy + CUT generator | Drive `1epH7GV3g9fk4_RwOX8x-uMo5iKOlj0I4`, `1r_1vdrVaqrBjuBktBKaj5fEwIXzbka8s` | 262 MB | Same as M4 | | |
| M6 | RPG-Palm `palm_full.zip` | Synthetic palm generator | Drive `1P-Z2lem3lRCu99oEReJhzYwBP6dzCuMn` | 218 MB | Same as M4 | | |
| M7 | Palm-Astro-Application `best_model.pth` | Small segmentation model | GitHub (lakshay102) | 57 MB | None | Quality unknown | |
| M8 | Akiyue/Palmistry (HF) | 5 YOLO-pose checkpoints | huggingface.co/Akiyue/Palmistry | *(unverified)* | "unknown"; YOLO is AGPL | Would go in `adapters-agpl/` only | |

---

## 3. Code repositories (reference or reuse)

| # | Repo | Use for | Licence | ★ / last push | Owner decision |
|---|---|---|---|---|---|
| R1 | [samuelwbarber/palm-line-reader](https://github.com/samuelwbarber/palm-line-reader) | In-browser pipeline, training recipe (clDice), label-review tool | MIT | new / 2026-07 | |
| R2 | [yeonsumia/palmistry](https://github.com/yeonsumia/palmistry) | Rectification via template homography; length rules | Apache-2.0 (+ GPL-derived `model.py`) | 55 / 2026-04 | |
| R3 | [lachlanchen/LazyOracle](https://github.com/lachlanchen/LazyOracle) | Hand-shape, finger-ratio and thumb-angle logic; "LLM narrates, never decides" | MIT | 0 / 2026-09 | |
| R4 | [2478732869-a11y/PalmLineExtraction-](https://github.com/2478732869-a11y/PalmLineExtraction-) | Frangi + Dijkstra classical recipe | none (re-implement only) | 0 / 2026-03 | |
| R5 | [longyaoyoudu/hand_check](https://github.com/longyaoyoudu/hand_check) | Quality-gate UX with explained failures | none | 4 / 2026-01 | |
| R6 | [sude-go/PalmSegNet](https://github.com/sude-go/PalmSegNet) | API design: 4 lines + fate, left/right detection, skeleton output | none ("Private") | 0 / 2026-08 | |
| R7 | [IamSparky/PRISM](https://github.com/IamSparky/PRISM-Palm-Reasoning-Interpretation-System-with-Models) | RAG over books pattern (do not copy its bundled copyrighted PDF) | Apache-2.0 | 0 / 2026-05 | |
| R8 | [timerzz/kanxiang](https://github.com/timerzz/kanxiang) | Chinese palm-reading rule reference (`references/shouxiang.md`) | MIT | 18 / 2026-09 | |
| R9 | [hhszzzz/taibu](https://github.com/hhszzzz/taibu) | Competitor/UX reference (mature Chinese divination platform) | **AGPL** | 597 / 2026-08 | |
| R10 | [TencentYoutuResearch/Palm-Applications](https://github.com/TencentYoutuResearch/Palm-Applications) | Prompt/UX reference | Apache-2.0 | 6 | |
| R11 | [Ukuer/Diff-Palm](https://github.com/Ukuer/Diff-Palm), [PCE-Palm](https://github.com/Ukuer/PCE-Palm), [rpg-palm](https://github.com/Ukuer/rpg-palm) | Synthetic crease generation; `PCEM.py` MFRAT-style crease energy | Apache-2.0 | 25 / 17 | |
| R12 | [safwankdb/Effectual-Palm-RoI-Extraction](https://github.com/safwankdb/Effectual-Palm-RoI-Extraction), [AngeloUNIMI/PalmSeg](https://github.com/AngeloUNIMI/PalmSeg) | Palmprint region-of-interest techniques | none / GPL | — | |
| R13 | [HuikaiShao/Awesome-Palmprint-Recognition](https://github.com/HuikaiShao/Awesome-Palmprint-Recognition) | Index of palmprint datasets and papers | — | — | |
| R14 | Vision-LLM wrappers: AuraScan, Poser8-Inc/palm-reader, barissglc/PalmReaderAI, Local-First-AI-Astrologer | Prompt ideas; a baseline "VLM-only" arm for comparison | mixed / none | — | |

---

## 4. Libraries and tools

| # | Tool | Role | Licence | Status | Owner decision |
|---|---|---|---|---|---|
| T1 | MediaPipe (`mediapipe` Python, `@mediapipe/tasks-vision`) | Landmarks, quality gate | Apache-2.0 | Core | |
| T2 | onnxruntime / onnxruntime-web | Inference | MIT | Core | |
| T3 | segmentation_models.pytorch + PyTorch | Training the v1 segmenter | MIT / BSD | Core (ml/) | |
| T4 | OpenCV, scikit-image | Classical CV, Frangi, skeletonise | Apache-2.0 / BSD-3 | Core | |
| T5 | json-logic (Python + JS) | Rule evaluation | MIT | Core | |
| T6 | Drizzle ORM + better-sqlite3 | Database (D-012) | Apache-2.0 / MIT | Core | |
| T7 | Better Auth | Auth (Phase 5) | MIT | Core | |
| T8 | FastAPI, Pydantic, uv | Engine | MIT | Core | |
| T9 | Next.js, Expo, react-native-vision-camera, react-native-svg | Clients | MIT | Core | |
| T10 | CVAT or Label Studio | Annotation | MIT / Apache-2.0 | Tooling | |
| T11 | SAM 2 | Annotation assist | Apache-2.0 | Tooling | |
| T12 | **jyotishganit** + Skyfield | Astrology default provider | MIT | Core | |
| T13 | pyswisseph (Swiss Ephemeris) | Astrology provider for comparison | **AGPL** / paid licence | `adapters-agpl` | |
| T14 | PyJHora | Jyotish reference, validation | **AGPL** | `adapters-agpl` | |
| T15 | kerykeion | Western charts | **AGPL** | `adapters-agpl` (optional) | |
| T16 | Ultralytics YOLO | Detection experiments | **AGPL** / paid | `adapters-agpl` (optional) | |
| T17 | OpenPose | — | Non-commercial; CMU owns derivatives | **Avoid** | |
| T18 | milesial/Pytorch-UNet | — | GPL-3.0 | Avoid (SMP does the same job) | |
| T19 | gdown, huggingface-cli | Downloads | MIT / Apache-2.0 | Tooling | |
| T20 | timezonefinder, GeoNames dump | Geocoding for astrology | MIT / CC BY 4.0 | Core | |

---

## 5. Texts for the rule base (public domain)

| # | Work | Source | Status | Owner decision |
|---|---|---|---|---|
| B1 | Cheiro, *Palmistry for All* (1916) | [Gutenberg #20480](https://www.gutenberg.org/ebooks/20480) | Public domain; plain text, easiest to parse | |
| B2 | Cheiro, *Language of the Hand* (1894/97) | [Internet Archive](https://archive.org/details/cheiros-language-of-the-hand) | Public domain; needs OCR; richest diagrams | |
| B3 | Cheiro, *Guide to the Hand* (1900) | [Internet Archive](https://archive.org/details/cheirosguidetoha00chei_0) | Public domain | |
| B4 | **W. G. Benham, *Laws of Scientific Hand Reading* (1900)** | [Internet Archive](https://archive.org/details/lawsscientifich00benhgoog) | Public domain; most systematic | |
| B5 | Mrs J. B. Dale, *Indian Palmistry* | [Gutenberg #52523](https://www.gutenberg.org/ebooks/52523) | Public domain | |
| B6 | Williams, *Key to Palmistry*; Markun, *What You Should Know About Palmistry* | [Gutenberg #79203](https://www.gutenberg.org/ebooks/79203), [#79270](https://www.gutenberg.org/ebooks/79270) | Public domain (US) | |
| B7 | Frith & Heron-Allen *Chiromancy* (1883); *Practice of Palmistry* (1900); Gaffney (1897); Farwell (1886); Campbell (1879) | Internet Archive | Public domain | |
| B8 | *Samudrika Shastra*, Pt. Shaktidhar (1916, Naval Kishor Press) | [Internet Archive](https://archive.org/details/QDSE_samudrika-shastra-first-half-by-pt.-shaktidhar-1916-munshi-naval-kishor-press) | Public domain; Hindi/Sanskrit; needs OCR | |
| B9 | Bhatta Keshava *Samudrika Shastra* (Sharada manuscript); *Samudrika Laksanam* (1959) | Internet Archive | Manuscript is public domain; **check the 1959 edition** | |
| B10 | Modern Hindi books tagged "CC0" on Internet Archive (e.g. Vyas 1976) | Internet Archive | ⚠️ Probably still in copyright; **avoid** | |
| B11 | Public-domain Jyotish texts (for astrology rules): *Brihat Parashara Hora Shastra* (old translations), *Phaladeepika* | *(to be located and verified)* | Check each edition | |

---

## 6. Proposed first download (awaiting owner approval)

**Tier 1, about 4.4 GB compressed:**

| Group | Items |
|---|---|
| Datasets | D1–D11 |
| Models | M1, M2 (all three ONNX variants + meta + example images), M3 (+ sample images, excluding the ~180 MB `results2/` folder) |

**Where everything goes:**
- Datasets: `data/raw/<id>-<name>/`
- Weights: `services/engine/models/weights/`

**Every item is recorded in `data/manifest.yaml`** with: source URL, SHA-256, size, licence, date, and the production permission needed.

**Downloads are also reproducible:** `scripts/fetch-data.sh --tier 1` fetches the same set.
