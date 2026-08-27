#!/usr/bin/env python3
"""Preflight the VITS checkout, dependencies, CUDA, and model imports.

Prereqs:
- Run from any working directory with `--repo-root` pointing at a VITS checkout.
- Requires the repo dependencies to be installed in the active Python.
- Use `--allow-cpu` only when you want import-only checks without a CUDA gate.

Example:
  python scripts/check_install.py --repo-root /path/to/vits
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the VITS environment and imports.")
    parser.add_argument("--repo-root", required=True, help="Path to the VITS checkout.")
    parser.add_argument(
        "--allow-cpu",
        action="store_true",
        help="Do not fail if CUDA is unavailable.",
    )
    parser.add_argument(
        "--check-english-cleaners",
        action="store_true",
        help="Run english_cleaners2 and require an installed espeak backend.",
    )
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        return fail(f"repo root not found: {repo_root}")
    sys.path.insert(0, str(repo_root))

    print(f"repo_root={repo_root}")

    try:
        import torch
        import librosa  # noqa: F401
        import phonemizer  # noqa: F401
        import tensorboard  # noqa: F401
        import Cython  # noqa: F401
        import scipy  # noqa: F401
        import data_utils  # noqa: F401
        import losses  # noqa: F401
        import mel_processing  # noqa: F401
        import text  # noqa: F401
        from text import cleaners
        import utils
        import models
        import monotonic_align
    except Exception as exc:  # pragma: no cover - diagnostic output
        return fail(f"import failure: {type(exc).__name__}: {exc}")

    print(f"torch={torch.__version__} cuda={torch.version.cuda}")
    print(f"cuda_available={torch.cuda.is_available()} device_count={torch.cuda.device_count()}")
    if not args.allow_cpu:
        require(torch.cuda.is_available(), "CUDA is required for the main VITS workflows")
        x = torch.empty((1,), device="cuda")
        print(f"cuda_alloc={x.device}")

    print(f"models={models.__name__} monotonic_align={monotonic_align.__name__}")
    path = monotonic_align.maximum_path(torch.zeros(1, 2, 2), torch.ones(1, 2, 2))
    print(f"maximum_path_shape={tuple(path.shape)}")

    print(f"basic_cleaners={cleaners.basic_cleaners('  A B  ')}")
    print(f"transliteration_cleaners={cleaners.transliteration_cleaners('Mañana  ')}")
    espeak = shutil.which("espeak") or shutil.which("espeak-ng")
    print(f"espeak_binary={espeak or 'missing'}")
    if args.check_english_cleaners:
        try:
            print(f"english_cleaners2={cleaners.english_cleaners2('VITS is Awesome!')}")
        except Exception as exc:  # pragma: no cover - diagnostic output
            return fail(f"english_cleaners2 failed: {type(exc).__name__}: {exc}")
    elif espeak is None:
        print("note: english_cleaners2 will fail until espeak or espeak-ng is installed")

    hps = utils.get_hparams_from_file(repo_root / "configs" / "ljs_nosdp.json")
    print(f"config_check_ok={hps.data.sampling_rate}Hz")
    print("install_check=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
