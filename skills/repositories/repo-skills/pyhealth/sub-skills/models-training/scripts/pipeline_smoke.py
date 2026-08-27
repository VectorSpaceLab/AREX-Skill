#!/usr/bin/env python3
"""Run a tiny model contract smoke without datasets, downloads, or checkpoints."""
import argparse
import torch
from torch import nn


class TinyClassifier(nn.Module):
    mode = "binary"
    def __init__(self):
        super().__init__()
        self.layer = nn.Linear(3, 1)
    def forward(self, x, label):
        logits = self.layer(x).squeeze(-1)
        loss = nn.functional.binary_cross_entropy_with_logits(logits, label.float())
        return {"loss": loss, "y_true": label, "y_prob": logits.sigmoid()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
    args = parser.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")
    device = torch.device(args.device)
    try:
        model = TinyClassifier().to(device)
        batch = {"x": torch.ones(4, 3, device=device), "label": torch.tensor([0, 1, 0, 1], device=device)}
        output = model(**batch)
        if "loss" not in output or output["y_prob"].shape != (4,):
            raise SystemExit("model contract failed")
        output["loss"].backward()
    except RuntimeError as exc:
        if args.device == "cuda" and ("out of memory" in str(exc).lower() or "cuda" in str(exc).lower()):
            print(f"CUDA smoke blocked: {exc}")
            return 2
        raise
    print({"device": str(device), "loss": float(output["loss"].detach()), "prob_shape": list(output["y_prob"].shape)})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
