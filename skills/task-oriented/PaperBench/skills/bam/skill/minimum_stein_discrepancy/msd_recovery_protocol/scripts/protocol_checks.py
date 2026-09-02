#!/usr/bin/env python3
"""Small validation helpers for MSD recovery protocol artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def source_manifest_has_no_original_repo(manifest: dict[str, object]) -> bool:
    forbidden = str(manifest.get("original_repo_path", "")).strip()
    if forbidden:
        return False
    for item in manifest.get("sources", []):
        if isinstance(item, dict) and item.get("kind") == "original_repo":
            return False
    return True


def mechanism_checks_complete(checks: dict[str, object]) -> bool:
    required = [
        "score_only_model_used",
        "stein_kernel_u_statistic_executed",
        "diffusion_factor_validated",
        "minimum_discrepancy_optimized",
        "reduced_training_executed",
        "optimizer_step_executed",
    ]
    return all(checks.get(key) is True for key in required)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("result")
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    result = json.loads(Path(args.result).read_text(encoding="utf-8"))
    report = {
        "source_boundary_ok": source_manifest_has_no_original_repo(manifest),
        "mechanism_checks_ok": mechanism_checks_complete(result.get("mechanism_checks", {})),
    }
    print(json.dumps(report, indent=2))
    return 0 if all(report.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
