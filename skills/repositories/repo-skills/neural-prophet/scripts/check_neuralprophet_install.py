#!/usr/bin/env python3
"""Check a NeuralProphet installation without requiring source checkout files.

Examples:
    python check_neuralprophet_install.py
    python check_neuralprophet_install.py --check-cuda
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import inspect
import sys
import warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose an installed NeuralProphet package.")
    parser.add_argument("--check-cuda", action="store_true", help="Also report torch CUDA availability and run a tiny CUDA allocation if possible.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
    try:
        version = metadata.version("neuralprophet")
    except metadata.PackageNotFoundError:
        print("neuralprophet distribution metadata was not found", file=sys.stderr)
        return 1
    try:
        import neuralprophet
        from neuralprophet import NeuralProphet, TorchProphet
    except Exception as exc:
        print(f"import neuralprophet failed: {exc}", file=sys.stderr)
        print("If the error mentions pkg_resources, try: python -m pip install 'setuptools<81'", file=sys.stderr)
        print("If a fit later fails with pandas Series.view, try: python -m pip install 'pandas<3'", file=sys.stderr)
        return 1

    print({"distribution": "neuralprophet", "version": version, "module_version": getattr(neuralprophet, "__version__", None)})
    print("NeuralProphet", inspect.signature(NeuralProphet))
    print("TorchProphet", inspect.signature(TorchProphet))

    try:
        import torch
    except Exception as exc:
        print(f"torch import failed: {exc}", file=sys.stderr)
        return 1
    print({"torch": torch.__version__, "cuda_runtime": torch.version.cuda, "cuda_available": torch.cuda.is_available(), "cuda_device_count": torch.cuda.device_count()})
    x = torch.tensor([1.0, 2.0])
    if float(x.sum()) != 3.0:
        print("torch CPU tensor check failed", file=sys.stderr)
        return 1
    if args.check_cuda:
        if not torch.cuda.is_available():
            print("CUDA was requested but torch.cuda.is_available() is False", file=sys.stderr)
            return 1
        y = torch.empty((1,), device="cuda")
        print({"cuda_device": torch.cuda.get_device_name(0), "cuda_capability": torch.cuda.get_device_capability(0), "cuda_tensor_shape": tuple(y.shape)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
