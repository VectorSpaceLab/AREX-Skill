#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def validate_protocol(protocol: dict) -> dict:
    errors = []
    warnings = []
    required = ["dataset", "split", "metric", "paper_value", "mode"]
    for field in required:
        if field not in protocol:
            errors.append(f"missing {field}")
    mode = protocol.get("mode")
    if mode in {"full", "reduced"} and protocol.get("classifier_scale") is None:
        errors.append("guided full or reduced protocol requires classifier_scale")
    if mode == "proxy":
        if protocol.get("proxy") is not True:
            errors.append("proxy mode requires proxy true")
        if not protocol.get("rationale"):
            errors.append("proxy mode requires rationale")
        if not protocol.get("mechanism_checks_expected"):
            errors.append("proxy mode requires expected mechanism checks")
    if protocol.get("upsampling") and protocol.get("resolution") is None:
        warnings.append("upsampling protocol should record output resolution")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "protocol": protocol}


def example_protocol(mode: str) -> dict:
    if mode == "proxy":
        return {
            "dataset": "synthetic_two_class_gaussian_diffusion",
            "split": "single_seed_proxy",
            "metric": "guided_distance_improvement",
            "paper_value": 0.0,
            "mode": "proxy",
            "proxy": True,
            "classifier_scale": 1.5,
            "rationale": "Scalar Gaussian proxy preserves classifier-gradient guidance while full FID recovery is blocked.",
            "mechanism_checks_expected": ["classifier_gradient_computed", "guided_distance_improved"],
        }
    if mode == "full_missing_scale":
        return {
            "dataset": "ImageNet",
            "split": "validation-like samples",
            "metric": "FID",
            "paper_value": 4.59,
            "mode": "full",
            "proxy": False,
            "resolution": 256,
        }
    raise ValueError(f"unknown mode: {mode}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["proxy", "full_missing_scale"], required=True)
    args = parser.parse_args()
    print(json.dumps(validate_protocol(example_protocol(args.mode)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
