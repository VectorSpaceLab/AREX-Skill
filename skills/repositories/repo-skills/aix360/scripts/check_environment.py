#!/usr/bin/env python3
"""Check AIX360 base and optional module availability without network or model downloads.

Examples:
  python scripts/check_environment.py --group base
  python scripts/check_environment.py --group time-series
  python scripts/check_environment.py --json

The checker reports import/version failures; it does not claim that an
algorithm's numerical workflow, hardware backend, dataset download, or model
training has succeeded.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version

GROUPS = {
    "base": ["aix360", "aix360.metrics", "numpy", "pandas", "sklearn"],
    "local-black-box": [
        "aix360.algorithms.lime.lime_wrapper",
        "aix360.algorithms.shap.shap_wrapper",
        "aix360.algorithms.gce.gce",
        "aix360.algorithms.nncontrastive.nncontrastive",
    ],
    "counterfactual-and-certification": [
        "aix360.algorithms.contrastive.CEM",
        "aix360.algorithms.ecertify.ecertify",
        "aix360.algorithms.glance.base",
        "aix360.algorithms.matching.order_constraints",
    ],
    "interpretable-models": [
        "aix360.algorithms.protodash.PDASH",
        "aix360.algorithms.rbm",
        "aix360.algorithms.rule_induction",
        "aix360.algorithms.imd.imd",
        "aix360.algorithms.ted.TED_Cartesian",
    ],
    "time-series": [
        "aix360.algorithms.tsice.tsice",
        "aix360.algorithms.tslime.tslime",
        "aix360.algorithms.tssaliency.tssaliency",
        "aix360.algorithms.tsutils.tsframe",
    ],
    "datasets-and-metrics": [
        "aix360.metrics.local_metrics",
        "aix360.datasets.heloc_dataset",
        "aix360.datasets.diabetes_dataset",
        "aix360.datasets.sunspots_dataset",
    ],
}


def check_module(name: str) -> dict[str, object]:
    result: dict[str, object] = {"module": name, "ok": False}
    try:
        module = importlib.import_module(name)
        result.update({"ok": True, "file": getattr(module, "__file__", None)})
    except Exception as exc:  # Optional modules fail in many valid installations.
        result.update({"error_type": type(exc).__name__, "error": str(exc)})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--group",
        choices=[*GROUPS, "all"],
        default="base",
        help="module group to import (default: base)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()

    try:
        distribution_version = version("aix360")
    except PackageNotFoundError:
        distribution_version = None

    names = sorted({module for group in GROUPS.values() for module in group})
    if args.group != "all":
        names = GROUPS[args.group]
    checks = [check_module(name) for name in names]
    report = {
        "distribution": "aix360",
        "version": distribution_version,
        "python": sys.version.split()[0],
        "group": args.group,
        "checks": checks,
        "all_passed": all(item["ok"] for item in checks),
        "note": "Imports only; no downloads, credentials, training, or backend execution.",
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"aix360={distribution_version or 'not-installed'} python={report['python']} group={args.group}")
        for item in checks:
            if item["ok"]:
                print(f"OK   {item['module']}")
            else:
                print(f"FAIL {item['module']}: {item['error_type']}: {item['error']}")
        print("result=" + ("PASS" if report["all_passed"] else "INCOMPLETE"))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
