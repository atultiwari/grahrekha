"""Train the per-line segmenter (Phase 2).

Usage (from ml/):
  uv run python -m grahrekha_ml.train_lines ../data --run v1 [--epochs 40] [--limit 16]

Model: U-Net, ResNet-34 encoder with ImageNet weights (torchvision, BSD licence; D-006:
no non-commercial encoder weights), 5 classes (bg, heart, head, life, fate), trained in
the canonical palm frame at 512 px. Best checkpoint by mean line Dice on the eval split.
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import segmentation_models_pytorch as smp
import torch
from torch.utils.data import DataLoader, Subset, WeightedRandomSampler

from grahrekha_ml.dataset import IGNORE_INDEX, LinesDataset, sample_weights
from grahrekha_ml.losses import LINE_CLASSES, LineLoss

CLASS_NAMES = {1: "heart", 2: "head", 3: "life", 4: "fate"}


def _plain(value: object) -> object:
    """Plain Python numbers only, so checkpoints load with torch.load(weights_only=True)."""
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    return value.item() if isinstance(value, np.generic) else value


def build_model(pretrained: bool = True) -> torch.nn.Module:
    model: torch.nn.Module = smp.Unet(
        encoder_name="resnet34", encoder_weights="imagenet" if pretrained else None, classes=5
    )
    return model


def device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


@torch.no_grad()
def evaluate(
    model: torch.nn.Module,
    loader: DataLoader[tuple[torch.Tensor, torch.Tensor]],
    dev: torch.device,
) -> dict[str, float]:
    model.eval()
    inter = np.zeros(5)
    total = np.zeros(5)
    for x, y in loader:
        pred = model(x.to(dev)).argmax(dim=1).cpu()
        valid = y != IGNORE_INDEX
        for cls in LINE_CLASSES:
            p, t = (pred == cls) & valid, (y == cls) & valid
            inter[cls] += float((p & t).sum())
            total[cls] += float(p.sum() + t.sum())
    dice = {
        CLASS_NAMES[c]: 2 * inter[c] / total[c] if total[c] else float("nan") for c in LINE_CLASSES
    }
    dice["mean"] = float(np.nanmean(list(dice.values())))
    return dice


def main() -> None:  # pragma: no cover - long-running training
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--run", default="v1")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument(
        "--limit", type=int, default=0, help="use only N training images (smoke test)"
    )
    parser.add_argument("--fate-boost", type=float, default=3.0, help="oversample fate palms")
    parser.add_argument("--fate-weight", type=float, default=3.0, help="fate class loss weight")
    args = parser.parse_args()

    torch.manual_seed(0)
    root = args.data / "processed/lines_v1"
    full_train = LinesDataset(root / "train", train=True, seed=0)
    weights = sample_weights(full_train, args.fate_boost)
    train_set: LinesDataset | Subset[tuple[torch.Tensor, torch.Tensor]] = full_train
    eval_set: LinesDataset | Subset[tuple[torch.Tensor, torch.Tensor]] = LinesDataset(
        root / "eval", train=False
    )
    if args.limit:
        train_set = Subset(full_train, range(args.limit))
        weights = weights[: args.limit]
        eval_set = Subset(eval_set, range(min(args.limit, len(eval_set))))
    sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)
    train_loader = DataLoader(
        train_set, batch_size=args.batch, sampler=sampler, num_workers=2, persistent_workers=True
    )
    eval_loader = DataLoader(eval_set, batch_size=args.batch, num_workers=2)

    dev = device()
    model = build_model().to(dev)
    loss_fn = LineLoss(class_weights=(0.2, 1.0, 1.0, 1.0, args.fate_weight)).to(dev)
    optimiser = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    schedule = torch.optim.lr_scheduler.OneCycleLR(
        optimiser, max_lr=args.lr, total_steps=args.epochs * len(train_loader), pct_start=0.1
    )
    run_dir = Path(__file__).resolve().parents[2] / "runs" / args.run
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(
        json.dumps(vars(args) | {"device": str(dev)}, default=str, indent=2)
    )
    best = -1.0
    for epoch in range(1, args.epochs + 1):
        model.train()
        start, losses = time.time(), []
        for x, y in train_loader:
            optimiser.zero_grad(set_to_none=True)
            loss = loss_fn(model(x.to(dev)), y.to(dev))
            loss.backward()
            optimiser.step()
            schedule.step()
            losses.append(float(loss.detach()))
        dice = evaluate(model, eval_loader, dev)
        record = {
            "epoch": epoch,
            "loss": float(np.mean(losses)),
            "seconds": round(time.time() - start),
            **dice,
        }
        with (run_dir / "metrics.jsonl").open("a") as log:
            log.write(json.dumps(record) + "\n")
        print(json.dumps(record), flush=True)
        if dice["mean"] > best:
            best = dice["mean"]
            torch.save(
                {"model": model.state_dict(), "epoch": epoch, "dice": _plain(dice)},
                run_dir / "best.pt",
            )


if __name__ == "__main__":  # pragma: no cover
    main()
