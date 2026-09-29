# Architecture Decision Log

Each decision records its context, the choice made, the alternatives, and what would make us revisit it.
Statuses: **Accepted** / **Proposed** / **Superseded**.

---

## D-001: Palm and astrology run as independent engines; they are not blended in v1
**Status:** Accepted (owner direction, 2026-09-29)

- **Context:**
  - Competitors blend palm, astrology and quiz answers, then present the result as a "palm reading" (see research 01).
  - The owner wants to test whether palm-only, astro-only or combined readings carry any signal.
- **Decision:**
  - Palm and astrology are separate modules. Each has its own inputs, output contract and rules.
  - Every statement records its `source_engine`.
  - The `combined` reading shows both sets side by side, labelled, with no fusion logic.
  - A study harness with a shuffled control arm is part of the core scope.
- **Revisit:** after the pre-registered study reaches its planned sample size.

## D-002: Hybrid pipeline in which the LLM only narrates
**Status:** Accepted

- **Context:**
  - Readings driven purely by a vision LLM are not reproducible and can invent lines.
  - The VLM benchmark papers show hallucinated hand geometry (research 03 §7).
  - Per-scan LLM cost pushes products into aggressive paywalls (the Bitscorp example).
- **Decision:** MediaPipe gate → rectify → segmentation → measured features → JSONLogic rules → the LLM turns the fired rules into prose. The LLM never receives the image.
- **Alternatives:** VLM-only (cheapest to build, least honest); rules-only with templates (kept as the fallback).
- **Revisit:** if a VLM passes our line-localisation evaluation at a level comparable to the segmenter.

## D-003: Monorepo with Next.js, a Python engine and a database behind adapters
**Status:** Accepted. Supabase replaced by SQLite for the POC (see D-012).

- **Decision:**
  - pnpm + Turborepo for TypeScript.
  - uv for Python.
  - One Python FastAPI "engine" service holding the palm, astro and rules modules.
  - Persistence behind adapters (SQLite + local files in the POC).
- **Why a single engine service:** a solo builder should keep the number of deployable units small. Module boundaries plus separate contracts give the independence we need without separate services.
- **Revisit:** if astrology traffic scales differently from palm traffic, or GPU inference becomes necessary.

## D-004: Mobile is built with Expo (React Native) alongside the web app; the authoritative quality gate runs on the server
**Status:** Accepted

- **Context:** the owner wants web and mobile together.
- **Options considered:**
  - A Capacitor wrapper of the web app: least code, but Apple's rule 4.2 against thin web wrappers is a risk, and a Next.js app with server rendering is awkward to wrap.
  - Flutter: no code shared with the TypeScript side.
  - Expo: shares types, API client, i18n and logic with the web app.
- **Decision:** Expo.
  - The server runs the authoritative MediaPipe gate, so both clients behave identically.
  - Web gets a live on-device guide from day one.
  - Mobile gets a static guide in v1. An on-device live guide (MediaPipe via a vision-camera frame processor, or an ONNX palm detector) comes in v2.
- **Revisit:** if maintaining two UIs becomes a bottleneck. Then consider Expo Router for web, or reducing the web app to a landing-plus-funnel site.

## D-005: jyotishganit (MIT) is the default astrology provider; AGPL providers are optional add-ons
**Status:** Accepted (revised by D-011). **Validated 2026-09-30** against Swiss Ephemeris: planets ≤ 0.003°, nodes 0.0007° after our precession fix, dashas ≤ 1 day (docs/eval/astro-validation.md). No commercial Swiss Ephemeris licence is needed for accuracy.

- **Context:** pyswisseph, kerykeion and PyJHora are AGPL. Swiss Ephemeris needs a paid professional licence for closed-source hosted use.
- **Decision:**
  - Use jyotishganit (Skyfield + JPL DE421) as the default `EphemerisProvider`.
  - Implement pyswisseph and PyJHora providers in `adapters-agpl/`.
  - Compare all providers on reference charts.
- **Outcome:** if the AGPL providers are measurably better, the owner seeks permission or buys the Swiss Ephemeris Professional licence. Otherwise we stay on MIT.

## D-006: Line-segmentation weights, prototype vs production
**Status:** Accepted

- **Context:**
  - The palm-line-reader code is MIT, but its weights were trained on photos scraped from Reddit.
  - PLSU has no licence.
  - Roboflow sets are CC BY 4.0 but their image sources are undocumented.
  - 11K Hands, IITD and PolyU are academic-only.
- **Decision** (revised by D-014):
  - During R&D, **any** dataset or weights may be used internally. They stay git-ignored and are listed in `data/manifest.yaml` and `docs/RESOURCES-REGISTRY.md`.
  - The prototype (Phase 1) may use palm-line-reader weights and PLSU-trained weights **internally**.
  - **Production uses only weights trained on:**
    1. images we have consent for;
    2. CC BY / public-domain sets after a provenance audit, with attribution;
    3. synthetic data from Apache-licensed generators.
  - Every model has a model card listing its training data licences.
  - Avoid GPL/AGPL code: no Ultralytics, and no milesial U-Net code. Use SMP (MIT) instead.

## D-007: Raw palm images are deleted after 24 h by default
**Status:** Accepted

- **Context:**
  - Palm images are biometric-adjacent (BIPA "hand geometry", GDPR Art. 9 risk, DPDP duties from May 2027).
  - Public sentiment after the 2026 ChatGPT palm trend makes privacy a selling point.
- **Decision:**
  - Keep derived features only.
  - Keep images longer only with explicit `retain_images` or `training_data` consent.
  - Enforce deletion with the scheduled cleanup job (`scripts/cleanup-uploads.ts`) and audit it via `image_deleted_at`.
  - This applies to user uploads in the app. R&D datasets under `data/` are governed by D-014.

## D-008: Rules stored as versioned YAML with JSONLogic conditions and mandatory citations
**Status:** Accepted

- **Decision:**
  - Rules live in git.
  - They are validated by a JSON Schema and a lint in CI (citations present, no banned health or lifespan categories, only features that exist).
  - Each approved release is snapshotted to `rulebase_releases`.
  - Statuses: extracted → reviewed → approved.
- **Why:** reviewable by the owner, easy to diff, deterministic, runs in both TypeScript and Python.

## D-009: No health, lifespan, disease or fertility statements
**Status:** Accepted

- **Context:**
  - The life-line/longevity studies are null or confounded.
  - The single-palm-crease finding carries a medical-stigma risk.
  - Astroline's `risk_cancer` fields show the regulatory hazard.
- **Decision:**
  - A banned-category list is enforced in the rule lint, the narrator prompt and a post-generation filter.
  - "Vitality" is framed as lifestyle energy only.

## D-010: Market-aware storefronts share one codebase
**Status:** Accepted

- **Decision:** `market` (`in` | `global`) and `locale` are part of the route and the profile. The market config chooses:
  - legal copy and consent text;
  - tradition labels (Hast Rekha terms vs Western terms);
  - later, when D-013 is lifted: currency, payment provider (Razorpay/UPI vs Stripe) and pricing.

  Engines are market-agnostic.

## D-011: Open source (Apache-2.0 code, CC BY 4.0 content); AGPL add-ons stay separate
**Status:** Accepted (owner, 2026-09-29)

- **Context:**
  - The project will spend a long time in R&D and validation, and the owner wants anyone to be able to contribute and check the work.
  - The owner does not want to rule out AGPL libraries before we know whether they help. Permissions can be sought later.
- **Decision:**
  - The core code is **Apache-2.0**.
  - `rules/`, `docs/` and `research/` are **CC BY 4.0** (`LICENSE-CONTENT`).
  - AGPL-dependent code lives only in `adapters-agpl/`:
    - it carries its own AGPL-3.0 licence;
    - it is an optional extra (`uv sync --extra agpl`);
    - it sits behind provider interfaces defined in core;
    - core never imports it, and CI checks this with an import-linter rule.
  - Examples: pyswisseph, PyJHora and kerykeion providers; Ultralytics experiments.
  - Contributions use a DCO sign-off, not a CLA.
  - **The repository is public from day one.** GitHub Actions is free for public repos, which matters because the owner's private-repo CI quota is used up. Consequences:
    - CI never needs secrets. All tests run on committed synthetic fixtures; no LLM keys and no datasets are used in CI.
    - A pre-commit hook plus a CI check block image, dataset and model files and `.env` files, so nothing git-ignored leaks.
    - Heavy evaluation runs (full datasets, training) happen on the owner's machine, not in CI.
- **Consequence:**
  - A deployment that enables `agpl` extras is an AGPL combined work. That is fine for R&D and an open demo.
  - For any future closed or paid deployment: disable the extras, or get a licence.
- **Revisit:** when comparison data shows whether an AGPL component is worth licensing.

## D-012: SQLite + local file storage for the POC and contributors
**Status:** Accepted (owner, 2026-09-29)

- **Context:** Supabase in Docker is heavy on RAM and disk, and open-source contributors should not need cloud accounts.
- **Decision:**
  - Drizzle ORM + better-sqlite3, one file `var/app.db`.
  - Plain-SQL migrations plus a full `db/schema.sql` snapshot for one-command setup (`pnpm db:reset`).
  - Portability conventions: ULID text IDs, ISO timestamps, JSON stored as TEXT.
  - Authorisation is enforced in a repository layer, with tests (there is no RLS).
  - Storage goes through a `StorageAdapter` backed by the local filesystem.
  - Auth: Better Auth (Phase 5).
- **Alternatives:**
  - Hosted Supabase free tier: needs an account; the free tier pauses when inactive.
  - Local Supabase: too heavy.
- **Revisit:** before any public multi-user deployment with real traffic. Then migrate to Postgres (Neon or hosted Supabase) and S3-compatible storage by swapping adapters.

## D-013: Payments and paywall deferred
**Status:** Accepted (owner, 2026-09-29)

- **Decision:**
  - No payment gateway, pricing, orders table or paywall UI until the owner explicitly asks.
  - All features are free in the open-source phase.
  - The architecture keeps a place for payments (market config, a future `orders` table), but nothing is built.

## D-014: R&D data policy for internal datasets
**Status:** Accepted (owner, 2026-09-29)

- **Context:**
  - Collecting consented photos takes time.
  - The owner authorises downloading publicly available datasets and models for **internal R&D**, whatever their licence, pending permissions for any production use.
- **Decision:**
  - All such data lives in `data/` and model files in `services/engine/models/weights/`. **Both are git-ignored and never redistributed.**
  - `data/manifest.yaml` records, for every item: source URL, licence, checksum, date downloaded, and the permission needed for production.
  - `scripts/fetch-data.sh` lets contributors fetch the same items themselves, under the source's own terms.
  - `docs/RESOURCES-REGISTRY.md` lists every dataset, model, repo and tool, with a column for the owner's decision.
  - Before any production use, each item must move to "cleared" in the registry.
  - Personal photos scraped from social media are **not** collected. Only published datasets are used.

## D-015: Rules may only use features that are reliable across repeat photos
**Status:** Accepted (evidence: docs/eval/features-v1.md, 2026-09-29)

- **Context:** test–retest on repeat photos of the same hand showed that pose variation between photos is comparable to the differences between people for hand-shape measures. Palm shape (0.57), index vs ring (0.62), finger length (0.68) and element (0.72) are not reproducible from one photo; nor is the fate line (0.68).
- **Decision:** every feature has a reliability tier (reliable / moderate / experimental), set from test–retest data.
  - Production rules may use **reliable** features, and **moderate** ones only when the zone is certain and the wording is soft.
  - **Experimental** features are used only in the research arm, labelled as such.
  - A CI lint on the rule base will enforce the tiers.
  - Tiers are re-measured whenever the pipeline changes.
- **Why:** a reading that changes when you retake the photo destroys trust, and would make the validation study measure noise.
- **Revisit:** after multi-photo capture (median of 2–3 photos per hand) and new retest data.

## D-016: The analysis engine has no outbound network access
**Status:** Accepted (2026-09-30)

- **Context:**
  - MediaPipe's native library contains Google usage-logging ("clearcut") code.
  - During dataset building it tried, and failed, to upload.
  - There is no documented opt-out, and we cannot verify what it would send.
- **Decision:**
  - In every deployment the engine runs on a network **without internet egress**. It only accepts requests from the web layer.
  - Docker Compose puts it on an `internal` network, and CI asserts that the engine container cannot reach the internet and is not published on the host.
  - Any hosted demo must apply an equivalent egress-deny rule.
- **Local development without Docker** is not isolated. Contributors who care should block the engine process in their firewall.
- **Revisit:** if MediaPipe documents an opt-out, or we move hand landmarks to our own ONNX model.
