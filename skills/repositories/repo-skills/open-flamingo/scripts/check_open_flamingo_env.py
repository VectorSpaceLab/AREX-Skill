#!/usr/bin/env python3
"""Check an installed OpenFlamingo environment without downloads or training.

The check imports public OpenFlamingo APIs, prints key package versions, verifies
important signatures, and optionally checks that packaged training/evaluation
entrypoint files are present. It does not instantiate models or contact model
hubs.

Example:
    python scripts/check_open_flamingo_env.py --json
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
from importlib import metadata
from pathlib import Path
from typing import Any, Dict


def version_or_missing(dist: str) -> str:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return "missing"


def build_report(check_entrypoints: bool) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "ok": True,
        "versions": {
            "open_flamingo": version_or_missing("open_flamingo"),
            "torch": version_or_missing("torch"),
            "torchvision": version_or_missing("torchvision"),
            "transformers": version_or_missing("transformers"),
            "open_clip_torch": version_or_missing("open-clip-torch"),
            "webdataset": version_or_missing("webdataset"),
            "scikit-learn": version_or_missing("scikit-learn"),
        },
        "imports": {},
        "signatures": {},
        "entrypoints": {},
        "warnings": [],
    }

    try:
        import torch
        import open_flamingo
        from open_flamingo import Flamingo, create_model_and_transforms
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["ok"] = False
        report["imports"]["open_flamingo"] = f"failed: {type(exc).__name__}: {exc}"
        return report

    report["imports"]["open_flamingo"] = "passed"
    report["cuda_available"] = bool(getattr(torch, "cuda", None) and torch.cuda.is_available())
    report["signatures"]["create_model_and_transforms"] = str(inspect.signature(create_model_and_transforms))
    report["signatures"]["Flamingo.forward"] = str(inspect.signature(Flamingo.forward))
    report["signatures"]["Flamingo.generate"] = str(inspect.signature(Flamingo.generate))

    if report["versions"]["scikit-learn"] == "missing":
        report["warnings"].append(
            "scikit-learn is missing; OpenFlamingo evaluate.py imports sklearn.metrics even though setup.py's eval extra may omit it."
        )
    if report["versions"]["transformers"].startswith("4.5"):
        report["warnings"].append(
            "Very new Transformers releases may require newer torch than OpenFlamingo's pinned torch==2.0.1; use a compatible Transformers release if PyTorch support is disabled."
        )

    if check_entrypoints:
        spec = importlib.util.find_spec("open_flamingo")
        if spec is None or spec.origin is None:
            report["ok"] = False
            report["entrypoints"]["package_dir"] = "missing"
        else:
            package_dir = Path(spec.origin).resolve().parent
            for label, rel in {
                "train": "train/train.py",
                "evaluate": "eval/evaluate.py",
                "cache_rices": "scripts/cache_rices_features.py",
            }.items():
                report["entrypoints"][label] = "present" if (package_dir / rel).exists() else "missing"
                if report["entrypoints"][label] == "missing":
                    report["ok"] = False

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--skip-entrypoint-files",
        action="store_true",
        help="Only inspect imports/signatures; do not check packaged train/eval script files.",
    )
    args = parser.parse_args()
    report = build_report(check_entrypoints=not args.skip_entrypoint_files)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("OpenFlamingo environment check:", "PASS" if report["ok"] else "FAIL")
        for group in ["versions", "imports", "signatures", "entrypoints"]:
            if report.get(group):
                print(f"\n{group}:")
                for key, value in report[group].items():
                    print(f"  {key}: {value}")
        for warning in report.get("warnings", []):
            print(f"warning: {warning}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
