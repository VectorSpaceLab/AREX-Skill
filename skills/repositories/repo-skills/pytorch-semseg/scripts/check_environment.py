#!/usr/bin/env python3
"""Check a pytorch-semseg runtime environment without training or reading data.

This helper verifies imports, optional backend visibility, and selected legacy
compatibility hazards. With --smoke it also runs a tiny no-download FRRN CPU
forward pass and a metrics update. It never downloads weights, opens datasets,
writes checkpoints, or runs repository training/inference entry points.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Iterable


def _version(module: object) -> str:
    return str(getattr(module, "__version__", "unknown"))


def _try_import(name: str) -> tuple[bool, str]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - depends on caller env
        return False, f"{type(exc).__name__}: {exc}"
    return True, _version(module)


def print_imports(names: Iterable[str]) -> bool:
    ok = True
    print("Import checks:")
    for name in names:
        passed, detail = _try_import(name)
        status = "OK" if passed else "FAIL"
        print(f"  {status:4} {name}: {detail}")
        ok = ok and passed
    return ok


def check_torch_backend() -> None:
    try:
        import torch
    except Exception as exc:  # pragma: no cover
        print(f"Torch backend: unavailable ({exc})")
        return
    print("Torch backend:")
    print(f"  torch: {_version(torch)}")
    print(f"  torch.version.cuda: {torch.version.cuda}")
    print(f"  cuda_available: {torch.cuda.is_available()}")
    print(f"  cuda_device_count: {torch.cuda.device_count()}")
    if torch.cuda.is_available():
        try:
            print(f"  cuda_device_0: {torch.cuda.get_device_name(0)}")
        except Exception as exc:  # pragma: no cover
            print(f"  cuda_device_0: query failed ({exc})")


def check_legacy_hazards() -> None:
    print("Compatibility notes:")
    try:
        import google.protobuf
        protobuf_version = _version(google.protobuf)
        print(f"  protobuf: {protobuf_version}")
        major_minor = tuple(int(part) for part in protobuf_version.split(".")[:2] if part.isdigit())
        if major_minor and major_minor >= (3, 21):
            print("  WARN caffe_pb2 may fail; use protobuf<3.21 or PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python.")
    except Exception as exc:
        print(f"  WARN protobuf unavailable: {exc}")
    try:
        import scipy.misc as misc  # noqa: F401
        missing = [name for name in ("imread", "imresize", "imsave", "toimage") if not hasattr(misc, name)]
        if missing:
            print("  WARN scipy.misc lacks legacy image helpers: " + ", ".join(missing))
        else:
            print("  scipy.misc legacy image helpers present")
    except Exception as exc:
        print(f"  WARN scipy.misc import failed: {exc}")
    try:
        import pydensecrf.densecrf  # noqa: F401
        print("  pydensecrf: available")
    except Exception:
        print("  INFO pydensecrf unavailable; test.py --dcrf will not work without installing it.")


def run_smoke(height: int, width: int, n_classes: int) -> bool:
    try:
        import numpy as np
        import torch
        from ptsemseg.loader import get_loader
        from ptsemseg.metrics import runningScore
        from ptsemseg.models import get_model
    except Exception as exc:
        print(f"Smoke import failed: {type(exc).__name__}: {exc}")
        return False

    ok = True
    try:
        model = get_model({"arch": "frrnA", "model_type": "A"}, n_classes=n_classes)
        model.eval()
        x = torch.zeros(1, 3, height, width)
        with torch.no_grad():
            y = model(x)
        print(f"FRRN smoke output_shape: {tuple(y.shape)}")
        ok = ok and tuple(y.shape)[1] == n_classes
    except Exception as exc:
        print(f"FRRN smoke failed: {type(exc).__name__}: {exc}")
        ok = False

    try:
        loader = get_loader("pascal")(root=None, test_mode=True)
        print(f"Pascal test-mode loader n_classes: {loader.n_classes}")
    except Exception as exc:
        print(f"Pascal loader smoke failed: {type(exc).__name__}: {exc}")
        ok = False

    try:
        rs = runningScore(2)
        rs.update([np.array([[0, 1], [1, 1]])], [np.array([[0, 1], [0, 1]])])
        scores, class_iou = rs.get_scores()
        print("Metric keys: " + ", ".join(sorted(scores.keys())))
        print("Class IoU keys: " + ", ".join(str(k) for k in sorted(class_iou.keys())))
    except Exception as exc:
        print(f"Metrics smoke failed: {type(exc).__name__}: {exc}")
        ok = False

    return ok


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check pytorch-semseg imports, backend visibility, and safe API smoke tests.")
    parser.add_argument("--smoke", action="store_true", help="Run a tiny FRRN/Pascal-loader/metrics smoke test.")
    parser.add_argument("--height", type=int, default=64, help="FRRN smoke input height; default 64.")
    parser.add_argument("--width", type=int, default=64, help="FRRN smoke input width; default 64.")
    parser.add_argument("--n-classes", type=int, default=2, help="FRRN smoke output classes; default 2.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    required = [
        "torch",
        "torchvision",
        "numpy",
        "scipy",
        "PIL",
        "yaml",
        "tqdm",
        "tensorboardX",
        "ptsemseg",
        "ptsemseg.models",
        "ptsemseg.loader",
        "ptsemseg.metrics",
    ]
    ok = print_imports(required)
    print("")
    check_torch_backend()
    print("")
    check_legacy_hazards()
    if args.smoke:
        print("")
        ok = run_smoke(args.height, args.width, args.n_classes) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
