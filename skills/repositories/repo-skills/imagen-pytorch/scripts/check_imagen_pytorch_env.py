#!/usr/bin/env python3
"""Safe import and backend check for imagen-pytorch.

This helper verifies the installed package surface without loading datasets,
training, sampling, downloading T5 weights, or relying on a source checkout.

Examples:
  python check_imagen_pytorch_env.py
  python check_imagen_pytorch_env.py --check-cuda --check-cli
  python check_imagen_pytorch_env.py --print-signatures
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import inspect
import sys
from typing import Iterable


CORE_IMPORTS = [
    ("imagen_pytorch", "Imagen"),
    ("imagen_pytorch", "Unet"),
    ("imagen_pytorch", "ImagenTrainer"),
    ("imagen_pytorch", "ElucidatedImagen"),
    ("imagen_pytorch", "Unet3D"),
]

SIGNATURE_TARGETS = [
    "Unet",
    "Imagen",
    "ElucidatedImagen",
    "Unet3D",
    "ImagenTrainer",
    "ImagenConfig",
    "ElucidatedImagenConfig",
]


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def import_symbol(module_name: str, symbol: str):
    module = __import__(module_name, fromlist=[symbol])
    return getattr(module, symbol)


def check_core_imports(print_signatures: bool) -> int:
    try:
        import imagen_pytorch  # noqa: F401
    except ModuleNotFoundError as exc:
        missing = exc.name or str(exc)
        return fail(
            f"could not import imagen_pytorch because dependency {missing!r} is missing. "
            "Install with `pip install imagen-pytorch` in the active environment."
        )
    except Exception as exc:  # pragma: no cover - diagnostic output only
        return fail(f"could not import imagen_pytorch: {type(exc).__name__}: {exc}")

    try:
        dist_version = metadata.version("imagen-pytorch")
    except metadata.PackageNotFoundError:
        dist_version = "not-found"

    import imagen_pytorch

    package_version = getattr(imagen_pytorch, "__version__", "unknown")
    print(f"imagen-pytorch distribution version: {dist_version}")
    print(f"imagen_pytorch package version: {package_version}")

    imported = []
    objects = {}
    for module_name, symbol in CORE_IMPORTS:
        try:
            objects[symbol] = import_symbol(module_name, symbol)
            imported.append(symbol)
        except Exception as exc:
            return fail(f"failed importing {symbol} from {module_name}: {type(exc).__name__}: {exc}")

    print("core public imports: " + ", ".join(imported))

    if print_signatures:
        for name in SIGNATURE_TARGETS:
            try:
                obj = getattr(imagen_pytorch, name)
            except AttributeError:
                continue
            try:
                sig = inspect.signature(obj)
            except (TypeError, ValueError):
                sig = "<signature unavailable>"
            print(f"signature {name}{sig}")

    return 0


def check_cuda() -> int:
    try:
        import torch
    except Exception as exc:
        return fail(f"could not import torch for CUDA check: {type(exc).__name__}: {exc}")

    print(f"torch version: {getattr(torch, '__version__', 'unknown')}")
    available = bool(torch.cuda.is_available())
    print(f"torch.cuda.is_available: {available}")
    if not available:
        print("CUDA unavailable: CPU smoke can still validate imports/configs, but realistic generation/training is CUDA-scale.")
        return 0

    try:
        x = torch.ones(1, device="cuda")
        print(f"cuda tensor allocation: ok sum={float(x.sum().item())}")
    except Exception as exc:
        return fail(f"CUDA was reported available but tensor allocation failed: {type(exc).__name__}: {exc}")
    return 0


def check_cli() -> int:
    try:
        from imagen_pytorch.cli import imagen
    except ModuleNotFoundError as exc:
        missing = exc.name or str(exc)
        return fail(f"could not import imagen CLI because dependency {missing!r} is missing")
    except Exception as exc:
        return fail(f"could not import imagen CLI: {type(exc).__name__}: {exc}")

    commands = sorted(getattr(imagen, "commands", {}).keys())
    if not commands:
        return fail("imagen CLI group imported but no commands were registered")
    print("imagen CLI commands: " + ", ".join(commands))
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check imagen-pytorch import, version, optional CUDA, and CLI surface safely.")
    parser.add_argument("--check-cuda", action="store_true", help="Also verify torch CUDA visibility and a one-element CUDA tensor allocation when available.")
    parser.add_argument("--check-cli", action="store_true", help="Also import the imagen Click command group and list registered commands.")
    parser.add_argument("--print-signatures", action="store_true", help="Print selected public API signatures for inspection.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    exit_code = check_core_imports(print_signatures=args.print_signatures)
    if exit_code:
        return exit_code

    if args.check_cuda:
        exit_code = check_cuda()
        if exit_code:
            return exit_code

    if args.check_cli:
        exit_code = check_cli()
        if exit_code:
            return exit_code

    print("imagen-pytorch environment check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
