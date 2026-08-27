#!/usr/bin/env python3
"""Check an installed stylegan2_pytorch environment without training.

This script verifies CUDA availability, package import, public API signatures,
and optional console-script help. It is safe by default: no models are trained,
no data is downloaded, and no files are written.

Example:
    python scripts/check_install.py
    python scripts/check_install.py --skip-cli-help
"""

from __future__ import annotations

import argparse
import inspect
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version


def _print_heading(title: str) -> None:
    print(f"\n== {title} ==")


def _fail(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def check_torch(require_cuda: bool) -> None:
    _print_heading("PyTorch / CUDA")
    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        _fail(f"Could not import torch: {exc}")

    print(f"torch: {torch.__version__}")
    print(f"torch.version.cuda: {torch.version.cuda}")
    available = torch.cuda.is_available()
    print(f"torch.cuda.is_available(): {available}")
    if not available:
        if require_cuda:
            _fail(
                "stylegan2_pytorch asserts CUDA availability at import time; "
                "install a CUDA-enabled torch/torchvision build or run on a CUDA host.",
                code=2,
            )
        return

    count = torch.cuda.device_count()
    print(f"CUDA device count: {count}")
    if count > 0:
        print(f"device 0: {torch.cuda.get_device_name(0)}")
        print(f"device 0 capability: {torch.cuda.get_device_capability(0)}")
        tensor = torch.empty((1,), device="cuda")
        print(f"tiny CUDA allocation: ok ({tensor.device}, numel={tensor.numel()})")


def check_package() -> None:
    _print_heading("stylegan2_pytorch package")
    try:
        dist_version = version("stylegan2_pytorch")
    except PackageNotFoundError:
        _fail("Distribution metadata for stylegan2_pytorch was not found. Run `pip install stylegan2_pytorch` or `pip install -e .`.")

    print(f"distribution version: {dist_version}")
    try:
        import stylegan2_pytorch
        from stylegan2_pytorch import ModelLoader, NanException, StyleGAN2, Trainer
        import stylegan2_pytorch.cli as cli
    except AssertionError as exc:
        _fail(f"Package import failed its CUDA assertion: {exc}", code=2)
    except Exception as exc:  # pragma: no cover - diagnostic path
        _fail(f"Package import failed: {type(exc).__name__}: {exc}")

    print(f"module file: {getattr(stylegan2_pytorch, '__file__', '<unknown>')}")
    exports = [
        name
        for name in ["Trainer", "StyleGAN2", "ModelLoader", "NanException"]
        if hasattr(stylegan2_pytorch, name)
    ]
    print(f"public exports: {exports}")
    if len(exports) != 4:
        _fail("Expected public exports Trainer, StyleGAN2, ModelLoader, NanException were not all present.")

    print(f"Trainer.__init__: {inspect.signature(Trainer.__init__)}")
    print(f"StyleGAN2.__init__: {inspect.signature(StyleGAN2.__init__)}")
    print(f"ModelLoader.__init__: {inspect.signature(ModelLoader.__init__)}")
    print(f"ModelLoader.noise_to_styles: {inspect.signature(ModelLoader.noise_to_styles)}")
    print(f"ModelLoader.styles_to_images: {inspect.signature(ModelLoader.styles_to_images)}")
    print(f"cli.train_from_folder: {inspect.signature(cli.train_from_folder)}")

    # Keep linters from treating NanException as an unused import in edited copies.
    print(f"NanException class: {NanException.__name__}")


def check_cli_help(timeout: float) -> None:
    _print_heading("CLI help")
    exe = shutil.which("stylegan2_pytorch")
    if exe is None:
        print("WARNING: console script `stylegan2_pytorch` was not found on PATH; package import checks passed.")
        return

    try:
        proc = subprocess.run(
            [exe, "--", "--help"],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        _fail(f"CLI help timed out after {timeout} seconds.")

    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        _fail(f"CLI help exited with status {proc.returncode}.")

    # Python Fire writes help to stderr in some invocation modes and stdout in
    # others, so validate the combined non-empty stream.
    help_output = proc.stdout or proc.stderr
    lines = help_output.splitlines()
    preview = "\n".join(lines[:50])
    print(preview)
    if "FLAGS" not in help_output or "--data" not in help_output:
        _fail("CLI help did not include the expected Fire FLAGS section and --data flag.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a stylegan2_pytorch install without training.")
    parser.add_argument(
        "--allow-no-cuda",
        action="store_true",
        help="Do not fail before import if torch reports no CUDA. Package import will probably still fail for this repo snapshot.",
    )
    parser.add_argument(
        "--skip-cli-help",
        action="store_true",
        help="Skip invoking the installed stylegan2_pytorch console script.",
    )
    parser.add_argument(
        "--cli-timeout",
        type=float,
        default=20.0,
        help="Seconds allowed for the CLI help command.",
    )
    args = parser.parse_args()

    check_torch(require_cuda=not args.allow_no_cuda)
    check_package()
    if not args.skip_cli_help:
        check_cli_help(timeout=args.cli_timeout)

    print("\nstylegan2_pytorch environment check: OK")


if __name__ == "__main__":
    main()
