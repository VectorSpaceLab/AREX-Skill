#!/usr/bin/env python3
"""Check a pytorch-cifar100 checkout without downloading data or running training.

Example:
  python check_environment.py --repo-root /path/to/pytorch-cifar100 --net resnet18

The script adds --repo-root to sys.path, imports the repo helpers, reports core
package versions and CUDA availability, and runs one random 32x32 forward pass.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from types import SimpleNamespace
from typing import Any, Dict

SUPPORTED_NETS = {
    "vgg16", "vgg13", "vgg11", "vgg19",
    "densenet121", "densenet161", "densenet169", "densenet201",
    "googlenet", "inceptionv3", "inceptionv4", "inceptionresnetv2", "xception",
    "resnet18", "resnet34", "resnet50", "resnet101", "resnet152",
    "preactresnet18", "preactresnet34", "preactresnet50", "preactresnet101", "preactresnet152",
    "resnext50", "resnext101", "resnext152",
    "shufflenet", "shufflenetv2", "squeezenet", "mobilenet", "mobilenetv2", "nasnet",
    "attention56", "attention92",
    "seresnet18", "seresnet34", "seresnet50", "seresnet101", "seresnet152",
    "wideresnet", "stochasticdepth18", "stochasticdepth34", "stochasticdepth50", "stochasticdepth101",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Non-destructive import/backend/model check for pytorch-cifar100.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", required=True, help="path to a pytorch-cifar100 checkout")
    parser.add_argument("--net", default="resnet18", help="supported network key to instantiate")
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="cpu", help="device for the random forward pass")
    parser.add_argument("--batch-size", type=int, default=1, help="random input batch size")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a text report")
    return parser


def fail(message: str, json_mode: bool) -> int:
    if json_mode:
        print(json.dumps({"ok": False, "error": message}, indent=2))
    else:
        print(f"FAIL: {message}", file=sys.stderr)
    return 1


def module_version(module: Any) -> str:
    return str(getattr(module, "__version__", "unknown"))


def main() -> int:
    args = build_parser().parse_args()
    if args.net not in SUPPORTED_NETS:
        return fail(f"unsupported net '{args.net}'. Use a key from the model-zoo catalog.", args.json)
    if args.batch_size <= 0:
        return fail("--batch-size must be greater than zero", args.json)

    repo_root = os.path.abspath(args.repo_root)
    if not os.path.isdir(repo_root):
        return fail(f"repo root does not exist: {repo_root}", args.json)
    for required in ["utils.py", "train.py", "test.py", "models"]:
        if not os.path.exists(os.path.join(repo_root, required)):
            return fail(f"repo root is missing expected pytorch-cifar100 artifact: {required}", args.json)

    sys.path.insert(0, repo_root)
    try:
        import numpy  # type: ignore
        import torch  # type: ignore
        import torchvision  # type: ignore
        from conf import settings  # type: ignore
        import utils  # type: ignore
    except BaseException as exc:
        return fail(f"import check failed: {type(exc).__name__}: {exc}", args.json)

    cuda_available = bool(torch.cuda.is_available())
    device = "cuda" if args.device == "auto" and cuda_available else args.device
    if device == "cuda" and not cuda_available:
        return fail("CUDA requested but torch.cuda.is_available() is false", args.json)

    try:
        model = utils.get_network(SimpleNamespace(net=args.net, gpu=(device == "cuda")))
        model.eval()
        x = torch.randn(args.batch_size, 3, 32, 32)
        if device == "cuda":
            x = x.cuda()
        with torch.no_grad():
            y = model(x)
        output_shape = list(y.shape)
        shape_ok = output_shape == [args.batch_size, 100]
    except BaseException as exc:
        return fail(f"model smoke failed for {args.net}: {type(exc).__name__}: {exc}", args.json)

    payload: Dict[str, Any] = {
        "ok": bool(shape_ok),
        "net": args.net,
        "device": device,
        "batch_size": args.batch_size,
        "output_shape": output_shape,
        "expected_output_shape": [args.batch_size, 100],
        "parameter_count": int(sum(p.numel() for p in model.parameters())),
        "versions": {
            "torch": module_version(torch),
            "torchvision": module_version(torchvision),
            "numpy": module_version(numpy),
        },
        "cuda_available": cuda_available,
        "settings": {
            "epochs": int(settings.EPOCH),
            "milestones": list(settings.MILESTONES),
            "checkpoint_path": str(settings.CHECKPOINT_PATH),
            "log_dir": str(settings.LOG_DIR),
        },
        "side_effects": "No CIFAR-100 download, no training, no checkpoint writes.",
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"OK: {payload['ok']}")
        print(f"net: {payload['net']}")
        print(f"device: {payload['device']} (cuda_available={payload['cuda_available']})")
        print(f"output_shape: {tuple(payload['output_shape'])}")
        print(f"parameter_count: {payload['parameter_count']}")
        print("versions: " + ", ".join(f"{k}={v}" for k, v in payload["versions"].items()))
        print(f"settings: epochs={settings.EPOCH}, milestones={settings.MILESTONES}, checkpoint={settings.CHECKPOINT_PATH}, logs={settings.LOG_DIR}")
        print(payload["side_effects"])
    return 0 if shape_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
