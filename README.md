# GrahRekha (ग्रह-रेखा)

> *Planets in your palm, lines in your stars.*

GrahRekha is an **open-source, evidence-minded research project for AI-assisted palmistry (Hast Rekha) and Vedic astrology (Jyotish)**.

It reads a photo of your palm with computer vision:
- it checks the photo is a real, usable palm;
- it finds the major lines;
- it measures them.

It then applies interpretation rules taken from public-domain palmistry texts, each rule citing its source. A separate engine computes your birth chart and Vimshottari dasha.

The two engines are kept **deliberately separate**. That way we can test honestly whether palm-only, astrology-only, or combined readings carry any signal beyond a blinded control reading.

> **For entertainment and self-reflection.** Palmistry and astrology have no established scientific validity. GrahRekha never makes health, lifespan, disease or fertility statements. See [research/03-academic-literature.md](research/03-academic-literature.md).

## Status

**Phase 0 (foundations) is complete.** Next is Phase 1, the palm engine prototype. See the [implementation plan](docs/IMPLEMENTATION-PLAN.md).

## How it works

```
photo → quality gate (MediaPipe) → rectify palm → segment lines (ONNX) → measure features
      → rule engine (YAML rules with book citations) → narration (template or optional LLM)

birth data → astrology engine (jyotishganit) → chart + dasha → rule engine → narration
```

Each sentence in a reading records **which engine and which rule** produced it.

More detail:
- [Architecture](docs/ARCHITECTURE.md)
- [Decisions](docs/DECISIONS.md)
- [Research](research/README.md)

## Repository layout

| Path | What |
|---|---|
| `apps/web` | Next.js web app and API layer |
| `apps/mobile` | Expo (React Native) app |
| `services/engine` | Python FastAPI engine: palm, astro, rules |
| `packages/*` | Shared TypeScript: contracts, ui, i18n, reading composer |
| `db/` | SQLite schema and migrations (Drizzle) |
| `rules/` | Interpretation rule base (YAML, CC BY 4.0) |
| `adapters-agpl/` | Optional AGPL providers, kept separate (see D-011) |
| `data/` | R&D datasets. **Git-ignored**; see [data/README.md](data/README.md) |
| `docs/`, `research/` | Architecture, plans, research reports |

## Quick start

Requirements:
- Node 22 and pnpm 9
- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- Optionally, Docker

```bash
pnpm install                          # also enables the pre-commit guard (.githooks)
pnpm db:reset                         # creates var/app.db (SQLite)
cp .env.example apps/web/.env.local   # web settings, including the engine secret
```

Run the engine and web app in two terminals:

```bash
# terminal 1: engine on :8000
cd services/engine && uv sync
ENGINE_SHARED_SECRET=local-dev-secret uv run uvicorn grahrekha_engine.server:app --reload --port 8000

# terminal 2: web on :3000
pnpm dev
```

Check that everything works: http://localhost:3000/api/health should return `{"web":"ok","engine":{"status":"ok",...}}`.

Or run everything with Docker (it binds to localhost only):

```bash
docker compose up --build
```

**No cloud accounts are needed.** An LLM is optional; readings fall back to templates.

**R&D datasets and model weights:**

```bash
scripts/fetch-data.sh --tier 1   # ~4.4 GB, verified against data/checksums.sha256
```

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md). The important rules:
- **Never commit real palm photos or datasets.**
- Sign off your commits with the DCO (`git commit -s`).

## Licence

| Part | Licence |
|---|---|
| Code | [Apache-2.0](LICENSE) |
| `rules/`, `docs/`, `research/` | [CC BY 4.0](LICENSE-CONTENT) |
| `adapters-agpl/` | AGPL-3.0 |

See [NOTICE](NOTICE).
