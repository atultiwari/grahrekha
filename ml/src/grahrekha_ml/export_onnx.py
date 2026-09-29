"""Export a trained line segmenter to ONNX for the engine, and verify it numerically.

Usage (from ml/):  uv run python -m grahrekha_ml.export_onnx --run v1

Writes services/engine/models/weights/M9-grahrekha-lines-<run>/{model.onnx,model_meta.json}
(git-ignored). The model card lives in services/engine/models/cards/.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch

from grahrekha_ml.train_lines import build_model, load_checkpoint

ROOT = Path(__file__).resolve().parents[3]
INPUT = 512


def export(run: str) -> Path:
    checkpoint = load_checkpoint(ROOT / "ml/runs" / run / "best.pt")
    model = build_model(pretrained=False)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    out_dir = ROOT / f"services/engine/models/weights/M9-grahrekha-lines-{run}"
    out_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = out_dir / "model.onnx"
    dummy = torch.randn(1, 3, INPUT, INPUT)
    torch.onnx.export(
        model,
        (dummy,),
        str(onnx_path),
        input_names=["input"],
        output_names=["logits"],
        opset_version=17,
        dynamo=False,
    )

    # Numerical check: ONNX Runtime must reproduce PyTorch.
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    sample = torch.randn(1, 3, INPUT, INPUT)
    with torch.no_grad():
        expected = model(sample).numpy()
    (actual,) = session.run(["logits"], {"input": sample.numpy()})
    max_diff = float(np.abs(actual - expected).max())
    if max_diff > 1e-3:
        raise RuntimeError(f"ONNX output differs from PyTorch by {max_diff}")

    meta = {
        "name": f"grahrekha-lines-{run}",
        "architecture": "segmentation_models_pytorch Unet, encoder resnet34 (ImageNet init)",
        "frame": "canonical palm frame (rectify.py), 512x512 RGB, left-palm layout",
        "input": {
            "name": "input",
            "shape": [1, 3, INPUT, INPUT],
            "normalize": "ImageNet mean/std after /255",
        },
        "output": {"name": "logits", "shape": [1, 5, INPUT, INPUT], "note": "softmax over axis 1"},
        "classes": ["background", "heart", "head", "life", "fate"],
        "trained_epoch": checkpoint["epoch"],
        "eval_dice": checkpoint["dice"],
        "onnx_max_abs_diff_vs_torch": max_diff,
        "sha256": hashlib.sha256(onnx_path.read_bytes()).hexdigest(),
        "licence_status": "RESEARCH ONLY: PLSU training masks have no stated licence (model card)",
    }
    (out_dir / "model_meta.json").write_text(json.dumps(meta, indent=2))
    return onnx_path


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="v1")
    print(export(parser.parse_args().run))
