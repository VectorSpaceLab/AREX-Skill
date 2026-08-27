#!/usr/bin/env python3
"""Safely inspect face.evoLVe PyTorch components without running full training.

The script imports backbone/head/loss modules from a user-supplied face.evoLVe
repository root, constructs selected components, and optionally runs tiny CPU
forwards on synthetic tensors. It intentionally does not import or execute the
training entrypoint.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import pathlib
import sys
import types
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


STABLE_BACKBONES = {
    "ResNet_50": ("backbone.model_resnet", "ResNet_50"),
    "ResNet_101": ("backbone.model_resnet", "ResNet_101"),
    "ResNet_152": ("backbone.model_resnet", "ResNet_152"),
    "IR_50": ("backbone.model_irse", "IR_50"),
    "IR_101": ("backbone.model_irse", "IR_101"),
    "IR_152": ("backbone.model_irse", "IR_152"),
    "IR_SE_50": ("backbone.model_irse", "IR_SE_50"),
    "IR_SE_101": ("backbone.model_irse", "IR_SE_101"),
    "IR_SE_152": ("backbone.model_irse", "IR_SE_152"),
}

ADVANCED_BACKBONES = {
    "MobileFaceNet": ("backbone.MobileFaceNets", "MobileFaceNet"),
    "GhostNet": ("backbone.GhostNet", "GhostNet"),
    "ResidualAttentionNet": ("backbone.AttentionNets", "ResidualAttentionNet"),
    "EfficientNet": ("backbone.EfficientNets", "EfficientNet"),
}

STABLE_HEADS = ["Softmax", "ArcFace", "CosFace", "SphereFace", "Am_softmax"]
EXPERIMENTAL_HEADS = [
    "AdaCos",
    "AM_Softmax",
    "ArcNegFace",
    "CircleLoss",
    "CurricularFace",
    "MagFace",
    "MV_Softmax",
    "NPCFace",
    "SST_Prototype",
]


def parse_input_size(value: str) -> Tuple[int, int]:
    cleaned = value.replace("x", ",").replace("X", ",")
    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    if len(parts) == 1:
        h = w = int(parts[0])
    elif len(parts) == 2:
        h, w = int(parts[0]), int(parts[1])
    else:
        raise argparse.ArgumentTypeError("input size must be 112, 224, H,W, or HxW")
    if h <= 0 or w <= 0:
        raise argparse.ArgumentTypeError("input dimensions must be positive")
    return h, w


def spatial_for_input(input_size: Tuple[int, int]) -> Tuple[int, int]:
    h, w = input_size
    if h == 112 and w == 112:
        return 7, 7
    if h == 224 and w == 224:
        return 14, 14
    # Conservative fallback for source backbones that downsample by about 16.
    return max(1, h // 16), max(1, w // 16)


def signature_of(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - defensive for unusual callables
        return f"<signature unavailable: {type(exc).__name__}: {exc}>"


def module_file(repo_root: pathlib.Path, dotted: str) -> pathlib.Path:
    return repo_root.joinpath(*dotted.split(".")).with_suffix(".py")


def load_head_metrics_with_optional_patch(repo_root: pathlib.Path, torch_module: Any) -> Tuple[types.ModuleType, bool, Optional[str]]:
    """Import head.metrics, patching missing Module only for inspection if needed."""
    try:
        module = importlib.import_module("head.metrics")
        return module, False, None
    except Exception as first_exc:
        message = f"normal import failed: {type(first_exc).__name__}: {first_exc}"
        if "Module" not in str(first_exc):
            raise

    path = module_file(repo_root, "head.metrics")
    source = path.read_text(encoding="utf-8")
    module = types.ModuleType("head.metrics_inspection_patch")
    module.__file__ = str(path)
    module.__package__ = "head"
    module.__dict__["Module"] = torch_module.nn.Module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module, True, message


def construct_backbone(name: str, input_size: Tuple[int, int], embedding_size: int) -> Tuple[Any, Dict[str, Any]]:
    if name in STABLE_BACKBONES:
        module_name, attr = STABLE_BACKBONES[name]
        module = importlib.import_module(module_name)
        ctor = getattr(module, attr)
        return ctor([input_size[0], input_size[1]]), {
            "module": module_name,
            "class_or_function": attr,
            "signature": signature_of(ctor),
            "status": "stable",
        }

    if name == "MobileFaceNet":
        module = importlib.import_module("backbone.MobileFaceNets")
        ctor = getattr(module, "MobileFaceNet")
        out_h, out_w = spatial_for_input(input_size)
        return ctor(embedding_size, out_h, out_w), {
            "module": "backbone.MobileFaceNets",
            "class_or_function": "MobileFaceNet",
            "signature": signature_of(ctor),
            "status": "advanced-source",
            "out_h": out_h,
            "out_w": out_w,
        }

    if name == "GhostNet":
        module = importlib.import_module("backbone.GhostNet")
        ctor = getattr(module, "GhostNet")
        out_h, out_w = spatial_for_input(input_size)
        return ctor(feat_dim=embedding_size, out_h=out_h, out_w=out_w), {
            "module": "backbone.GhostNet",
            "class_or_function": "GhostNet",
            "signature": signature_of(ctor),
            "status": "advanced-source",
            "out_h": out_h,
            "out_w": out_w,
        }

    if name == "ResidualAttentionNet":
        module = importlib.import_module("backbone.AttentionNets")
        ctor = getattr(module, "ResidualAttentionNet")
        out_h, out_w = spatial_for_input(input_size)
        return ctor(1, 1, 1, embedding_size, out_h, out_w), {
            "module": "backbone.AttentionNets",
            "class_or_function": "ResidualAttentionNet",
            "signature": signature_of(ctor),
            "status": "advanced-source",
            "stage_modules": [1, 1, 1],
            "out_h": out_h,
            "out_w": out_w,
        }

    if name == "EfficientNet":
        # Let the import fail visibly if the source file still contains invalid text.
        module = importlib.import_module("backbone.EfficientNets")
        ctor = getattr(module, "EfficientNet")
        raise RuntimeError(
            "EfficientNet-like source imported, but this script does not guess blocks_args/global_params; "
            f"constructor signature is {signature_of(ctor)}"
        )

    known = sorted(list(STABLE_BACKBONES) + list(ADVANCED_BACKBONES))
    raise ValueError(f"unknown backbone {name!r}; known: {', '.join(known)}")


def inspect_losses() -> Dict[str, Any]:
    losses: Dict[str, Any] = {}
    try:
        focal_mod = importlib.import_module("loss.focal")
        focal_cls = getattr(focal_mod, "FocalLoss")
        losses["FocalLoss"] = {"signature": signature_of(focal_cls), "status": "stable"}
    except Exception as exc:
        losses["FocalLoss"] = {"error": f"{type(exc).__name__}: {exc}"}
    return losses


def inspect_heads(repo_root: pathlib.Path, torch: Any, embedding_size: int, num_classes: int, batch_size: int) -> Dict[str, Any]:
    result: Dict[str, Any] = {"stable": {}, "experimental": {}, "module_patch_used": False}
    metrics_mod, patched, import_note = load_head_metrics_with_optional_patch(repo_root, torch)
    result["module_patch_used"] = patched
    if import_note:
        result["normal_import_note"] = import_note

    features = torch.randn(batch_size, embedding_size)
    labels = torch.arange(batch_size, dtype=torch.long) % max(1, num_classes)

    for name in STABLE_HEADS:
        entry: Dict[str, Any] = {}
        try:
            cls = getattr(metrics_mod, name)
            entry["signature"] = signature_of(cls)
            head = cls(in_features=embedding_size, out_features=num_classes, device_id=None)
            head.eval()
            with torch.no_grad():
                if name == "Softmax":
                    logits = head(features)
                else:
                    logits = head(features, labels)
            entry["forward_shape"] = list(logits.shape)
            entry["status"] = "stable"
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
        result["stable"][name] = entry

    for name in EXPERIMENTAL_HEADS:
        entry = {}
        try:
            cls = getattr(metrics_mod, name)
            entry["signature"] = signature_of(cls)
            entry["status"] = "experimental-source; signature only"
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
        result["experimental"][name] = entry

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect face.evoLVe PyTorch backbone/head/loss components without running full training."
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to a face.evoLVe checkout whose PyTorch source modules should be inspected.",
    )
    parser.add_argument(
        "--backbone",
        default="IR_50",
        help="Backbone to construct. Stable: ResNet_50/101/152, IR_50/101/152, IR_SE_50/101/152. Advanced: MobileFaceNet, GhostNet, ResidualAttentionNet, EfficientNet.",
    )
    parser.add_argument(
        "--input-size",
        type=parse_input_size,
        default=(112, 112),
        help="Input size as 112, 224, H,W, or HxW. Default: 112.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2,
        help="Synthetic batch size for the CPU forward check. Use at least 2 to avoid BatchNorm training-mode issues. Default: 2.",
    )
    parser.add_argument(
        "--embedding-size",
        type=int,
        default=512,
        help="Expected embedding size for heads and advanced backbone constructors. Default: 512.",
    )
    parser.add_argument(
        "--num-classes",
        type=int,
        default=5,
        help="Synthetic class count for stable head logits. Default: 5.",
    )
    parser.add_argument(
        "--inspect-heads",
        action="store_true",
        help="Inspect head.metrics signatures and run stable heads on synthetic CPU tensors with device_id=None.",
    )
    parser.add_argument(
        "--skip-forward",
        action="store_true",
        help="Only import/construct the selected backbone; do not run a synthetic forward pass.",
    )
    parser.add_argument(
        "--list-components",
        action="store_true",
        help="Print known stable and advanced component names and exit after repo-root validation.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root).expanduser().resolve()
    report: Dict[str, Any] = {
        "repo_root_supplied": str(repo_root),
        "note": "This script avoids importing or executing the full training entrypoint.",
        "input_size": list(args.input_size),
        "batch_size": args.batch_size,
        "embedding_size": args.embedding_size,
        "num_classes": args.num_classes,
    }

    if not repo_root.exists():
        report["error"] = f"repo root does not exist: {repo_root}"
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2
    if not (repo_root / "backbone").is_dir():
        report["error"] = "repo root does not look like face.evoLVe PyTorch source: missing backbone/"
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    sys.path.insert(0, str(repo_root))

    if args.list_components:
        report["components"] = {
            "stable_backbones": sorted(STABLE_BACKBONES),
            "advanced_backbones": sorted(ADVANCED_BACKBONES),
            "stable_heads": STABLE_HEADS,
            "experimental_heads": EXPERIMENTAL_HEADS,
            "stable_losses": ["FocalLoss", "torch.nn.CrossEntropyLoss"],
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if args.batch_size <= 0:
        report["error"] = "--batch-size must be positive"
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2
    if args.num_classes <= 0:
        report["error"] = "--num-classes must be positive"
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    try:
        import torch
    except Exception as exc:
        report["error"] = f"failed to import torch: {type(exc).__name__}: {exc}"
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    report["torch"] = {"version": getattr(torch, "__version__", "unknown"), "cuda_available": bool(torch.cuda.is_available())}

    try:
        backbone, info = construct_backbone(args.backbone, args.input_size, args.embedding_size)
        report["backbone"] = info
        report["backbone"]["selected"] = args.backbone
        report["backbone"]["parameter_count"] = int(sum(p.numel() for p in backbone.parameters()))
        backbone.eval()
        if not args.skip_forward:
            x = torch.randn(args.batch_size, 3, args.input_size[0], args.input_size[1])
            with torch.no_grad():
                y = backbone(x)
            report["backbone"]["forward_shape"] = list(y.shape)
            report["backbone"]["expected_embedding_size"] = args.embedding_size
            report["backbone"]["embedding_size_matches"] = bool(len(y.shape) == 2 and y.shape[1] == args.embedding_size)
    except Exception as exc:
        report["backbone"] = {"selected": args.backbone, "error": f"{type(exc).__name__}: {exc}"}
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    report["losses"] = inspect_losses()

    if args.inspect_heads:
        try:
            report["heads"] = inspect_heads(repo_root, torch, args.embedding_size, args.num_classes, args.batch_size)
        except Exception as exc:
            report["heads"] = {"error": f"{type(exc).__name__}: {exc}"}
            print(json.dumps(report, indent=2, sort_keys=True))
            return 1

    if args.batch_size == 1:
        report.setdefault("warnings", []).append(
            "Batch size 1 is acceptable for eval-mode inspection but unsafe for training-mode BatchNorm checks."
        )

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
