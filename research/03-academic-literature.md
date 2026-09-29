# Academic and Open-Access Literature for AI-Assisted Palmistry

**Research date:** 2026-09-29

**How items were checked:** every item was confirmed against a primary index (arXiv, PubMed/PMC, Semantic Scholar, IEEE/Springer metadata, or the publisher's page). Four PDFs were read in full:
- arXiv 2102.12127
- arXiv 2006.10214
- arXiv 2509.02248
- arXiv 2501.01166

Anything that could not be confirmed is marked **[unverified]**.

---

## 1. Summary

- **Direct "automated palmistry" papers are weak.** They are small conference papers using classical computer vision (edge detection, Hough transform) or tiny CNNs. None of them checks readings against real-world outcomes.
- **Palm-line extraction is mature, but in a different field: biometrics.** Those methods usually work on a cropped square from the centre of the palm and aim to identify people. They do not label lines as life, head or heart.
- **Closest published work to our core model:** Pham Van et al. 2020, a U-Net that segments palm lines, trained on 1,039 annotated images. Its mIoU is 0.584.
- **No commercially licensed palm dataset with per-line labels exists.** We will need to build our own.
- **Scientific validity:**
  - Two independent studies of the life line against age at death found no correlation.
  - The one positive study is confounded: skin creases lengthen as people age.
  - Readings *feel* accurate because of the Forer/Barnum effect: people accept vague, flattering descriptions as personal.
- **Some palm features do have real science behind them:** the 2D:4D finger ratio (a population-level sex difference), the single transverse palmar crease (prevalence varies by ethnicity), and dermatoglyphics. They are not diagnostic for any individual.

---

## 2. Papers that attempt automated palmistry

| Paper | Method | Notes / relevance |
|---|---|---|
| Leung & Law 2016, *An efficient automatic palm reading algorithm and its mobile applications development*, IEEE ICSPCC ([link](https://ieeexplore.ieee.org/document/7753706/)) | Adaptive threshold → finger lengths → three principal lines → regression fitting to join broken segments. Android/OpenCV app, 2–4 seconds. | Earliest clear "palm-reading app" pipeline. Reuse the curve-fitting idea for line continuity. |
| Phienthrakul 2018, *Palm's Lines Detection and Automatic Palmistry Prediction System*, Springer AISC 684 (doi 10.1007/978-3-319-70016-8_18) | Extracts line position, length and curvature, then nearest-neighbour matching to an archive of patterns with known meanings. | Same architecture as our rule engine. Validation is qualitative only. |
| Bansal et al. 2020, *Palmistry using Machine Learning and OpenCV*, IEEE ICISC (doi 10.1109/ICISC47916.2020.9171158) | Palm colour, finger spacing, Canny + morphology → traits. | Indian paper. **Cautionary:** it drifts toward health claims. |
| Acharjee et al. 2020, *A Deep Learning Approach for Efficient Palm Reading*, TAAI (doi 10.1109/TAAI51410.2020.00039) | Deep network that classifies line patterns into predefined labels. | Details **[unverified]**. |
| Nakhua et al. 2024, *Palmistry with Deep Learning Approaches Using CNN and OpenCV*, IEEE Global AI Summit (doi 10.1109/GlobalAISummit62156.2024.10947974) | Small CNN predicts gender (98.2%) and handedness; lines found with Canny + Hough. | Useful point: palmistry needs to know handedness. |
| Patil 2025, *Palmistry-Informed Feature Extraction and Analysis using ML*, [arXiv 2509.02248](https://arxiv.org/abs/2509.02248) | Edge features → Random Forest / SVM → personality category. About 400 images. | **Circular labels:** the training labels come from palmistry rules, so "accuracy" only measures agreement with those rules. The paper disclaims itself honestly as entertainment. Good model for our framing. |
| Anand et al. 2020, *Can Cheiromancy Predict … ALS?*, J Neurosci Rural Pract ([PMC7195958](https://pmc.ncbi.nlm.nih.gov/articles/PMC7195958/)) | PGIMER Chandigarh; palmists read palms blind (ALS patients vs controls). | Inconclusive. Do **not** cite as evidence that palmistry works. |

---

## 3. Extracting principal lines (biometrics literature)

| Paper | Key idea | Use for us |
|---|---|---|
| Huang, Jia & Zhang 2008, *Palmprint verification based on principal lines*, Pattern Recognition 41(4) (doi 10.1016/j.patcog.2007.08.016) | **MFRAT** (modified finite Radon transform) extracts principal lines even with strong wrinkles. | Deterministic baseline, and a generator of **pseudo-labels** for training data. |
| Liu, Zhang & Wang 2005, *Palm-line detection*, ICIP ([open PDF](https://ira.lib.polyu.edu.hk/bitstream/10397/1203/1/palm-line-detection_05.pdf)) | SUSAN-like crease detector. Beat Canny on PolyU. | Classical fallback. |
| **Pham Van et al. 2020, *Efficient Palm-Line Segmentation with U-Net Context Fusion Module*** ([arXiv 2102.12127](https://arxiv.org/abs/2102.12127)) | U-Net + attention context fusion, 256×256 input, 94 FPS. 1,039 images from 11K Hands, annotated and augmented to 4,156. | **Closest to our core model.** mIoU is 0.584. Its F1 of 99% is inflated by background pixels, so mIoU is the honest metric. The dataset link redirects **[availability unverified]**. Its licence follows 11K Hands (academic only). |
| Fan et al. 2022, *Palmprint Phenotype Feature Extraction and Classification Based on DL*, Phenomics ([PMC9590507](https://pmc.ncbi.nlm.nih.gov/articles/PMC9590507/)) | HED line extraction (480 labelled images) + ResNet34 classifying crease type: normal / **Sydney** / **simian** / triple, at 95.7%. | Shows deep learning can classify crease *topology*. The dataset (10,502 images) is not public. |
| Wang & Lv 2025, *Palmprint recognition based on principal line features*, PeerJ CS ([PMC12453761](https://pmc.ncbi.nlm.nih.gov/articles/PMC12453761/)) | A wide-line extraction filter plus a Gabor filter that removes fine wrinkles. | Practical recipe for separating principal lines from minor creases. |
| Zhang et al. 2020, *Towards Palmprint Verification On Smartphones* ([arXiv 2003.13266](https://arxiv.org/abs/2003.13266)) | **MPD** dataset: 16,000 smartphone images, 200 people. Keypoint-based cropping to the region of interest. | Closest to our real input photos. The cropping pipeline is reusable. |
| Gao et al. 2025, *Deep Learning in Palmprint Recognition — A Comprehensive Survey* ([arXiv 2501.01166](https://arxiv.org/abs/2501.01166)) | Survey; lists 17 datasets. | **Warning on domain gap:** one model scores 100% on the Tongji dataset but 24% on the NTU-PI dataset. Budget for our own data. |
| Lan et al. 2025, *Canny2Palm* ([arXiv 2505.04922](https://arxiv.org/abs/2505.04922)) | Pix2Pix model generates realistic palm images from Canny line maps. | A route to **synthetic paired training data** (line mask ↔ photo). |

---

## 4. Hand landmarks, segmentation and measurements

- **Zhang et al. 2020, *MediaPipe Hands: On-device Real-time Hand Tracking*** ([arXiv 2006.10214](https://arxiv.org/abs/2006.10214))
  - Two stages: a palm detector, then a model that predicts **21 landmarks** plus handedness.
  - Trained on real and synthetic data.
  - Use it for four things:
    1. The quality gate: is there a palm, and is it facing the camera?
    2. Left/right hand detection.
    3. Normalising rotation and scale using landmarks 0, 5, 9, 13 and 17.
    4. Cropping to the region of interest.
  - ⚠️ Its landmarks sit at the **centres of the joints**, not on the skin creases. Finger lengths measured from them are therefore approximate.
- **Urooj Khan & Borji 2018, *Analysis of Hand Segmentation in the Wild*** (CVPR, [open PDF](https://openaccess.thecvf.com/content_cvpr_2018/papers/Urooj_Analysis_of_Hand_CVPR_2018_paper.pdf))
  - Produces pixel-level hand masks (81.4% mIoU on EgoHands).
  - Useful for removing the background.
- **Afifi 2019, *11K Hands*** ([arXiv 1711.04322](https://arxiv.org/abs/1711.04322))
  - 11,076 images from 190 people, on a white background, with age, gender and skin-tone metadata.
  - Licence: **academic fair use only.**
- **Measuring the 2D:4D ratio from images** (computer-assisted reliability studies)
  - Reliable when the hand is flat, the camera points straight down, and the finger length is measured from the base crease of the finger.
  - Sources: Am J Hum Biol (doi 10.1002/ajhb.20892); BMC Med Imaging 2015 ([PMC4323124](https://pmc.ncbi.nlm.nih.gov/articles/PMC4323124/)).
- **Hand "types"** (earth / air / fire / water; conic and similar)
  - **No peer-reviewed validation.**
  - Measurable hand-geometry ratios, such as palm length to palm width, are a sound basis if we describe them as descriptive only.

---

## 5. Palm features with real scientific evidence

| Feature | Evidence | Product rule |
|---|---|---|
| **Single transverse palmar crease** ("simian line") | Found in 1.5–3% of the general population. **Varies hugely by ethnicity**: 14.6% of Nepalese children and 71% in the Lama group (Malla et al. 2010, doi 10.3126/kumj.v8i4.6241). Found in 89% of children with Down syndrome (Kaya & Alavanda 2024, [PMC11457039](https://pmc.ncbi.nlm.nih.gov/articles/PMC11457039/)). | Describe it neutrally as a common variation. **Never** hint at any medical condition. |
| **2D:4D digit ratio** | Manning et al. 1998, *Hum Reprod* (doi 10.1093/humrep/13.11.3000). Meta-analysis by Hönekopp & Watson 2010 (116 samples, ~25,000 people): a robust group-level sex difference, but **self-measured ratios are only about 46% as reliable** as expert measurements. No predictive value for prostate cancer (Salomão et al. 2014). | Fine as a fun "measured fact" compared with the population average (~0.95–0.98). No predictions about traits or health. |
| **Dermatoglyphics** | Penrose 1973, *Fingerprints and palmistry*, Lancet (doi 10.1016/s0140-6736(73)90543-6): the classic paper separating the science of skin-ridge patterns from palmistry. | Keep fingerprint/ridge science separate from the palmistry reading. |

---

## 6. Does palmistry work? The evidence

**Life line vs lifespan**

- **Wilson & Mather 1974**, *JAMA* 229(11):1421 (doi 10.1001/jama.1974.03230490023011): 51 cadavers. No significant correlation after correcting for body size.
- **Newrick, Affie & Corrall 1990**, *J R Soc Med* 83(8):499 ([PMC1292776](https://pmc.ncbi.nlm.nih.gov/articles/PMC1292776/)): 100 autopsies. Found a "highly significant" association, but the authors themselves note that **creases lengthen with age as skin wrinkles**, so the result is confounded. The reply letters include *"I don't fancy cheiromancy"* (1991).
- **Lucas, Dhugga & Henneberg 2019**, *Anthropological Review* 82(2):155 (doi 10.2478/anre-2019-0011, open access): 60 cadavers. **No significant correlation.**

**Reviews**

- Toren et al. 2024, *Metoposcopy redux*, Clin Dermatol: classes palmistry as a pseudoscience.
- Furnham 2000, J Altern Complement Med: a study of what people believe works, not of whether it works.
- Pejic 2008, J La State Med Soc: frames palmistry as a kind of supportive psychotherapy or placebo.

**Why readings feel accurate**

- **Forer 1949**, *J Abnorm Soc Psychol* 44(1):118. Every student received the same generic sketch and rated it as highly accurate about themselves.
- **Dickson & Kelly 1985**, *Psychological Reports* 57:367 (doi 10.2466/pr0.1985.57.2.367): a review of the Barnum effect. People accept vague statements more readily when they are favourable and seem personal.
- **Hyman 1977**, *"Cold reading"*, The Zetetic 1(2): describes palmistry as a vehicle for cold reading.

**Implication for your validation study**

User-rated accuracy will be high for *any* flattering reading. A study is only informative if it compares against a **control reading**, such as another person's palm features or a shuffled reading, shown blind. The strongest design is **prospective**: record predictions, then check later life events. Pre-register the hypotheses before collecting data.

---

## 7. Vision-language models on hands

- **HandVQA** (CVPR 2026, [arXiv 2603.26362](https://arxiv.org/abs/2603.26362)): more than 1.6M questions about hand geometry. LLaVA, DeepSeek and Qwen-VL **hallucinate finger parts and misread geometry**. Fine-tuning with LoRA helps.
- **SafeGesture** ([arXiv 2608.16081](https://arxiv.org/abs/2608.16081)): GPT-4o recognises gestures 98.4% of the time but picks the right action only 53% of the time. Models rarely say "uncertain".
- **No published evaluation of VLMs reading palm lines exists.** Assume a VLM given a raw photo will confidently describe lines it cannot actually locate. Give it measured features instead of asking it to read the photo.

---

## 8. Datasets

| Dataset | Size | Capture | Access / licence | Line labels? |
|---|---|---|---|---|
| Pham Van et al. palm-line set (from 11K Hands) | 1,039 (4,156 augmented) | White background | Link redirects **[unverified]**; academic | **Yes**: masks, but lines not labelled by type |
| CAS_Palm (Fan 2022) | 10,502 images / 5,251 subjects; 480 with line labels | Unconstrained | **Not public** | Yes (480) + crease type |
| 11K Hands | 11,076 / 190 subjects | White background | Academic fair use | No (skin masks only) |
| MPD / MPD-v2 (Tongji mobile) | 16,000 / 200 subjects | Smartphones | Baidu Pan; assume academic | No (keypoints, region crops) |
| Tongji contactless | ~12,000 / 300 subjects | Controlled | Academic request | No |
| IITD touchless | 230 subjects | Contactless | Academic request | No |
| CASIA palmprint | 312 subjects | Contactless | Academic request | No |
| PolyU 2D | 7,752 / 193 subjects | Contact, 128×128 crops | Academic | No |
| XJTU-UP | 200 palms, 5 phones | Smartphone | Academic request | No |
| NTU-CP-v1 / NTU-PI-v1 | 2,478 / 7,781 images | Contactless / scraped from the web | Academic | No |
| X-Palm (2026) | 6,006 / 103 people | Multispectral + phone | CC BY 4.0 + EULA, **non-commercial** | No |
| Roboflow Universe community sets ("Palmistry_seg", "Palm lines recognition", "Palm_lines" and others) | Hundreds to ~1,000 | Web + phone | Reported as CC BY 4.0 **[unverified]** | **Yes, labelled by line type** (life/head/heart/fate) |
| EgoHands / EgoYouTubeHands / HandOverFace | Thousands of frames | Egocentric | Research | No (hand masks) |

**Conclusion:**
- Good smartphone photo sets exist, but they are academic-only and have no line labels.
- Sets that do have line labels are small, or of uncertain quality and licence.
- **We must collect and annotate our own data, with user consent.**

---

## 9. Takeaways for product design

1. **Hybrid pipeline:**
   - MediaPipe as the quality gate and for normalisation.
   - A U-Net-class model to segment the lines, with MFRAT / wide-line / Gabor filters as pre-processing or pseudo-labels.
   - **Deterministic rules** that decide which line is which from its position relative to the landmarks. For example, the heart line is nearest the finger bases on the little-finger side, and the life line arcs around the base of the thumb.
   - An LLM only to turn measured features into prose.
2. **Build our own data:**
   - Consented smartphone photos.
   - Polyline annotations for each line.
   - MFRAT pseudo-labels to bootstrap.
   - Optional synthetic images in the style of Canny2Palm.
   - Do not ship model weights trained on 11K Hands, MPD or X-Palm without written permission.
3. **Metrics:**
   - Report mIoU and per-line recall, not pixel F1.
   - Expect a large drop in accuracy on real user photos.
   - Always offer a "retake photo" path.
4. **Honest framing:** present readings as entertainment or self-reflection. Cite the life-line studies and the Barnum effect on an "About our method" page.
5. **Hard red lines:** no lifespan predictions from the life line; no links between creases and disease; no health readings from colour or finger ratios.
6. **A "measured facts" layer** gives credibility without false claims. It would include:
   - 2D:4D ratio compared with the population average, with a reliability caveat.
   - Palm length-to-width ratio.
   - Handedness.
   - Crease topology, described only.
7. **Capture guidance:** flat, open palm; fingers slightly spread; even light; plain background. Enforce this with landmark, blur and exposure checks.
8. **Fairness:** line visibility varies with skin tone and age, and crease prevalence varies by ethnicity. Evaluate the model across these groups.
9. **Privacy:** palmprints are biometric identifiers; the best biometric systems match them with error rates below 1%. Process on-device where possible, keep data only briefly, get explicit consent, and never use the images to identify people. This matters under India's DPDP Act, GDPR Art. 9 and Illinois BIPA.

Research notes and PDFs are in the session scratchpad (`papers/`).
