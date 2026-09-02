#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _numeric_vector(values: Any) -> bool:
    return isinstance(values, list) and all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in values)


def load_reference_summary(summary_path: str | Path, reference_info_path: str | Path | None = None, statistic: str = "mean_value") -> dict[str, Any]:
    summary = _load(Path(summary_path))
    names = summary.get("names") or summary.get("name") or []
    values = summary.get(statistic)
    blockers: list[str] = []
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        blockers.append("names must be a list of strings")
        names = []
    if not _numeric_vector(values):
        blockers.append(f"{statistic} must be a finite numeric vector")
        values = []
    if names and values and len(names) != len(values):
        blockers.append("names and statistic vector lengths differ")

    mcse_values = summary.get(f"mcse_{statistic}") or summary.get("mcse_mean") or summary.get("mcse")
    mcse: dict[str, float] = {}
    mcse_available = False
    if _numeric_vector(mcse_values) and len(mcse_values) == len(names):
        mcse = {name: float(value) for name, value in zip(names, mcse_values)}
        mcse_available = True

    info: dict[str, Any] = {}
    if reference_info_path:
        info_path = Path(reference_info_path)
        if info_path.exists():
            info = _load(info_path)
        else:
            blockers.append(f"reference info path missing: {info_path}")

    diagnostics_present = any(key.lower() in {"rhat", "r_hat", "efmi", "e_fmi", "divergences", "diagnostics"} for key in info)
    values_map = {name: float(value) for name, value in zip(names, values)} if not blockers else {}
    return {
        "valid": not blockers,
        "statistic": statistic,
        "values": values_map,
        "mcse": mcse,
        "quality_flags": {
            "finite_values": bool(values_map),
            "mcse_available": mcse_available,
            "reference_info_available": bool(info),
            "diagnostics_present": diagnostics_present,
        },
        "blockers": blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    parser.add_argument("--reference-info", default="")
    parser.add_argument("--statistic", default="mean_value")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = load_reference_summary(args.summary, args.reference_info or None, args.statistic)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
