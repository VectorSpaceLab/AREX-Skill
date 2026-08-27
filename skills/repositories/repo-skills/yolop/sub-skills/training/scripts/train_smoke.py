#!/usr/bin/env python3
"""Run a tiny YOLOP model/training-path smoke without loading BDD100K.

Default behavior checks imports, model construction, and a dummy forward in
train mode. Use --check-loss to also exercise MultiHeadLoss on synthetic
labels; this may expose torch-version compatibility issues in build_targets.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _shape(value: Any) -> Any:
    if hasattr(value, "shape"):
        return list(value.shape)
    if isinstance(value, (list, tuple)):
        return [_shape(v) for v in value]
    return type(value).__name__


def main() -> int:
    parser = argparse.ArgumentParser(description="YOLOP tiny training smoke")
    parser.add_argument("--repo-root", required=True, help="Path to a YOLOP checkout")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, cuda:0, ...")
    parser.add_argument("--image-size", type=int, default=128, help="Dummy square size, multiple of 32")
    parser.add_argument("--batch-size", type=int, default=1, help="Tiny synthetic batch size")
    parser.add_argument("--check-loss", action="store_true", help="Also call get_loss on synthetic targets")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not (repo_root / "lib" / "core" / "loss.py").is_file():
        print(f"ERROR: not a YOLOP checkout: {repo_root}", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo_root))

    import torch
    from lib.config import cfg
    from lib.core.loss import get_loss
    from lib.models import get_net

    if args.image_size <= 0 or args.image_size % 32 != 0:
        print("ERROR: --image-size must be a positive multiple of 32", file=sys.stderr)
        return 3
    if args.batch_size <= 0:
        print("ERROR: --batch-size must be positive", file=sys.stderr)
        return 4
    if args.device != "cpu" and args.device.startswith("cuda") and not torch.cuda.is_available():
        print("ERROR: CUDA requested but torch.cuda.is_available() is false", file=sys.stderr)
        return 5

    device = torch.device(args.device)
    torch.set_num_threads(1)
    model = get_net(cfg).to(device)
    model.train()
    dummy = torch.zeros(args.batch_size, 3, args.image_size, args.image_size, device=device)
    outputs = model(dummy)
    summary: dict[str, Any] = {
        "torch": torch.__version__,
        "device": str(device),
        "batch_size": args.batch_size,
        "image_size": args.image_size,
        "forward_output_shape": _shape(outputs),
        "loss_checked": False,
    }

    if args.check_loss:
        criterion = get_loss(cfg, device=device)
        # One synthetic detection target: image index, class id, normalized cx/cy/w/h.
        det_target = torch.tensor([[0.0, 0.0, 0.5, 0.5, 0.1, 0.1]], device=device)
        da_target = torch.zeros(args.batch_size, 2, args.image_size, args.image_size, device=device)
        ll_target = torch.zeros(args.batch_size, 2, args.image_size, args.image_size, device=device)
        shapes = [((args.image_size, args.image_size), ((1.0, 1.0), (0.0, 0.0))) for _ in range(args.batch_size)]
        try:
            loss, heads = criterion(outputs, [det_target, da_target, ll_target], shapes, model)
            summary["loss_checked"] = True
            summary["loss"] = float(loss.detach().cpu())
            summary["head_losses"] = [float(x) for x in heads]
        except Exception as exc:  # pragma: no cover - diagnostic path
            summary["loss_checked"] = True
            summary["loss_error"] = str(exc)
            print("ERROR: loss smoke failed. See training troubleshooting for torch-version build_targets notes.", file=sys.stderr)
            print(str(exc), file=sys.stderr)
            if args.json:
                print(json.dumps(summary, indent=2, sort_keys=True))
            return 6

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("YOLOP training-path smoke passed")
        for key, value in summary.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
