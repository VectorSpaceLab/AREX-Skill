#!/usr/bin/env python3
"""Validate a small JSON description of an Earth2Studio workflow contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.config is None:
        parser.print_help()
        return 0
    data = json.loads(args.config.read_text(encoding="utf-8"))
    errors: list[str] = []
    notes: list[str] = []
    if data.get("workflow", "deterministic") not in {"deterministic", "diagnostic"}:
        errors.append("workflow must be deterministic or diagnostic")
    if not isinstance(data.get("time"), list) or not data["time"]:
        errors.append("time must be a non-empty list")
    nsteps = data.get("nsteps")
    if not isinstance(nsteps, int) or isinstance(nsteps, bool) or nsteps < 0:
        errors.append("nsteps must be a non-negative integer")
    model = data.get("model_input_coords", {})
    model_variables = set(model.get("variable", []))
    source_variables = set(data.get("data_variables", []))
    missing = sorted(model_variables - source_variables) if source_variables else []
    if missing: errors.append("data_variables missing model variables: " + ", ".join(missing))
    model_coords = data.get("model_output_coords", {})
    output = data.get("output_coords", {})
    for key, values in output.items():
        if key in model_coords and not set(values).issubset(set(model_coords[key])):
            errors.append(f"output_coords[{key!r}] contains values outside model output coordinates")
    source_coords = data.get("data_coords", {})
    for key, values in source_coords.items():
        if key in model and set(model[key]) - set(values):
            message = f"source coordinate {key!r} does not cover the model coordinate"
            (errors if args.strict else notes).append(message)
    result = {"ok": not errors, "errors": errors, "notes": notes, "workflow": data.get("workflow", "deterministic"), "nsteps": nsteps, "missing_model_variables": missing, "offline": True}
    if args.json: print(json.dumps(result, sort_keys=True))
    else:
        print("workflow configuration: " + ("PASS" if not errors else "FAIL"))
        for note in notes: print("NOTE:", note)
        for error in errors: print("ERROR:", error)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
