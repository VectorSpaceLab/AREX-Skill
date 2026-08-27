#!/usr/bin/env python3
"""Read-only schema checks for BindCraft target, filter, and advanced JSON files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TARGET_KEYS = {
    "design_path", "binder_name", "starting_pdb", "chains",
    "target_hotspot_residues", "lengths", "number_of_final_designs",
}
ADVANCED_KEYS = {
    "design_algorithm", "use_multimer_design", "num_recycles_design",
    "num_recycles_validation", "af_params_dir", "dssp_path", "dalphaball_path",
    "enable_mpnn", "max_trajectories", "acceptance_rate",
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", type=Path)
    p.add_argument("--filters", type=Path)
    p.add_argument("--advanced", type=Path)
    return p


def load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def check_target(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["target root must be an object"]
    missing = sorted(TARGET_KEYS - data.keys())
    errors = [f"target missing keys: {', '.join(missing)}"] if missing else []
    if "lengths" in data and (not isinstance(data["lengths"], list) or len(data["lengths"]) != 2):
        errors.append("target lengths must be a two-element array")
    return errors


def check_filters(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["filters root must be an object"]
    errors: list[str] = []
    for name, condition in data.items():
        if not isinstance(condition, dict):
            errors.append(f"filter {name!r} must be an object")
            continue
        # InterfaceAAs filters are one level deeper: amino-acid -> condition.
        if "threshold" not in condition and "higher" not in condition:
            for residue, nested in condition.items():
                if not isinstance(nested, dict) or "threshold" not in nested or "higher" not in nested:
                    errors.append(f"filter {name!r}.{residue!r} needs threshold and higher")
                elif not isinstance(nested["higher"], bool):
                    errors.append(f"filter {name!r}.{residue!r}.higher must be boolean")
            continue
        if "threshold" not in condition or "higher" not in condition:
            errors.append(f"filter {name!r} needs threshold and higher")
        elif not isinstance(condition["higher"], bool):
            errors.append(f"filter {name!r}.higher must be boolean")
    return errors


def check_advanced(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["advanced root must be an object"]
    missing = sorted(ADVANCED_KEYS - data.keys())
    # Some historical/custom presets may omit path or monitoring keys; report
    # them as warnings at the caller rather than treating every preset as invalid.
    return [f"advanced missing expected keys: {', '.join(missing)}"] if missing else []


def main() -> int:
    args = parser().parse_args()
    selected = [("target", args.target, check_target), ("filters", args.filters, check_filters), ("advanced", args.advanced, check_advanced)]
    if not any(path for _, path, _ in selected):
        parser().error("supply at least one of --target, --filters, or --advanced")
    errors = 0
    for label, path, checker in selected:
        if path is None:
            continue
        try:
            problems = checker(load(path))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"{label}: ERROR {exc}")
            errors += 1
            continue
        if problems:
            prefix = "WARNING" if label == "advanced" else "ERROR"
            print(f"{label}: {prefix}: {'; '.join(problems)}")
            if prefix == "ERROR":
                errors += 1
        else:
            print(f"{label}: OK ({path})")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
