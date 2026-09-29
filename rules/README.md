# GrahRekha rule base

This folder holds the interpretation rules that turn **measured palm features** into statements. Each statement cites a public-domain source.

Licence: **CC BY 4.0** (see `LICENSE-CONTENT`). The quoted source texts themselves are public domain.

## Rules of the rule base

1. **Every rule cites its source.** It gives the work, a locator (chapter or page), and a short **verbatim quote**. CI checks each quote word for word against the source text, which is fetched with `scripts/fetch-data.sh --only B1`.
2. **No health, lifespan, disease, fertility or accident claims** ([D-009](../docs/DECISIONS.md)). The CI lint rejects banned terms.

   For this reason there are **no life-line rules**: Cheiro's life-line chapter is about health, constitution and length of life.
3. **Only features we can measure reliably** ([D-015](../docs/DECISIONS.md)). `feature-tiers.yaml` lists every feature as reliable, moderate or experimental, based on test–retest measurements ([docs/eval/features-v1.md](../docs/eval/features-v1.md)).
   - Approved rules cannot use experimental features.
   - A rule that uses a zone must also require the zone to be *certain*.
4. **Known measurement problems block approval.** `validity_blocker` records an artefact that makes a rule misleading. For example, the v0 segmenter truncates heart lines, which biases the heart-line end zone. A rule with a blocker cannot be approved.
5. **Review workflow:** `extracted` → `reviewed` → `approved` (or `rejected`).
   - Only **approved** rules appear in production readings.
   - Unreviewed rules are visible only in the private `/lab` pages.
   - Approval needs a named `reviewer`.

## Format

```yaml
- id: palm.head.straight_across        # unique, dotted, lower-case
  tradition: western                    # western | vedic | chinese
  engine: palm                          # palm | astro (never both, D-001)
  domain: mind_learning                 # fixed taxonomy (docs/ARCHITECTURE.md §6.2)
  when:                                 # JSONLogic subset over palm_features.v1
    and:
      - "==": [{var: lines.head.present}, true]
      - ">": [{var: lines.head.slope_deg}, -34.8]
  statement: {en: "..."}                # our paraphrase, modern and non-judgemental
  polarity: positive                    # positive | neutral | caution
  strength: 1                           # 1-3; resolves `excludes` conflicts
  excludes: [palm.head.steep_to_moon]
  source:
    work: "Cheiro, Palmistry for All (1916)"
    locator: "Chapter II, ..."
    edition: "Project Gutenberg #20480"
    quote: "verbatim extract"
  mapping_note: "how the author's terms map onto our measured features"
  validity_blocker: null
  review: {status: extracted, reviewer: null, notes: ""}
```

**Thresholds** such as "short" or "steep" are set from percentiles of measured palms. Each file's header records them.

**Supported operators:** `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `and`, `or`, `!`, `var`. Comparisons with a missing feature are false, so absent lines never trigger a rule.

## Current contents

| File | Rules | Status |
|---|---|---|
| `palm/western/cheiro-heart.yaml` | 5 | extracted. Heart end-zone rules are valid only with the v1 segmenter (88% agreement with human annotation; v0: 72%). |
| `palm/western/cheiro-head.yaml` | 5 | extracted. Two use an experimental feature (research arm only). |
| `astro/vedic/brihat-jataka-houses.yaml` | 18 | extracted. Planets in houses, Brihat Jataka ch. XX (tr. Chidambaram Iyer, 1885). |
| `astro/vedic/jataka-chandrika-dasha.yaml` | 4 | extracted. Current mahadasha judged by its lord's house rulership (Jataka Chandrika, tr. Rao, 1900). |

**Astro rules** are evaluated on `astro_features.v1` (`services/engine/src/grahrekha_engine/astro/features.py`):
- `planets.<Planet>.house`, `.sign`, `.navamsa_sign` and `.retrograde`;
- `lagna_sign`;
- `mahadasha` / `antardasha`, each with `lord` and `houses_ruled`;
- `time_confidence` and `moon_nakshatra_uncertain`.

The lint applies the astro version of "zones must be certain":
- Rules that use houses, the lagna or lordship must require `time_confidence == exact` **and** `lagna_margin_deg >= 2`. The lagna moves about 1° every 4 minutes, so near a sign boundary a slightly wrong time changes every house.
- Rules that use the dasha must require `moon_nakshatra_uncertain == false`.

The two Jyotish sources are OCR scans, so their quotes are checked at ≥ 90% similarity rather than verbatim. Why these sources were chosen: [research/04-jyotish-sources.md](../research/04-jyotish-sources.md).

**Next:**
- Benham, *The Laws of Scientific Hand Reading* (1900).
- Dale, *Indian Palmistry*.
- Samudrika Shastra (1916).
- Owner review of all rules.
