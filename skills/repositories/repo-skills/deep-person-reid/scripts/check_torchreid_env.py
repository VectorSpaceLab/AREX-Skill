#!/usr/bin/env python3
"""Safe Torchreid environment check for generated deep-person-reid skill users.

This helper imports Torchreid, reports core package/backend facts, builds a
small model with pretrained=False, and optionally probes CUDA. It does not
start training, download datasets, or fetch pretrained weights.
"""

from __future__ import annotations

import argparse
import json
from importlib import metadata
from typing import Any

MODEL_KEYS = {
    "resnet18", "resnet34", "resnet50", "resnet101", "resnet152",
    "resnext50_32x4d", "resnext101_32x8d", "resnet50_fc512", "resnet50mid",
    "resnet50_ibn_a", "resnet50_ibn_b", "se_resnet50", "se_resnet50_fc512",
    "se_resnet101", "se_resnext50_32x4d", "se_resnext101_32x4d",
    "densenet121", "densenet169", "densenet201", "densenet161",
    "densenet121_fc512", "inceptionresnetv2", "inceptionv4", "xception",
    "nasnsetmobile", "mobilenetv2_x1_0", "mobilenetv2_x1_4", "shufflenet",
    "shufflenet_v2_x0_5", "shufflenet_v2_x1_0", "shufflenet_v2_x1_5",
    "shufflenet_v2_x2_0", "squeezenet1_0", "squeezenet1_0_fc512",
    "squeezenet1_1", "mudeep", "hacnn", "pcb_p6", "pcb_p4", "mlfn",
    "osnet_x1_0", "osnet_x0_75", "osnet_x0_5", "osnet_x0_25",
    "osnet_ibn_x1_0", "osnet_ain_x1_0", "osnet_ain_x0_75",
    "osnet_ain_x0_5", "osnet_ain_x0_25",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a non-training Torchreid import/backend/model smoke check.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--model-name",
        default="osnet_x0_25",
        help="Torchreid model key to build with pretrained=False.",
    )
    parser.add_argument(
        "--num-classes",
        type=int,
        default=2,
        help="Classifier output count for the model-build smoke.",
    )
    parser.add_argument(
        "--probe-cuda",
        action="store_true",
        help="Also check torch.cuda availability and a tiny CUDA allocation when available.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON only.",
    )
    return parser.parse_args()


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    args = parse_args()
    if args.model_name not in MODEL_KEYS:
        close = sorted(k for k in MODEL_KEYS if args.model_name.lower() in k)[:8]
        raise SystemExit(
            f"Unknown model key: {args.model_name!r}. "
            f"Try one of: {', '.join(close) if close else ', '.join(sorted(MODEL_KEYS)[:8])}"
        )
    if args.num_classes <= 0:
        raise SystemExit("--num-classes must be positive")

    import torch
    import torchvision
    import torchreid
    from torchreid.models import build_model

    summary: dict[str, Any] = {
        "torchreid_version": getattr(torchreid, "__version__", dist_version("torchreid")),
        "torch_distribution_version": dist_version("torch"),
        "torchvision_distribution_version": dist_version("torchvision"),
        "torch_import_version": torch.__version__,
        "torchvision_import_version": torchvision.__version__,
        "torch_cuda_version": torch.version.cuda,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        "model_name": args.model_name,
    }

    model = build_model(
        name=args.model_name,
        num_classes=args.num_classes,
        pretrained=False,
        use_gpu=False,
    )
    summary["model_class"] = type(model).__name__
    summary["model_parameter_count"] = int(sum(p.numel() for p in model.parameters()))

    x = torch.ones(2, 3)
    summary["cpu_tensor_sum"] = float(x.sum())

    if args.probe_cuda:
        if torch.cuda.is_available():
            cuda_tensor = torch.empty((1,), device="cuda")
            summary["cuda_probe"] = {
                "status": "passed",
                "device_name": torch.cuda.get_device_name(0),
                "device_capability": list(torch.cuda.get_device_capability(0)),
                "tiny_allocation_shape": list(cuda_tensor.shape),
            }
        else:
            summary["cuda_probe"] = {
                "status": "unavailable",
                "note": "torch.cuda.is_available() is false in this environment",
            }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("Torchreid environment check")
        print("- torchreid:", summary["torchreid_version"])
        print("- torch:", summary["torch_import_version"])
        print("- torchvision:", summary["torchvision_import_version"])
        print("- CUDA available:", summary["cuda_available"])
        print("- model:", summary["model_name"], summary["model_class"])
        print("- parameters:", summary["model_parameter_count"])
        print("- CPU tensor sum:", summary["cpu_tensor_sum"])
        if "cuda_probe" in summary:
            print("- CUDA probe:", summary["cuda_probe"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
