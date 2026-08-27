#!/usr/bin/env python3
"""Run the bundled Fast Style Transfer image stylization CLI replacement for source evaluate.py.

This wrapper resolves the skill-owned runtime code and then delegates to the
adapted repository CLI. It does not require the original source checkout to
remain available, but it still requires user-supplied runtime assets such as
VGG files, checkpoints, images, videos, and compatible TensorFlow dependencies.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _runtime_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "scripts" / "fast_style_transfer_runtime"


def main() -> int:
    runtime = _runtime_dir()
    if not runtime.exists():
        raise SystemExit(f"Bundled runtime directory not found: {runtime}")
    sys.path.insert(0, str(runtime))
    from evaluate import main as delegated_main  # type: ignore
    delegated_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
