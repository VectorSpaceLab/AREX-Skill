#!/usr/bin/env python3
"""Verify a stitching installation from the target Python environment.

This helper is safe to run from any current working directory. It imports the
installed package, confirms a few public defaults, and runs the public CLI help
through `python -m stitching.cli.stitch --help`.

Optional:
  --repo-root PATH   Prepend a local checkout to sys.path before importing.

Example:
  python scripts/check_install.py
  python scripts/check_install.py --json
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Optional local checkout to inspect instead of only the installed package.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON report instead of human-readable text.",
    )
    return parser.parse_args()


def maybe_prepend_repo_root(repo_root: Path | None) -> None:
    if repo_root is None:
        return
    repo_root = repo_root.resolve()
    sys.path.insert(0, str(repo_root))


def run_cli_help() -> dict:
    cmd = [sys.executable, "-m", "stitching.cli.stitch", "--help"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout_head": proc.stdout.splitlines()[:12],
        "stderr_head": proc.stderr.splitlines()[:12],
    }


def main() -> int:
    args = parse_args()
    maybe_prepend_repo_root(args.repo_root)

    try:
        stitching = importlib.import_module("stitching")
        from stitching import AffineStitcher, Stitcher
        from stitching.feature_detector import FeatureDetector
        from stitching.feature_matcher import FeatureMatcher
        from stitching.images import Images
    except Exception as exc:  # pragma: no cover - diagnostic helper
        payload = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload["error"])
        return 1

    report = {
        "ok": True,
        "package": {
            "name": getattr(stitching, "__name__", "stitching"),
            "version": getattr(stitching, "__version__", None),
        },
        "imports": {
            "Stitcher": str(inspect.signature(Stitcher)),
            "AffineStitcher": str(inspect.signature(AffineStitcher)),
            "FeatureDetector": str(inspect.signature(FeatureDetector)),
            "FeatureMatcher": str(inspect.signature(FeatureMatcher)),
            "Images.of": str(inspect.signature(Images.of)),
        },
        "defaults": {
            "detectors": list(FeatureDetector.DETECTOR_CHOICES.keys()),
            "matchers": list(FeatureMatcher.MATCHER_CHOICES),
            "image_resolutions": {
                key: value.value for key, value in Images.Resolution.__members__.items()
            },
        },
        "cli_help": run_cli_help(),
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"stitching {report['package']['version']} imported successfully")
        print(f"Stitcher: {report['imports']['Stitcher']}")
        print(f"AffineStitcher: {report['imports']['AffineStitcher']}")
        print(f"Detectors: {', '.join(report['defaults']['detectors'])}")
        print(f"Matchers: {', '.join(report['defaults']['matchers'])}")
        print(f"CLI help exit code: {report['cli_help']['returncode']}")
        if report['cli_help']['stdout_head']:
            print("CLI help preview:")
            for line in report['cli_help']['stdout_head']:
                print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
