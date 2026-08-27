#!/usr/bin/env python3
"""Safe pytorch-semseg model registry inspection and FRRN smoke helper.

This script intentionally avoids datasets, checkpoints, training, writes, and
network/download-triggering model paths by default.
"""

from __future__ import annotations

import argparse
import os
import sys
import warnings
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict

MODEL_IDS = [
    "fcn32s",
    "fcn16s",
    "fcn8s",
    "unet",
    "segnet",
    "pspnet",
    "icnet",
    "icnetBN",
    "linknet",
    "frrnA",
    "frrnB",
]

DOWNLOAD_RISK_MODEL_IDS = {"fcn32s", "fcn16s", "fcn8s", "segnet"}
FRRN_MODEL_TYPES = {"frrnA": "A", "frrnB": "B"}


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List pytorch-semseg registries and optionally run a safe CPU FRRN forward smoke.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="list registry keys and utility availability, then exit without a model forward",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="run a no-download CPU forward smoke; supported for frrnA/frrnB only",
    )
    parser.add_argument(
        "--model-id",
        choices=MODEL_IDS,
        default="frrnA",
        help="model id to inspect or smoke",
    )
    parser.add_argument("--n-classes", type=positive_int, default=2, help="number of output classes")
    parser.add_argument("--height", type=positive_int, default=64, help="dummy input height")
    parser.add_argument("--width", type=positive_int, default=64, help="dummy input width")
    return parser.parse_args(argv)


def format_keys(values: Any) -> str:
    return ", ".join(str(value) for value in sorted(values))


def ensure_source_root_on_path() -> None:
    """Make ptsemseg importable when this helper is run from inside the repo tree."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "ptsemseg" / "__init__.py").is_file():
            sys.path.insert(0, str(parent))
            return


def import_ptsemseg_api() -> Dict[str, Any]:
    ensure_source_root_on_path()
    # pspnet/icnet import generated caffe_pb2 metadata. This environment variable
    # keeps registry inspection usable with modern protobuf; a protobuf<3.21 pin is
    # still preferred for normal environments.
    os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

    # Avoid leaking environment-specific source paths from known compatibility warnings.
    warnings.filterwarnings("ignore", category=FutureWarning)

    try:
        import numpy as np
        import torch
        from ptsemseg import models as model_api
        from ptsemseg.augmentations import key2aug
        from ptsemseg.loss import key2loss
        from ptsemseg.metrics import averageMeter, runningScore
        from ptsemseg.optimizers import key2opt
        from ptsemseg.schedulers import key2scheduler
        from ptsemseg.utils import convert_state_dict
    except Exception as exc:  # pragma: no cover - exercised by broken user envs
        print("ERROR: failed to import pytorch-semseg APIs.", file=sys.stderr)
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        print("Hints:", file=sys.stderr)
        print("  - Run from the repository root or put the source root on PYTHONPATH.", file=sys.stderr)
        print("  - If the message mentions protobuf descriptors/caffe_pb2, install protobuf<3.21", file=sys.stderr)
        print("    or set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python.", file=sys.stderr)
        print("  - Ensure torch, torchvision, numpy, scipy, Pillow, PyYAML, and tqdm are installed.", file=sys.stderr)
        raise SystemExit(1)

    return {
        "np": np,
        "torch": torch,
        "model_api": model_api,
        "key2aug": key2aug,
        "key2loss": key2loss,
        "key2opt": key2opt,
        "key2scheduler": key2scheduler,
        "runningScore": runningScore,
        "averageMeter": averageMeter,
        "convert_state_dict": convert_state_dict,
    }


def print_registries(api: Dict[str, Any]) -> None:
    print("pytorch-semseg registry inspection")
    print(f"models: {format_keys(MODEL_IDS)}")
    print(f"losses: {format_keys(api['key2loss'].keys())}")
    print(f"optimizers: {format_keys(api['key2opt'].keys())}")
    print(f"schedulers: {format_keys(api['key2scheduler'].keys())}")
    print(f"augmentations: {format_keys(api['key2aug'].keys())}")
    print("utilities: runningScore, averageMeter, convert_state_dict")
    print("warnings:")
    print("  - FCN and SegNet get_model paths call torchvision.models.vgg16(pretrained=True).")
    print("  - frrnA/frrnB both use the frrn constructor; pass model_type='A' or 'B' explicitly.")
    print("  - Very small inputs can fail in deep architectures; the FRRN smoke default is 64x64.")


def run_utility_smoke(api: Dict[str, Any]) -> None:
    np = api["np"]
    runningScore = api["runningScore"]
    averageMeter = api["averageMeter"]
    convert_state_dict = api["convert_state_dict"]

    scorer = runningScore(2)
    scorer.update([np.array([[0, 1], [1, 0]])], [np.array([[0, 1], [0, 0]])])
    scores, cls_iu = scorer.get_scores()
    meter = averageMeter()
    meter.update(4.0, n=2)
    converted = convert_state_dict(OrderedDict([("module.layer.weight", "dummy")]))

    print("utility smoke:")
    print(f"  runningScore keys: {format_keys(scores.keys())}; class IoU keys: {format_keys(cls_iu.keys())}")
    print(f"  averageMeter avg after update: {meter.avg}")
    print(f"  convert_state_dict stripped prefix: {'layer.weight' in converted}")


def run_model_smoke(api: Dict[str, Any], args: argparse.Namespace) -> int:
    model_id = args.model_id
    if model_id in DOWNLOAD_RISK_MODEL_IDS:
        print(
            f"SAFE-SKIP: {model_id} is not instantiated by this helper because its get_model path "
            "can trigger torchvision VGG pretrained weight cache/network access.",
            file=sys.stderr,
        )
        print("Use --list-only or choose frrnA/frrnB for a no-download CPU smoke.", file=sys.stderr)
        return 2

    if model_id not in FRRN_MODEL_TYPES:
        print(
            f"SAFE-SKIP: --smoke supports only frrnA/frrnB. {model_id} is listed, but not "
            "forward-smoked by this helper to avoid architecture-specific size/runtime surprises.",
            file=sys.stderr,
        )
        return 2

    torch = api["torch"]
    model_api = api["model_api"]
    model_type = FRRN_MODEL_TYPES[model_id]
    payload = {"arch": model_id, "model_type": model_type}

    print("model smoke:")
    print(f"  payload: {payload}")
    print(f"  n_classes: {args.n_classes}")
    print(f"  input_shape: (1, 3, {args.height}, {args.width})")

    try:
        model = model_api.get_model(payload, n_classes=args.n_classes)
        model.cpu().eval()
        x = torch.randn(1, 3, args.height, args.width, device="cpu")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with torch.no_grad():
                y = model(x)
    except Exception as exc:
        print("ERROR: FRRN smoke failed.", file=sys.stderr)
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        print("Hints:", file=sys.stderr)
        print("  - Try the default 64x64 input or larger.", file=sys.stderr)
        print("  - Ensure model_type is explicit: 'A' for frrnA, 'B' for frrnB.", file=sys.stderr)
        print("  - Check protobuf/caffe_pb2 troubleshooting if import failed before construction.", file=sys.stderr)
        return 1

    shape = tuple(y.shape) if hasattr(y, "shape") else type(y).__name__
    print(f"  output_shape: {shape}")
    if caught:
        unique_messages = []
        for warning in caught:
            message = str(warning.message)
            if message not in unique_messages:
                unique_messages.append(message)
        print("  compatibility_warnings:")
        for message in unique_messages[:5]:
            print(f"    - {message}")
        if len(unique_messages) > 5:
            print(f"    - ... {len(unique_messages) - 5} more warning(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    api = import_ptsemseg_api()
    print_registries(api)
    run_utility_smoke(api)

    if args.smoke:
        return run_model_smoke(api, args)

    if not args.list_only:
        print("No --smoke requested; completed list-only inspection by default.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
