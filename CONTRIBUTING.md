# Contributing to GrahRekha

Thank you for helping. This project is research-first: **honesty, reproducibility and privacy come before features.**

## Ground rules

1. **No real palm photos, faces, or dataset files in the repo. Ever.**
   - Only synthetic test images, under `**/fixtures/synthetic/`, are allowed.
   - A pre-commit hook and CI block image, model and dataset files everywhere else.
2. **No health, lifespan, disease or fertility claims** in rules, templates or prompts (see [D-009](docs/DECISIONS.md)). A CI lint enforces this.
3. **Every interpretation rule cites its source** (work plus page or chapter). Rules come from public-domain texts only.
4. **Core code must not import `adapters-agpl/`** ([D-011](docs/DECISIONS.md)).
5. **Tests first.** New engine functions come with tests, and coverage for engine and API code should stay at 80% or above.

## Developer Certificate of Origin (DCO)

Sign off every commit to certify that you wrote the change, or have the right to submit it under the project's licences ([developercertificate.org](https://developercertificate.org/)):

```bash
git commit -s -m "feat: add heart line curvature feature"
```

## Workflow

1. Open or claim an issue.
2. Branch from `main`: `feat/…`, `fix/…`, `docs/…`.
3. Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `perf:`, `ci:`.
4. Run the checks locally:

   ```bash
   pnpm lint && pnpm typecheck && pnpm test
   (cd services/engine && uv run ruff check . && uv run mypy && uv run pytest)
   ```
5. Open a PR using the template. CI must be green.

## Setting up hooks

```bash
git config core.hooksPath .githooks
```

## Working with data

Datasets and weights are fetched with `scripts/fetch-data.sh` into git-ignored folders. By downloading them you accept each source's own terms (many are academic-only). See [docs/RESOURCES-REGISTRY.md](docs/RESOURCES-REGISTRY.md).

## Adding a rule

See [docs/ARCHITECTURE.md §6](docs/ARCHITECTURE.md). In short:
1. Add a YAML entry under `rules/`, with `source` filled in and `review.status: extracted`.
2. Run the rule lint.
3. A maintainer reviews it before it becomes `approved`.
