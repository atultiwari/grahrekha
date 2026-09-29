# data/ (git-ignored R&D datasets)

This folder is **git-ignored** except for this README and `manifest.yaml`.
It holds third-party datasets used for **internal research only**. The policy is [D-014](../docs/DECISIONS.md), and each item's licence and status is tracked in [RESOURCES-REGISTRY.md](../docs/RESOURCES-REGISTRY.md).

## Fetch

```bash
scripts/fetch-data.sh --tier 1            # everything in Tier 1
scripts/fetch-data.sh --only D2,M1,M2     # specific items
```

Each download is recorded in `data/fetch-log.tsv` (size and SHA-256). A summary is kept in `manifest.yaml`.

By downloading, you accept each source's own terms. Many sources are **academic or non-commercial only**.

## Layout

```
data/raw/<ID>-<name>/          # untouched source data (IDs match the registry)
data/splits/*.txt              # frozen evaluation splits (paths relative to data/)
data/processed/                # derived crops/masks (reproducible from raw + scripts)
```

**Never commit images from here.** CI and pre-commit hooks block image and dataset files anywhere outside `**/fixtures/synthetic/`.
