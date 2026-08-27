#!/usr/bin/env python3
"""Static checker for LTP Rust/CFFI layout and prerequisites.

This script does not build. It checks manifests, optional toolchain presence,
and optional legacy model files in a user-supplied checkout/staging directory.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check LTP Rust crate/CFFI layout without building.")
    parser.add_argument("--repo-root", default=".", help="LTP checkout or staged source tree")
    parser.add_argument("--require-toolchain", action="store_true", help="fail if cargo/rustc are missing")
    parser.add_argument("--require-models", action="store_true", help="fail if data/legacy-models/*.bin files are missing")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    errors = []
    warnings = []
    required_files = [
        "Cargo.toml",
        "rust/ltp/Cargo.toml",
        "rust/ltp/src/lib.rs",
        "rust/ltp-cffi/Cargo.toml",
        "rust/ltp-cffi/src/lib.rs",
    ]
    for rel in required_files:
        if not (root / rel).is_file():
            errors.append(f"missing {rel}")

    cargo = shutil.which("cargo")
    rustc = shutil.which("rustc")
    if not cargo or not rustc:
        msg = f"Rust toolchain incomplete: cargo={cargo or 'missing'} rustc={rustc or 'missing'}"
        if args.require_toolchain:
            errors.append(msg)
        else:
            warnings.append(msg)

    model_dir = root / "data" / "legacy-models"
    model_files = [model_dir / "cws_model.bin", model_dir / "pos_model.bin", model_dir / "ner_model.bin"]
    for path in model_files:
        if not path.is_file():
            msg = f"legacy model file missing: {path}"
            if args.require_models:
                errors.append(msg)
            else:
                warnings.append(msg)

    print(f"repo_root={root}")
    print(f"cargo={cargo or 'missing'}")
    print(f"rustc={rustc or 'missing'}")
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"- {warning}")
    if errors:
        print("errors:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Rust/CFFI layout check passed for the requested strictness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
