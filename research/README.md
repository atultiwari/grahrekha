# Palmistry Portal: Research

Research done on 2026-09-29, before designing the architecture.

| # | Report | What it covers |
|---|---|---|
| 01 | [Competitor analysis](01-competitor-analysis.md) | How about 25 automated palm-reading products work (tarotbyvela, Nebula, Astroline, Palmist.io, GPTPalm, PANDIT AI…). Five technical levels, from fake to vision-LLM. Monetisation and dark patterns. Privacy law (DPDP, GDPR, BIPA). 17 lessons for our portal. |
| 02 | [Open-source resources](02-open-source-resources.md) | GitHub projects, datasets (Roboflow, Kaggle, academic), hand-landmark and segmentation tools, classical computer-vision recipe, public-domain palmistry books, astrology libraries, licensing cheat-sheet, recommended starter stack. |
| 03 | [Academic literature](03-academic-literature.md) | Palmistry automation papers, palm-line segmentation research, evidence-based palm features (2D:4D finger ratio, single palm crease), studies on whether palmistry is valid, the Barnum effect, datasets, how vision-language models handle hands. |

## Product decisions so far

- **Markets:** India and global storefronts from day one.
- **Palm and astrology are separate engines at first.** This lets us study palm-only vs astrology-only vs combined accuracy. The studies must include a shuffled/control reading to measure the Barnum effect (people rate vague readings as accurate).
- **Interpretation rules come from public-domain books** (Cheiro, Benham, Dale, Samudrika Shastra 1916). They will be reviewed later by the product owner.

## Five points that matter most for the architecture

1. **Hybrid pipeline:**
   - MediaPipe checks photo quality and straightens the palm.
   - A segmentation model traces the lines.
   - Code measures the geometry of each line.
   - A rule engine chooses the meanings.
   - The LLM only writes the prose.

   Never let a vision LLM "read" lines directly.
2. **We must build our own labelled dataset.** No licensed, commercially usable palm-line dataset exists. An editable line overlay, with the user's consent, doubles as a labelling tool.
3. **Every statement records its source:** palm, astrology or quiz, plus the rule that produced it. This is what makes the validation study possible.
4. **Privacy-first:** process on the device where possible, delete raw photos after a short period, get explicit consent. No health or lifespan claims.
5. **Watch licences:** avoid AGPL/GPL/non-commercial components, or buy commercial licences (Swiss Ephemeris). jyotishganit (MIT) is the permissive astrology option.
