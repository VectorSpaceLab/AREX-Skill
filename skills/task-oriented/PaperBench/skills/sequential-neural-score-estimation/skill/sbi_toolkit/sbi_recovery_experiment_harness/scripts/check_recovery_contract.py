#!/usr/bin/env python3
import argparse
import json
import pathlib

REQUIRED_CHECKS = [
    "prior_sampling_executed",
    "simulator_executed",
    "conditional_posterior_depends_on_x",
    "posterior_samples_drawn",
    "diagnostics_executed",
]


def validate_contract(result, forbidden_path=None, hard_mode=False):
    errors = []
    if hard_mode and result.get("is_proxy"):
        errors.append("hard mode cannot accept proxy recovery")
    checks = result.get("mechanism_checks", {})
    for name in REQUIRED_CHECKS:
        if checks.get(name) is not True:
            errors.append(f"missing mechanism check: {name}")
    if forbidden_path:
        forbidden = str(pathlib.Path(forbidden_path).resolve())
        for path in result.get("source_paths_read", []):
            if str(pathlib.Path(path).resolve()).startswith(forbidden):
                errors.append(f"forbidden source path was read: {path}")
    metric = result.get("metrics", {}).get("posterior_mean_abs_error")
    if metric is None or metric > result.get("acceptance_thresholds", {}).get("max_posterior_mean_abs_error", 0.5):
        errors.append("posterior mean error missing or above threshold")
    return {"ok": not errors, "errors": errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-json", required=True)
    parser.add_argument("--forbidden-path")
    parser.add_argument("--hard-mode", action="store_true")
    args = parser.parse_args()
    with open(args.result_json, "r", encoding="utf-8") as handle:
        result = json.load(handle)
    print(json.dumps(validate_contract(result, args.forbidden_path, args.hard_mode), indent=2))


if __name__ == "__main__":
    main()
