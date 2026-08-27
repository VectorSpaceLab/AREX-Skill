#!/usr/bin/env python3
"""Run MimicMotion local inference from a checkout.

This is a small wrapper around the repository's inference entry point. It adds a
`--repo-root` argument so future agents can run the workflow from any working
directory without hardcoding checkout paths.

Typical usage:
    python scripts/run_inference.py --repo-root /path/to/MimicMotion \
        --inference-config configs/test.yaml --output-dir outputs/
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_runtime import validate_runtime


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MimicMotion local inference.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Path to a MimicMotion checkout")
    parser.add_argument(
        "--inference-config",
        type=Path,
        default=Path("configs/test.yaml"),
        help="Path to the inference config relative to the repository root unless absolute",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"), help="Directory for generated videos")
    parser.add_argument("--log-file", type=Path, default=None, help="Optional explicit log file path")
    parser.add_argument(
        "--no-use-float16",
        action="store_true",
        help="Disable the float16 default dtype used by the source CLI",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = args.repo_root.resolve()
    if not repo_root.exists():
        print(f"[FAIL] repo root does not exist: {repo_root}", file=sys.stderr)
        return 2

    # Mimic the source CLI's expectation that relative paths resolve from the
    # repository checkout.
    os.chdir(repo_root)
    sys.path.insert(0, str(repo_root))

    try:
        validate_runtime(repo_root, repo_root / "models", skip_models=False)
    except Exception as exc:  # pragma: no cover - surfaced to user
        print(f"[FAIL] preflight failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    import inference as source_inference  # noqa: WPS433 - deliberate runtime import

    output_dir = args.output_dir if args.output_dir.is_absolute() else repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.log_file is None:
        log_file = output_dir / f"{datetime.now().strftime('%Y%m%d%H%M%S')}.log"
    else:
        log_file = args.log_file if args.log_file.is_absolute() else repo_root / args.log_file

    runtime_args = argparse.Namespace(
        log_file=str(log_file),
        inference_config=str(args.inference_config),
        output_dir=str(output_dir),
        no_use_float16=bool(args.no_use_float16),
    )

    source_inference.set_logger(runtime_args.log_file)
    source_inference.main(runtime_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
