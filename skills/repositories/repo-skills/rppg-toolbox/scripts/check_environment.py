#!/usr/bin/env python3
"""Read-only environment probe for rPPG-Toolbox dependencies and backends.

This helper does not import the source checkout, install packages, download
weights, or write files. It reports which public modules are discoverable and,
when requested, whether one CUDA device can allocate a tiny tensor.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from typing import Iterable, Optional


REQUIRED_MODULES = (
    "numpy",
    "scipy",
    "pandas",
    "cv2",
    "yaml",
    "yacs",
    "skimage",
    "sklearn",
    "torch",
    "timm",
)
MAMBA_MODULES = ("causal_conv1d", "mamba_ssm")


def parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--cuda",
        action="store_true",
        help="require one CUDA device and perform a tiny allocation",
    )
    result.add_argument(
        "--mamba",
        action="store_true",
        help="also require causal_conv1d and mamba_ssm imports",
    )
    return result


def module_status(names: Iterable[str]) -> bool:
    """Print import-spec status and return whether every module is present."""
    ok = True
    for name in names:
        present = importlib.util.find_spec(name) is not None
        print(f"{'PASS' if present else 'MISSING'} module={name}")
        ok = ok and present
    return ok


def cuda_status() -> bool:
    """Check CUDA availability and allocate one small tensor."""
    try:
        import torch
    except Exception as exc:
        print(f"BLOCKED cuda=missing-torch error={type(exc).__name__}: {exc}")
        return False
    if not torch.cuda.is_available() or torch.cuda.device_count() < 1:
        print("BLOCKED cuda=no-visible-device")
        return False
    try:
        device = torch.device("cuda:0")
        value = torch.ones((1,), device=device)
        print(
            "PASS cuda="
            f"{torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)} "
            f"value={value.item():g}"
        )
        return True
    except Exception as exc:
        print(f"BLOCKED cuda=allocation-error error={type(exc).__name__}: {exc}")
        return False


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Run requested read-only checks."""
    args = parser().parse_args(argv)
    print(f"python={sys.version.split()[0]}")
    ok = module_status(REQUIRED_MODULES)
    if args.mamba:
        ok = module_status(MAMBA_MODULES) and ok
    if args.cuda:
        ok = cuda_status() and ok
    print(f"RESULT: {'PASS' if ok else 'BLOCKED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
