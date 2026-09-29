# Automated Palm-Reading Products: How They Work

**Research date:** 2026-09-29
**Method:** Only public material was used: store listings, marketing pages, public JS bundles, privacy policies, reviews, blogs and GitHub. No photos were uploaded, no forms submitted, no accounts created and nothing was bought.
**Evidence labels:** **[C]** = confirmed directly from code, a listing, a policy or a quote. **[I]** = inference.

Companion reports:
- [02-open-source-resources.md](02-open-source-resources.md): code, models, datasets and books
- [03-academic-literature.md](03-academic-literature.md): papers, scientific evidence and datasets

---

## 1. Executive summary

1. **No product we examined has a palmist in the loop.** Every product is one of five technical tiers, shown in the table below. Most commercial winners sit at tier 2–3. The fast-growing long tail since 2025 is tier 4.

   | Tier | What it does | Examples |
   |---|---|---|
   | 0 | Fake or random output | Low-end ad-ware apps |
   | 1 | The user answers questions about their own lines | Questionnaire apps |
   | 2 | Real hand detection, but mostly templated text | Nebula, tarotbyvela |
   | 3 | Measured line geometry feeding a rule engine | Astroline, Palmist (Global Sense) |
   | 4 | Photo sent to a vision LLM (GPT-4.1-mini, Azure OpenAI, GPT Image 2, Grok) | Palmist.io, GPTPalm, Overchat |

2. **The industry shares one data model.** Nebula, Astroline and tarotbyvela all return:
   - 21 hand landmarks (MediaPipe topology) or 5 fingertips;
   - one polyline per line: heart, head, life, fate ("money"), marriage;
   - per-line scalar features: length, curvature, depth;
   - enumerated failure codes (NO_HAND, INCORRECT, TIMEOUT).
3. **The "prediction" usually does not come from the palm.**
   - tarotbyvela's dated periods come from **Vimshottari dasha**.
   - Nebula's paywall teaser is **static copy**, and its "Only 0.7% of users…" headline is filled from a **quiz answer**.
   - The palm scan works as a *trust device*: a real detector plus an overlay drawn on your own photo. The text engine behind it is often generic.
4. **The money is in the funnel, not the reading.** The dominant models are:
   - a $1 trial that auto-renews at $39.99–$71.50 a month (Nebula) [C];
   - chat with an astrologer or AI advisor at ₹4 per message or ₹25 per minute (Palmist.io) [C].
   The top complaint across the category is being charged unexpectedly after a trial. Nebula has **1.5/5 on Trustpilot**.
5. **Nobody publicly proves honesty.** No product publishes:
   - a test showing it rejects non-palm images;
   - a consistency test (same palm, same reading);
   - a line-detection accuracy score.
   This is the clearest opportunity for us.

---

## 2. Deep dive: astro.tarotbyvela.com

This is the site we analysed first, working from its unminified client JS.

| Stage | Where | What happens |
|---|---|---|
| Capture | Browser | `getUserMedia` opens the rear camera at 1440×1920 with a hand-outline guide. A gallery upload is the fallback (image files only, under 20 MB). |
| Bot gate | Browser → server | Cloudflare Turnstile issues a challenge token, which `/api/palm/scan-token` exchanges for a short-lived scan token. |
| Detection | Server `/api/palm/detect` | Returns `hand_points` (21 landmarks), `lines.{love,life,head,fate}` (up to 48 points each), `line_quality` (flags lines marked `estimated` or `source:'template'`), `is_flipped` and `angle_rotate`. The scan passes if at least 2 real lines are found. An HTTP 422 means the photo was rejected. |
| Mounts | Browser | **Not detected.** Each mount is a weighted average of landmarks; for example, Jupiter is the index-finger base moved 12% toward the wrist. A code comment says: *"presentation anchors… never newly detected lines."* |
| Reading | Server `/api/reading` | Receives palm JSON, name, DOB, birth time, place and coordinates, plus quiz answers. |
| Report | Server → browser | Six modules: career, money, recognition, love/marriage, family/children, energy. Each has "windows" (dated periods), reasoning blocks and "calculation details". The dates come from **Lagna, houses and dasha**; the code mentions "dasha" 165 times. |
| Face product | Browser | MediaPipe FaceLandmarker runs **on-device** in a Web Worker. |

**Lesson:** a clean tier-3 pipeline paired with astrology produces a convincing report. But palm and astrology signals are blended and not labelled separately, so you cannot tell which one generated a given claim.

---

## 3. Competitor comparison

| # | Product | Market | Popularity | Monetisation | Tier | Extra inputs |
|---|---|---|---|---|---|---|
| 1 | **Nebula** (Obrio) web funnel + app | Global | iOS 4.6★ / 171K; Play 5M+; Trustpilot 1.5/5 | $1–$13.67 trial → $39.99–$49.99/mo; £4.99–£19.99 report upsells; psychic chat | 2–3 | Gender, handedness, goal, DOB, place, 10+ quiz steps, email |
| 2 | **Astroline** (Appsella) | Global | Play 10M+, 3.9★ | Subscription + per-minute chat + coins | 3 | Birth data, **both hands** |
| 3 | **Hint** | Global | Trustpilot 4.1 (34K) | Weekly subscription (£14.99/wk complaint) | ? (marketed as AI) | Birth chart |
| 4 | **Palmist** (Global Sense) | iOS | 4.1★ / 4.5K | $7.99/wk to $89.99/yr | 3, **user can edit detected lines** | Fingerprints, hand shape |
| 5 | **PalmistryHD** | Global | Play 500K+ | £7.99/mo, credits, psychic chat | ? ("biometric algorithm") | Name, DOB |
| 6 | **MagicWay** | Android | 4.6★ / 43K | Hard paywall right after the scan; $49.99 lifetime | ? | Zodiac |
| 7–14 | Touchzing, Digitalists, PavelDev, WhiteStar, Palm Reader Master and others | Mostly Android | 100K–1M+ each | Ads, rewarded-ad loops, small in-app purchases | 0–2 | Zodiac or quiz |
| 15–17 | Bitscorp, AI Studio, Palmistry GPT-AI | Android/iOS | Small | Pay per scan or coins | **4** ("OpenAI API", "ChatGPT") | — |
| 18 | **Palmist.io** | **India**, 13 languages | — | Free reading → AI astrologer ₹4/msg, ₹25/min | **4** (Azure OpenAI) | Name, DOB/time/place |
| 19 | **GPTPalm** | Web | — | Free | **4** (GPT-4.1-mini) | Both palms, age, gender |
| 20 | **Overchat** | Web | — | Credits | **4 + image** (GPT Image 2 annotated infographic) | Dominant or non-dominant hand |
| 21 | aipalmreading.net / palmreading.pro | Web (SEO sites) | — | Free preview → $3.99 report | **4** (ShipAny boilerplate via OpenRouter) | — |
| 22 | iWeaver, Pokecut, Jenova, media.io | Web AI suites | Pokecut claims 1M users | Credits, $20/mo | 4 | — |
| 23 | **PANDIT AI** | **India** | — | App consultations | Claims CV → classifier → Vedic rule engine | Both hands |
| 24 | KundliChat, Astroyogi | **India** | Astroyogi 500K+ | Free → astrologer chat | In-browser scan (KundliChat); manual selection (Astroyogi) [I] | Name, DOB, relationship status |

**Not found:** AstroSage, Astrotalk and Moonly have **no automated palm scan**. They sell palmistry only through human consultations. The biggest Indian astrology platforms leave this open.

---

## 4. The most instructive products

### 4.1 Nebula: the reference "web2app" palm funnel [C]

**Funnel sequence** (from `__NEXT_DATA__`):
gender → hand usage → goal → DOB → about 7 psychological questions → *fake* "Connecting to database…" screen with "We've helped {{N}} women with a {{zodiac}} sun sign" → "which line matters most?" → scan → an "analysing" animation that asks more quiz questions while it runs → email → **trial paywall** → upsells.

**How the scan works:**
- The browser POSTs a PNG to `/readings/palmistry/detect`.
- The response contains `life/heart/head/marriage/fate_line_pts` and five fingertip points.
- `fate_line_pts` is **relabelled "money line"** in the UI.
- There is a real rejection message: "Unfortunately, we were unable to detect a palm…"

**Growth stack:**
- GrowthBook for A/B tests.
- Amplitude for analytics.
- An `ltv-predict` endpoint that feeds the Facebook purchase value.
- Price IDs such as `1_USD_7d_trial_30d_49_99_palm`, with a countdown timer and testimonial carousel.

### 4.2 Astroline: the richest scan payload [C]

- **Service:** `hand-detection.astroline.today` with `/palm/` and `/lines/` endpoints. It includes a hard-coded 21-point hand template.
- **Per-line features:** `curvature`, `depth`, `length`, `lineScore`, `lineSuggestion`.
- **Derived fields:** marriage probability at ages 20, 40, 60 and 80; number of children; earnings by age; MBTI-like axes; top careers.
- **⚠️ Health fields:** `lifeExpectancy` and `risk_cancer`, `risk_stroke`, `risk_alzheimer`, `risk_heart_disease` and similar. This is a regulatory landmine to avoid.
- **Advisor handoff:** the full two-hand reading is flattened into a **hidden message** sent to the astrologer chat. The advisor looks informed, which makes paid chat feel personal.

### 4.3 Palmist.io: an India-first vision-LLM product [C]

- Six lines (including marriage and money), mounts, 13 languages.
- **Photo handling:** the photo is sent to **Azure OpenAI**. The policy says: "We don't keep it — only the text reading is saved." It cites India's **DPDP Act 2023**.
- **Framing:** an honest disclaimer ("tradition, not science").
- **Revenue:** from AI astrologer chat, not from the reading itself.

### 4.4 Bitscorp: the unit economics of vision LLMs [C]

The developer replied to a review: *"every scan has the price for me… I started to have the huge bills for ai."*
Sending every raw photo to a vision LLM forces a paywall on every scan.

### 4.5 The low end (tiers 0–1)

- Palm Reader Master: *"used the same hand twice and it gave two different results."*
- WhiteStar: always outputs "Libra" regardless of input, and runs endless ad loops.
- Touchzing: readings are identical across users.
- A top review on another app asks: *"I would like it to actually scan the palm."*
- **Nobody has publicly run the "scan your foot" test** on any of these apps.

---

## 5. Cross-cutting patterns

### 5.1 Report content

- **Lines everyone covers:** life, heart, head and fate.
- **Commercial hooks:** marriage and money lines.
- **Mostly Indian products:** Sun (Apollo) and Mercury lines.
- **Mounts** (seven Vedic/Western): only the richer products.
- **Hand shape / elements** (Earth, Air, Fire, Water): mainly LLM products.
- **Both hands:** the story "left hand = innate, right hand = lived" is universal. It doubles scan engagement.
- **Timelines:** Astroline uses age buckets; tarotbyvela uses dasha dates; most products avoid dates entirely.
- **Visual overlay on the user's own photo:** the single strongest "it really scanned me" cue.
- **The report as a lead magnet:** the scan feeds the context of an advisor chat, and the chat minutes are the revenue.

### 5.2 Dark patterns to avoid

1. A $1 trial that turns into a $40–$70 monthly subscription.
2. Scan first, then a paywall, exploiting the effort already invested.
3. Static or quiz-filled teaser text presented as a palm insight.
4. Fake "connecting to database" screens, fabricated "just scanned" notifications, countdown timers.
5. Coins bought *before* the photo-quality check (Palmistry GPT-AI charged first, then rejected the photo).
6. Forced rating prompts before any value is delivered; rewarded-ad loops.
7. Ambiguous or pre-selected plan tiles.

### 5.3 Ethical monetisation seen in the market

- A one-time $3.99 report (palmreading.pro).
- A free reading plus pay-per-message chat (Palmist.io).
- "No subscriptions, on-device processing" (Tamizha).

---

## 6. Privacy and regulation

*General observations, not legal advice.*

**What products do with the photo:**

| Handling | Products |
|---|---|
| Raw images kept long-term | Nebula (`palmistry_photo_id`, `GET /palmistry/scan`); Astroline (`left_hand_path` / `right_hand_path`); palmreading.pro ("for service-quality review") |
| Claims no retention | Palmist.io, iWeaver, KundliChat, aipalmreading.net |

**Laws that apply:**

- **GDPR / UK GDPR:** a palm photo becomes "biometric data" under Art. 4(14) when it is technically processed in a way that allows unique identification. High-resolution palmprints *can* identify a person. Treat them conservatively: explicit consent, minimisation, short retention.
- **Illinois BIPA:** explicitly covers a "scan of hand geometry", which is about 11% of BIPA cases. The risky pattern is **extracting landmark geometry tied to a logged-in, named user**, which is exactly what detect endpoints do. BIPA requires written consent and a published retention schedule, and forbids selling the data. Texas and Washington have similar laws.
- **India DPDP Act 2023 + DPDP Rules (notified 14 Nov 2025):**
  - There is no special "sensitive" category.
  - The main obligations (notice, security, breach reporting, rights) start on **14 May 2027**.
  - Consent managers start in November 2026.
  - Verifiable parental consent is required for minors, which matters because the audience skews young.
- **Public mood:** the April 2026 ChatGPT palm-reading trend triggered "they now have your palm data" memes. **Privacy is now a marketable feature.**
- **Health claims:** lifespan or disease predictions (as in Astroline) create exposure under consumer-protection law and app-store rules.

---

## 7. Lessons for our portal

These are adapted to our direction: **India + global storefronts, palm and astrology engines kept separate for a validation study, rules sourced from books.**

### Architecture

1. **Hybrid tier-3+ pipeline.**
   - On-device MediaPipe quality gate.
   - Rectify to a canonical palm.
   - Palm-line segmentation model.
   - **Measured features**: length relative to palm width, curvature, start and end points relative to landmarks, breaks, forks, islands.
   - **Rule engine** (from the books) → meaning codes.
   - LLM writes prose **only from the feature JSON**.
   - Never let a VLM invent lines it cannot localise.
2. **Separate engines with provenance on every claim.** Each sentence carries `source: palm | astro | quiz` and the feature IDs that triggered it.
   - This is the **foundation of your validation study**, and it is more honest than tarotbyvela's or Nebula's blending.
   - Keep the two engines able to run independently, so the same user can receive "palm only", "astro only" and "combined" versions.
3. **Deterministic readings.**
   - Cache by a perceptual hash of the normalised palm crop.
   - Use fixed templates, or an LLM at temperature 0.
   - Show "why": *"Your heart line ends under the index finger → …"*
4. **A strict palm gate as a marketing asset.**
   - Specific rejection reasons: NO_HAND, BACK_OF_HAND, FINGERS_CLOSED, TOO_DARK, BLURRY, TOO_FAR.
   - The pitch: "Try it with your foot, we'll refuse."
   - **Charge only after the gate passes.**
5. **Editable overlay.** Draw coloured polylines on the user's photo and let the user nudge a line that is wrong, as Palmist (Global Sense) does.
   - Better UX.
   - Consented, human-corrected **training labels**, which fill the biggest data gap in the field.
6. **Cost control.**
   - Detection and segmentation run on-device or at the edge (ONNX / WebGPU).
   - Only compact feature JSON goes to a mini LLM.
   - Cache per palm.

### Data capture for the validation study (specific to our plan)

7. For each user, store these as **separate, versioned records**:

   | Record | Contents |
   |---|---|
   | (a) Palm features | Numeric, no image by default |
   | (b) Astro chart and dasha | |
   | (c) Quiz / self-report | |
   | (d) Generated statements | Tagged with their source |
   | (e) User feedback | Per-statement accuracy rating |
   | (f) Optional follow-ups | Life events later (marriage, job change) for prospective checks |

8. **Blind A/B arms.** Randomly show a palm-only, astro-only, combined or **shuffled-control** reading (another user's palm features). Ask users to rate accuracy.
   - The shuffled control is essential: it measures the **Barnum effect** baseline (see report 03).
   - Without it, any "accuracy" number is meaningless.
9. **Test–retest.** Two photos of the same hand should give the same features. Publish the agreement rate.

### Product and market

10. **India depth:**
    - Hast Rekha / Samudrika terminology alongside the Western terms.
    - Sun, Mercury, marriage and children lines; bracelets (manibandh).
    - Hindi plus regional languages.
    - UPI via Razorpay.
    - ₹ micro-pricing (inferred ₹99–₹299 one-time report).
11. **Global storefront:** Western terminology, USD, GDPR/BIPA consent flow, 18+ gate.
12. **Honest monetisation:**
    - Free rich reading before any email wall.
    - Paid one-time deep report or PDF.
    - Pay-per-question AI chat grounded in the user's own features (show the user what context the chat sees; no hidden message).
    - An optional, clearly priced subscription (two-hand comparison, yearly "your palm changed" history).
13. **Hard red lines:** no lifespan, disease or fertility predictions. Describe a single transverse crease (simian line) neutrally, never medically.
14. **Privacy as a feature:**
    - On-device processing wherever possible.
    - Downscale images to avoid fingerprint-grade resolution.
    - Raw images deleted within 24 h unless the user opts in.
    - Explicit consent checkbox; named AI sub-processors with no-training terms.
    - Notice in English + Hindi.
    - Say all of this **on the scan screen** itself.
15. **Publish an "accuracy and consistency" page**: non-palm rejection rate, test–retest agreement, segmentation Dice score, and (later) validation-study results. No competitor does this. It is a trust moat, and AI answer engines tend to cite pages like it.
16. **Shareable cards** for Instagram and WhatsApp, rendered deterministically from our own polylines. This matches the GPT-Image "annotated palm" trend at near-zero cost.
17. **SEO long tail:** a page per line, per life area and per question, in Hindi and regional languages, with the scanner embedded. Keep Turnstile on the upload endpoint; no account needed for the first reading.

---

## 8. Gaps and unverified items

- The scan internals of Hint and PalmistryHD were not inspected (no public bundle).
- PANDIT AI's claim of "millions of palm images" is unverified.
- No public "non-hand object" test exists for any product. We could run one ourselves later with dummy images.
- The Indian one-time-report price range is an estimate.

## Key sources

- Nebula: [funnel](https://appnebula.co/palmistry), [App Store](https://apps.apple.com/us/app/nebula-horoscope-astrology/id1459969523), [Trustpilot](https://www.trustpilot.com/review/appnebula.co)
- Astroline: [Play](https://play.google.com/store/apps/details?id=com.fortunescope&hl=en_US)
- [Palmist.io](https://palmist.io/) · [GPTPalm](https://gptpalm.com/en) · [Overchat](https://overchat.ai/ai-hub/ai-palm-reading) · [PANDIT AI](https://pandit.ai/palm-scanner) · [KundliChat](https://kundlichat.in/free-palm-reading-online)
- Bitscorp: [Play](https://play.google.com/store/apps/details?id=co.bitscorp.palm&hl=en)
- Regulation: [GDPR Art. 4](https://gdpr-info.eu/art-4-gdpr/) · [DPDP Rules 2025 (PIB)](https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf) · [BIPA – ABA](https://www.americanbar.org/content/dam/aba/publications/antitrust/source/2025/june/biometric-privacy-litigation.pdf)
- ChatGPT palm trend: [letsdatascience](https://letsdatascience.com/news/viral-chatgpt-palm-reader-trend-raises-biometric-privacy-con-529dbbcf)

Evidence files (downloaded bundles and listings) are in the session scratchpad (`competitors/`).
