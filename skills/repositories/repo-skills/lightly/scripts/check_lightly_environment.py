#!/usr/bin/env python3
"""Check a LightlySSL Python environment without downloading data.

Examples:
  python scripts/check_lightly_environment.py
  python scripts/check_lightly_environment.py --components import tensor cli
  python scripts/check_lightly_environment.py --device auto
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import shutil
import subprocess
import sys
from importlib import metadata


def _version(dist: str) -> str:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return "not-installed"


def check_imports() -> int:
    modules = [
        "lightly",
        "lightly.data",
        "lightly.loss",
        "lightly.transforms",
        "lightly.models.modules",
        "lightly.cli",
    ]
    for name in modules:
        try:
            importlib.import_module(name)
            print(f"import ok: {name}")
        except Exception as exc:  # pragma: no cover - diagnostic path
            print(f"import failed: {name}: {exc}", file=sys.stderr)
            return 1
    print("versions:", {"lightly": _version("lightly"), "torch": _version("torch"), "torchvision": _version("torchvision"), "pytorch-lightning": _version("pytorch-lightning")})
    return 0


def check_optional() -> int:
    checks = {
        "timm": "TIMM-backed ViT/MAE/IJEPA/CAPI/Pixio modules",
        "av": "direct video-file datasets through PyAV",
    }
    for module, purpose in checks.items():
        spec = importlib.util.find_spec(module)
        status = "available" if spec else "missing"
        print(f"optional {module}: {status} ({purpose})")
    return 0


def check_tensor(device: str) -> int:
    try:
        import torch
        from lightly.loss import NTXentLoss
        from lightly.models.modules import SimCLRProjectionHead
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"tensor smoke import failed: {exc}", file=sys.stderr)
        return 1
    if device == "auto":
        selected = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        selected = device
    if selected == "cuda" and not torch.cuda.is_available():
        print("CUDA requested but torch.cuda.is_available() is false", file=sys.stderr)
        return 2
    model = SimCLRProjectionHead(input_dim=8, hidden_dim=16, output_dim=4).to(selected)
    z0 = model(torch.randn(4, 8, device=selected))
    z1 = model(torch.randn(4, 8, device=selected))
    loss = NTXentLoss()(z0, z1)
    if not torch.isfinite(loss):
        print(f"non-finite loss: {loss}", file=sys.stderr)
        return 3
    print(f"tensor smoke ok: device={selected} z_shape={tuple(z0.shape)} loss={float(loss.detach()):.6f}")
    return 0


def check_cli() -> int:
    exe = shutil.which("lightly-version")
    if not exe:
        print("lightly-version executable not found on PATH", file=sys.stderr)
        return 1
    proc = subprocess.run([exe], text=True, capture_output=True, check=False, timeout=20)
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        return proc.returncode
    print(proc.stdout.strip())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe LightlySSL environment preflight.")
    parser.add_argument("--components", nargs="+", choices=["import", "optional", "tensor", "cli"], default=["import", "optional", "tensor"], help="Checks to run.")
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="cpu", help="Device for the tensor smoke.")
    args = parser.parse_args()
    checks = {
        "import": check_imports,
        "optional": check_optional,
        "tensor": lambda: check_tensor(args.device),
        "cli": check_cli,
    }
    for component in args.components:
        code = checks[component]()
        if code:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
