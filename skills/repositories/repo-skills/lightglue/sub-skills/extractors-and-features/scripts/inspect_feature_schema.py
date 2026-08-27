#!/usr/bin/env python3
"""Inspect LightGlue extractor feature dictionaries for one image.

The default extractor is OpenCV SIFT, which avoids pretrained model downloads.
Selecting superpoint, disk, aliked, or doghardnet can download pretrained weights
through torch/Kornia on first use if the cache is empty.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


EXTRACTOR_CHOICES = ("sift", "superpoint", "disk", "aliked", "doghardnet")
ALIKED_MODELS = ("aliked-t16", "aliked-n16", "aliked-n16rot", "aliked-n32")
SIFT_BACKENDS = ("opencv", "pycolmap", "pycolmap_cpu", "pycolmap_cuda")


class UserError(Exception):
    """Expected command-line or environment error."""


def parse_resize(value: str) -> Optional[int]:
    text = str(value).strip().lower()
    if text in {"none", "no", "off", "false"}:
        return None
    try:
        parsed = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "resize must be a positive integer or 'none'"
        ) from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("resize must be positive, or use 'none'")
    return parsed


def parse_max_keypoints(value: str) -> Tuple[str, Optional[int]]:
    text = str(value).strip().lower()
    if text == "default":
        return "default", None
    if text == "none":
        return "value", None
    try:
        parsed = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "max-keypoints must be an integer, 'none', or 'default'"
        ) from exc
    return "value", parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print keys, shapes, dtypes, and validation notes for a LightGlue "
            "extractor feature dictionary. Defaults to SIFT to avoid pretrained "
            "downloads."
        )
    )
    parser.add_argument(
        "--image",
        required=True,
        type=Path,
        help="Path to an input image readable by OpenCV.",
    )
    parser.add_argument(
        "--extractor",
        default="sift",
        choices=EXTRACTOR_CHOICES,
        help=(
            "Extractor to instantiate. Non-SIFT choices may download pretrained "
            "weights on first use."
        ),
    )
    parser.add_argument(
        "--max-keypoints",
        default="512",
        type=parse_max_keypoints,
        metavar="N|none|default",
        help=(
            "Feature limit to pass as max_num_keypoints. Default: 512. Use "
            "'default' for the class default or 'none' where the selected "
            "extractor supports it. For ALIKED, -1 means threshold-mode default."
        ),
    )
    parser.add_argument(
        "--resize",
        default=1024,
        type=parse_resize,
        metavar="N|none",
        help="Resize long side used by Extractor.extract; use 'none' to disable.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Torch device: cpu, cuda, mps, cuda:0, or auto. Default: cpu.",
    )
    parser.add_argument(
        "--sift-backend",
        default="opencv",
        choices=SIFT_BACKENDS,
        help="SIFT backend for sift and doghardnet extractors. Default: opencv.",
    )
    parser.add_argument(
        "--aliked-model",
        default="aliked-n16",
        choices=ALIKED_MODELS,
        help="ALIKED model variant. Default: aliked-n16.",
    )
    parser.add_argument(
        "--detection-threshold",
        type=float,
        default=None,
        help=(
            "Optional detector threshold override. For ALIKED, values <= 0 with "
            "positive --max-keypoints request fixed top-k behavior."
        ),
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print a traceback for unexpected errors.",
    )
    return parser


def tensor_summary(value: Any) -> Dict[str, Any]:
    import torch

    if torch.is_tensor(value):
        summary: Dict[str, Any] = {
            "type": "torch.Tensor",
            "shape": list(value.shape),
            "dtype": str(value.dtype),
            "device": str(value.device),
        }
        if value.numel() and value.numel() <= 16:
            summary["values"] = value.detach().cpu().tolist()
        return summary
    return {"type": type(value).__name__, "repr": repr(value)}


def resolve_device(requested: str):
    import torch

    if requested == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        mps = getattr(torch.backends, "mps", None)
        if mps is not None and mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    device = torch.device(requested)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise UserError("CUDA was requested but torch.cuda.is_available() is false.")
    if device.type == "mps":
        mps = getattr(torch.backends, "mps", None)
        if mps is None or not mps.is_available():
            raise UserError("MPS was requested but torch.backends.mps is unavailable.")
    return device


def expected_descriptor_dim(extractor_name: str, aliked_model: str) -> int:
    if extractor_name == "superpoint":
        return 256
    if extractor_name == "aliked" and aliked_model == "aliked-t16":
        return 64
    return 128


def matcher_preset(extractor_name: str, aliked_model: str) -> Optional[str]:
    if extractor_name == "doghardnet":
        return "doghardnet"
    if extractor_name == "aliked" and aliked_model == "aliked-t16":
        return None
    return extractor_name


def build_extractor(args: argparse.Namespace):
    from lightglue import ALIKED, DISK, SIFT, DoGHardNet, SuperPoint

    classes = {
        "sift": SIFT,
        "superpoint": SuperPoint,
        "disk": DISK,
        "aliked": ALIKED,
        "doghardnet": DoGHardNet,
    }
    conf: Dict[str, Any] = {}

    max_mode, max_value = args.max_keypoints
    if max_mode == "value":
        conf["max_num_keypoints"] = max_value

    if args.extractor in {"sift", "doghardnet"}:
        conf["backend"] = args.sift_backend
    if args.extractor == "aliked":
        conf["model_name"] = args.aliked_model
        if max_mode == "value" and max_value is None:
            raise UserError("ALIKED does not accept --max-keypoints none; use -1 or a positive integer.")
    if args.detection_threshold is not None:
        conf["detection_threshold"] = args.detection_threshold

    return classes[args.extractor](**conf), conf


def validate_features(features: Dict[str, Any], extractor_name: str, aliked_model: str) -> Dict[str, Any]:
    import torch

    notes = []
    errors = []
    required = ["keypoints", "descriptors", "image_size"]
    if extractor_name in {"sift", "doghardnet"}:
        required.extend(["scales", "oris"])

    for key in required:
        if key not in features:
            errors.append(f"missing required key: {key}")

    kpts = features.get("keypoints")
    desc = features.get("descriptors")
    if torch.is_tensor(kpts) and torch.is_tensor(desc):
        if kpts.ndim != 3 or kpts.shape[-1] != 2:
            errors.append("keypoints should have shape [B,N,2]")
        if desc.ndim != 3:
            errors.append("descriptors should have shape [B,N,D]")
        if kpts.ndim >= 2 and desc.ndim >= 2 and tuple(kpts.shape[:2]) != tuple(desc.shape[:2]):
            errors.append("keypoints and descriptors disagree on [B,N]")
        if desc.ndim == 3:
            expected_dim = expected_descriptor_dim(extractor_name, aliked_model)
            if desc.shape[-1] != expected_dim:
                errors.append(
                    f"descriptor dimension is {desc.shape[-1]}, expected {expected_dim} for {extractor_name}"
                )

    image_size = features.get("image_size")
    if torch.is_tensor(image_size) and tuple(image_size.shape[-1:]) != (2,):
        errors.append("image_size should end with dimension 2 in [width,height] order")

    if extractor_name in {"sift", "doghardnet"}:
        for key in ("scales", "oris"):
            value = features.get(key)
            if torch.is_tensor(value) and torch.is_tensor(kpts) and value.shape != kpts.shape[:2]:
                errors.append(f"{key} should have shape [B,N]")
        notes.append("SIFT-family matcher presets require scales and oris shaped [B,N]; orientations are radians.")

    preset = matcher_preset(extractor_name, aliked_model)
    if preset is None:
        notes.append(
            "ALIKED aliked-t16 emits 64-D descriptors and is not compatible with LightGlue(features='aliked')."
        )
    else:
        notes.append(f"Compatible pretrained matcher preset: LightGlue(features='{preset}').")

    if "keypoint_scores" not in features:
        notes.append("keypoint_scores is optional for LightGlue and may be absent for some SIFT backends.")

    return {"errors": errors, "notes": notes, "ok": not errors}


def run(args: argparse.Namespace) -> int:
    import torch
    from lightglue.utils import load_image

    if not args.image.exists():
        raise UserError(f"Image does not exist: {args.image}")
    if args.extractor != "sift":
        print(
            "note: selected extractor may download pretrained weights on first use if not cached",
            file=sys.stderr,
        )
    if args.extractor == "doghardnet":
        print(
            "note: doghardnet uses SIFT detections plus Kornia HardNet descriptors and may require cached/downloaded weights",
            file=sys.stderr,
        )

    device = resolve_device(args.device)
    image = load_image(args.image).to(device)
    extractor, passed_conf = build_extractor(args)
    extractor = extractor.eval().to(device)

    with torch.no_grad():
        features = extractor.extract(image, resize=args.resize)

    validation = validate_features(features, args.extractor, args.aliked_model)
    output = {
        "extractor": args.extractor,
        "device": str(device),
        "image": {"shape": list(image.shape), "dtype": str(image.dtype)},
        "passed_config": passed_conf,
        "extract_resize": args.resize,
        "features": {key: tensor_summary(value) for key, value in sorted(features.items())},
        "validation": validation,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if validation["ok"] else 3


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return run(args)
    except UserError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    except ImportError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"ImportError: {exc}",
                    "hint": "Install LightGlue runtime dependencies, or use the default SIFT path in an environment with OpenCV SIFT.",
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    except Exception as exc:  # catch backend/download/runtime errors with a concise default report
        if args.debug:
            import traceback

            traceback.print_exc()
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "hint": "For offline schema checks use --extractor sift --sift-backend opencv. Neural extractors and matchers may require pretrained weight downloads or compatible backends.",
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
