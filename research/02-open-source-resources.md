# Open-Source and Open-Access Resources for AI Palmistry

**Research date:** 2026-09-29.

**How this was checked:**
- `gh api`: stars, last push, SPDX licence, READMEs and source files.
- Hugging Face Hub API, Kaggle API, Roboflow Universe pages.
- Project Gutenberg and Internet Archive search.

Star counts and dates are as of the research date.

> Papers with Code now redirects to huggingface.co/papers, so Hugging Face Papers search was used instead.

---

## 1. Summary

1. **No mature open-source palmistry product exists.** What is out there is student projects, hackathon demos and thin wrappers around a vision-language model (VLM).
2. **Two repos are genuinely reusable for line detection:**
   - **samuelwbarber/palm-line-reader** (MIT, 2026): an 11 MB ONNX segmentation model for 4 classes that runs in the browser alongside MediaPipe.
   - **yeonsumia/palmistry** (Apache-2.0, 55★): straightens the photo using landmarks, then U-Net → K-means → length rules.
3. **Labelled data is the bottleneck.**
   - The largest open line-labelled sets are on Roboflow Universe under CC BY 4.0, some with around 7k images. These counts probably include augmented copies, and the image sources are unknown.
   - The academic PLSU dataset has no licence.
   - Palmprint biometric databases are research-only.
4. **No structured palmistry rule base exists.** We must build one from public-domain books.
5. **Licensing traps:**
   - OpenPose: non-commercial only.
   - AGPL: Ultralytics YOLO, Swiss Ephemeris/pyswisseph, kerykeion, PyJHora.
   - GPL: the U-Net code inside yeonsumia.
   - Academic-only: 11K Hands and IITD.

---

## 2. End-to-end palmistry projects

| Project | Pipeline | ★ / last push | Licence | Verdict |
|---|---|---|---|---|
| **[yeonsumia/palmistry](https://github.com/yeonsumia/palmistry)** ("Fortune On Your Hand", Korean) | HSV skin mask → MediaPipe 21 landmarks → **homography to a canonical hand template** (straightens the palm) → 256×256 U-Net line mask → **K-means** splits heart/head/life → length judged against landmark-based thresholds, with canned text | 55★, 2026-04 | Apache-2.0, **but** `model.py` is derived from milesial/Pytorch-UNet (**GPL-3.0**). Weights trained on PLSU (no licence). | **Best reference architecture.** Re-implement the straightening and landmark-relative measurement. Rewrite the U-Net with SMP (MIT). Its rules are naive: 3 lines, 1 rule each. |
| **[samuelwbarber/palm-line-reader](https://github.com/samuelwbarber/palm-line-reader)** | In-browser: MediaPipe crops the palm and mirrors right hands → **SMP U-Net, mit_b0 encoder** (5.55M params) → 4 classes (background/heart/head/life) at 512×512 via **onnxruntime-web (WebGPU/WASM)**. A large model (mit_b5) produced first-pass labels on a few thousand r/PalmReading photos, which were corrected by hand. Loss: Dice + **clDice** + distance + connectivity. **Foreground Dice 0.81.** | new, 2026-07 | MIT | **Most directly usable.** fp16 = 11 MB, int8 = 5.7 MB. ⚠️ Weights were trained on scraped Reddit photos, so use them only for prototyping and first-pass labels, then retrain on our own data. No fate line. |
| [lachlanchen/LazyOracle](https://github.com/lachlanchen/LazyOracle) | MediaPipe landmarks → **hand shape (earth/air/fire/water), finger-length ratios, thumb angle, 8 Chinese palm palaces**. The user taps to mark lines. Principle: *"the model narrates; it never decides."* Has tests. | 2026-09 | MIT | **Reuse its hand-shape and finger-ratio logic, and its design principle.** |
| [2478732869-a11y/PalmLineExtraction-](https://github.com/2478732869-a11y/PalmLineExtraction-) | MediaPipe polygon mask (shrunk inward) → **Frangi ridge filter → Dijkstra shortest path** between anatomical start/end zones, one line at a time | 2026-03 | none | Good classical design. **Re-implement; do not copy.** |
| [longyaoyoudu/hand_check](https://github.com/longyaoyoudu/hand_check) | MediaPipe crop → blur and brightness **quality gate that explains why a photo failed** → CLAHE + bilateral filter → heuristic lines → Gradio UI; under 0.2 s | 4★, 2026-01 | none | Reference for quality-gate UX. |
| [sude-go/PalmSegNet](https://github.com/sude-go/PalmSegNet) | FastAPI, SMP UNet++, 4 lines including fate, left/right detection, canonical rotation, returns skeletons | 2026-08 | none ("Private") | API design reference only. |
| [TencentYoutuResearch/Palm-Applications](https://github.com/TencentYoutuResearch/Palm-Applications) (PalmDestiny) | LLM reads the palm photo + BaZi and zodiac | 6★ | Apache-2.0 | Prompt and UX reference; no computer vision. |
| [IamSparky/PRISM](https://github.com/IamSparky/PRISM-Palm-Reasoning-Interpretation-System-with-Models) | Retrieval-augmented generation (RAG) over palmistry PDFs (ChromaDB + Gemini) + FastAPI | 2026-05 | Apache-2.0 | Reusable RAG pattern. ⚠️ Bundles a copyrighted modern book; do not copy its data. |
| [timerzz/kanxiang](https://github.com/timerzz/kanxiang) | Claude skill for Chinese face and palm reading, with a rule file `references/shouxiang.md` drawn from classical texts | 18★, 2026-09 | MIT | Reusable **Chinese palm rule knowledge**. |
| [hhszzzz/taibu](https://github.com/hhszzzz/taibu) (mingai.fun) | Mature Chinese multi-divination platform (Next.js + Supabase, VLM palm and face reading, MCP server) | **597★** | **AGPL-3.0** | Competitor and UX reference only; **do not copy code.** |
| MuntahaShams, Sachin-579 (YOLOv8 boxes) | Bounding boxes around lines | 0–1★ | none, YOLO is AGPL | Skip: a box is the wrong shape for a line. |
| daliborristic883/PalmLineReading, palmy, Horo, lyhanburger/palm_dealing, and others | Pre-2020 OpenCV attempts | — | mixed | **Abandoned.** palm_dealing makes health claims. |

**Thin VLM wrappers** (useful for prompt and UX ideas only):
- AuraScan (Claude; estimates $0.01–0.03 per reading)
- Poser8-Inc/palm-reader (Claude)
- barissglc/PalmReaderAI (Groq Llama-3.2-Vision + Gemini)
- BearNick/Palmistry-telegram-bot (OpenAI)
- SpandanM110/Local-First-AI-Astrologer (Gemini + FAISS RAG over *Palmistry for All* + ephem charts)
- myeongun-palm (Flutter + Gemini)

None of these ground the VLM in measured geometry.

**Hugging Face:** there is **no credible palm-line model or dataset.**
- The Spaces are thin (lsh8458/palm-lines-api, kfaraz/drishti-palmistry-api).
- Akiyue/Palmistry has YOLO-pose weights with an "unknown" licence.
- yawerabbas/palmistry-checkpoint is a re-upload of the yeonsumia checkpoint.

---

## 3. Datasets for line detection and segmentation

### 3.1 Roboflow Universe (all CC BY 4.0 unless noted; attribution required; image sources undocumented)

| Dataset | Task | Images | Classes |
|---|---|---|---|
| [docseg/palmistry-kp](https://universe.roboflow.com/docseg/palmistry-kp) | Keypoints (a line stored as points) | 7,112 | head, fate, heart, life |
| [palmistry-ccmq5/palmistry-dhpnb](https://universe.roboflow.com/palmistry-ccmq5/palmistry-dhpnb) | Boxes | 7,177 | 4 lines |
| [palmistry-2klz8/palmistry-g45zz](https://universe.roboflow.com/palmistry-2klz8/palmistry-g45zz) | Boxes | 6,679 | 4 lines (**public domain**) |
| [dstu-dfliv/palm-lines-recognition](https://universe.roboflow.com/dstu-dfliv/palm-lines-recognition) | Keypoints | 2,959 | 4 lines |
| [cv2project-uu3kn/palmistry-zbcbn](https://universe.roboflow.com/cv2project-uu3kn/palmistry-zbcbn) | **Instance segmentation** | 1,083 | head, heart, life |
| [24rd021/palm-reading-itwlw](https://universe.roboflow.com/24rd021/palm-reading-itwlw) | Instance segmentation | 506 | fate, head, heart, life, **marriage, sun, property** |
| [palmlinesdetection/palmlinesdetection](https://universe.roboflow.com/palmlinesdetection/palmlinesdetection) | Instance segmentation | 403 | Line1–4 |
| [palmveda/lines-ermuj](https://universe.roboflow.com/palmveda/lines-ermuj) | Instance segmentation | 63 | 8 lines, including **mercury/health, sun, mars** |
| Smaller: fudan palm-line-detect (156), palm-line-segmentation (118, includes girdle of Venus), abhiwan (110), and others | Segmentation | 50–156 | — |

**How to use them:**
- Merge the segmentation sets as seed data.
- Convert the keypoint sets into thick polylines to get weak segmentation labels for pretraining.
- Use the box sets only as rough location hints.
- **Audit quality and image provenance before relying on any of them.**

### 3.2 Academic and synthetic data

- **PLSU** (Pham Van et al. 2020, [arXiv 2102.12127](https://arxiv.org/abs/2102.12127))
  - Hand-annotated line masks; yeonsumia trained on it.
  - **No licence stated.** Email the authors at Sun* Inc., Vietnam, before any commercial use.
- **Synthetic palm creases** (Apache-2.0 code), good for pretraining:
  - [Ukuer/Diff-Palm](https://github.com/Ukuer/Diff-Palm) (CVPR 2025)
  - [Ukuer/PCE-Palm](https://github.com/Ukuer/PCE-Palm) (AAAI-24)
  - [Ukuer/rpg-palm](https://github.com/Ukuer/rpg-palm)
  - ⚠️ Their checkpoints were trained on research-only palmprint data.

### 3.3 Kaggle raw hand photos (no line labels; candidates for annotation)

| Dataset | Size | Licence | Note |
|---|---|---|---|
| [feyiamujo/human-palm-images](https://www.kaggle.com/datasets/feyiamujo/human-palm-images) | 800 DSLR photos, 400 subjects (Nigeria) | **CC BY 4.0** | **Best commercially usable raw set**; adds darker skin tones |
| shyambhu/hands-and-palm-images | 11K Hands re-upload | labelled ODbL, but the original is academic-only | Treat as non-commercial |
| saqibshoaibdz/palm-dataset | 12,000 TIFF | labelled "MIT" | Provenance suspect |
| axondata/palm-recognition-large-scale | 24k | CC BY-NC | Non-commercial |
| unidpro/open-palm-hand-images | Sample of a paid 500k set | CC BY-NC-ND | **Possible vendor for licensed data** |

---

## 4. Hand landmarks, segmentation and palm cropping

| Tool | Licence | Use |
|---|---|---|
| **MediaPipe Hand Landmarker** (`@mediapipe/tasks-vision`; Web WASM/GPU, Android, iOS, Python) — [docs](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker) | Apache-2.0, 37k★ | **Core of capture:** hand present, palm side facing camera, handedness, quality checks, palm crop, straightening, landmark-relative measurements. About 17 ms on a Pixel 6 CPU. |
| OpenCV Zoo `palm_detection_mediapipe` / `handpose_estimation_mediapipe` (ONNX) | Apache-2.0 | Server-side alternative |
| segmentation_models.pytorch (SMP) | MIT, 11.7k★ | **Training framework** (UNet/UNet++, MiT/EfficientNet encoders). Check each encoder's weight licence. |
| onnxruntime-web | MIT | Runs the segmentation model on the device |
| SAM 2 | Apache-2.0 | Speeds up annotation |
| scikit-image (Frangi/Sato/Meijering), OpenCV-contrib RidgeDetectionFilter | BSD-3 / Apache-2.0 | Classical ridge filters for detecting creases |
| EgoHands | CC BY 4.0 | Hand-mask pretraining |
| HaGRID (~550k gesture images, including open palms) | CC BY-SA 4.0 variant | Training the quality gate. Share-alike applies, so get legal review. |
| 11K Hands | Academic only | Research and evaluation only |
| **OpenPose** | **Non-commercial; CMU owns derivatives** | **Do not use** |
| Ultralytics YOLO | **AGPL** | Avoid, or buy a licence |
| milesial/Pytorch-UNet | **GPL-3.0** | Avoid |

**Palmprint biometrics (technique reference only):**
- ROI (palm-centre crop) code: safwankdb/Effectual-Palm-RoI-Extraction (no licence), AngeloUNIMI/PalmSeg (GPL), Huterox/palm_recongnition.
- With MediaPipe, a region of interest is simply built from landmarks 0, 5, 9, 13 and 17.
- Databases are all research-only or have unclear terms: Tongji, IITD, PolyU-IITD, CASIA, XJTU-UP, NTU.
- See the [IAPR TC4 list](https://iapr-tc4.org/palmprint-datasets/) and [Awesome-Palmprint-Recognition](https://github.com/HuikaiShao/Awesome-Palmprint-Recognition).

---

## 5. Classical line extraction recipe (re-implement)

1. MediaPipe palm polygon mask, shrunk inward so the hand outline does not dominate.
2. CLAHE contrast boost on the L channel, plus a bilateral filter.
3. Frangi / Sato filter with `black_ridges=True` (creases are dark valleys). Tune sigma after straightening the palm to a fixed size.
4. **Minimal-path (Dijkstra) search for each line** between anatomical start and end zones defined by landmarks. Cost = 1 − ridge strength.
   - Life line: from between the index finger and thumb, around the base of the thumb.
   - Heart line: from under the little finger toward the index or middle finger.
5. Skeletonise, prune small spurs, measure.

MFRAT, Gabor and competitive-code methods are available in Li-ChengYan/palmprint-recognition-matlab (MIT) and PCE-Palm `PCEM.py` (Apache). Use them as extra feature channels or for weak labels.

**Role of this recipe:**
- A fallback when the model is unsure.
- A generator of first-pass labels.
- An explainable confidence signal.

---

## 6. Public-domain sources for interpretation rules

| Work | Where | Notes |
|---|---|---|
| Cheiro, *Palmistry for All* (1916) | [Gutenberg #20480](https://www.gutenberg.org/ebooks/20480) | Public domain. Easiest to parse (plain text). |
| Cheiro, *Language of the Hand* (1894/97) | [IA](https://archive.org/details/cheiros-language-of-the-hand) | Public domain. Richest diagrams of lines and mounts. |
| Cheiro, *Guide to the Hand* (1900) | [IA](https://archive.org/details/cheirosguidetoha00chei_0) | Public domain |
| **W. G. Benham, *The Laws of Scientific Hand Reading* (1900)** | [IA](https://archive.org/details/lawsscientifich00benhgoog) | Public domain. **The most systematic rule set** (mounts, hand types, line qualities). Avoid the 1958/1988 re-editions. |
| Mrs J. B. Dale, *Indian Palmistry* | [Gutenberg #52523](https://www.gutenberg.org/ebooks/52523) | Public domain. Indian tradition written in English. |
| Williams, *Key to Palmistry*; Markun, *What You Should Know About Palmistry* | [Gutenberg #79203](https://www.gutenberg.org/ebooks/79203), [#79270](https://www.gutenberg.org/ebooks/79270) | Public domain (US) |
| Frith & Heron-Allen *Chiromancy* (1883); *Practice of Palmistry* (1900); Gaffney (1897); Farwell (1886); Campbell (1879) | Internet Archive | Public domain |
| **Samudrika Shastra**: Pt. Shaktidhar 1916 (Naval Kishor Press); Bhatta Keshava Sharada manuscript; *Samudrika Laksanam* (1959) | [IA 1916](https://archive.org/details/QDSE_samudrika-shastra-first-half-by-pt.-shaktidhar-1916-munshi-naval-kishor-press), [IA manuscript](https://archive.org/details/432SamudrikaShastraBhattaKeshavaJyotishaDAMSharadaBirchBark), [IA 1959](https://archive.org/details/in.ernet.dli.2015.408515) | The 1916 edition and the manuscript are public domain. ⚠️ The 1959 edition's copyright status was not checked. ⚠️ 20th-century Hindi books tagged "CC0" by uploaders (e.g. Vyas 1976) are probably still in copyright. |
| Chinese palm reading (手相) | [kanxiang `references/shouxiang.md`](https://github.com/timerzz/kanxiang) | MIT |

**Suggested rule-base format:**
- One record per rule: `rule_id, tradition (western|vedic|chinese), feature, condition, interpretation, polarity, source (book, page), confidence, reviewer_notes`.
- Stored as YAML/JSON.
- Extracted from the texts with an LLM, then checked by a human (you).
- Conflicting traditions are kept side by side, never merged silently.

---

## 7. Astrology libraries (for the separate astrology engine)

| Library | Licence | Notes |
|---|---|---|
| **[jyotishganit](https://github.com/northtara/jyotishganit)** | **MIT** | Uses Skyfield + NASA JPL DE421 ephemeris, not Swiss Ephemeris. Covers divisional charts D1–D60, panchanga, shadbala, **Vimshottari dasha**, JSON output. **Best permissive option.** Young project, so validate its output against JHora. |
| [Skyfield](https://github.com/skyfielders/python-skyfield) | MIT | Ephemeris engine if we build our own dasha calculations |
| [jyotisha](https://github.com/jyotisham/jyotisha) | MIT | Panchanga and festivals |
| [VedAstro](https://github.com/VedAstro/VedAstro) | MIT | Calls Swiss Ephemeris internally, so the Swiss Ephemeris licence still applies |
| Swiss Ephemeris / pyswisseph | **AGPL or paid professional licence** | Industry standard. **Buy the licence** if we host it. |
| kerykeion, PyJHora | **AGPL** | PyJHora is the most complete Jyotish implementation. Use it for validation only, not in production. |
| panchangJS | MPL-2.0 | Client-side panchang |
| jyotish-api | GPL-3.0 | Avoid |

---

## 8. Recommended starter stack

| Stage | Choice |
|---|---|
| Capture and quality gate | MediaPipe Hand Landmarker in the browser. Checks: one hand, palm side, fingers spread, blur, brightness. Explain the reason for any rejection. Capture both hands. |
| Straightening (rectification) | Homography from the 21 landmarks to a canonical template. Mirror right hands. Crop the palm. |
| Line segmentation v0 | palm-line-reader `student_fp16.onnx` via onnxruntime-web (heart/head/life). Frangi + minimal path as a cross-check. |
| Line segmentation v1 | Our own SMP UNet (MiT-b0/b2), Dice + clDice + connectivity loss, 5+ classes. Pretrain on synthetic creases, Roboflow CC BY data and first-pass labels. Fine-tune on our own annotations. Export to ONNX fp16/int8. |
| Features | Skeleton → per line: length relative to landmarks, start and end zones, curvature, breaks, forks, islands, contrast. Plus hand shape, finger ratios, thumb angle (LazyOracle logic). |
| Palm interpretation engine | Our YAML rule base (from §6) → selected rules → LLM **narrates only**, citing sources. |
| Astrology engine (kept separate) | jyotishganit (MIT). Swiss Ephemeris only with the paid licence. |
| Annotation | CVAT or Label Studio (polylines) + SAM 2 + a correction tool like palm-line-reader's |

## 9. Gaps: what we must build ourselves

1. **A consented palm-photo dataset with polyline labels for 6–8 lines.**
   - Scale: 2–5k images across skin tones, ages, lighting conditions and phones.
   - At least 2 annotators, and measure how often they agree.
   - Nothing like this exists openly with clear rights.
2. **Minor lines and marks** (islands, stars, crosses, chains, marriage and children lines). Only tiny sets exist (63–506 images).
3. **A structured interpretation knowledge base** with source citations, covering Western + Samudrika + Chinese traditions.
4. **Measurement standards**, e.g. what counts as a "long" heart line or a "deep" line. Define them relative to landmarks, then calibrate later with your own review.
5. **Evaluation set and metrics:**
   - clDice, Hausdorff distance, per-line recall.
   - Test–retest: the same palm photographed several times should give the same features.
6. **Mount prominence** is weak from a single 2D photo. Treat it as low-confidence.
7. **Privacy compliance** (DPDP, GDPR, BIPA), because palm images are biometric identifiers.

## 10. Licensing cheat-sheet

| Category | Items |
|---|---|
| ✅ Safe (permissive) | MediaPipe, onnxruntime, SMP, scikit-image, OpenCV, SAM 2, Diff-Palm/PCE-Palm code, palm-line-reader code, LazyOracle, kanxiang, jyotishganit, Skyfield, public-domain books |
| ⚠️ Copyleft | AGPL: YOLO, Swiss Ephemeris (unless the paid licence), pyswisseph, kerykeion, PyJHora, taibu. GPL: Pytorch-UNet (and so yeonsumia's `model.py`), PalmSeg, jyotish-api |
| ⛔ Non-commercial | OpenPose, 11K Hands, IITD, PolyU-IITD, Kaggle NC sets |
| ❓ Unclear provenance | PLSU, Tongji, palm-line-reader weights, Roboflow image sources, Kaggle "MIT" re-uploads, HF checkpoints with "unknown" licence |
| 🔒 No licence (all rights reserved) | PalmLineExtraction-, hand_check, safwankdb ROI, most student repos. Learn from them; do not copy. |

Raw research notes are in the session scratchpad (`oss/`).
