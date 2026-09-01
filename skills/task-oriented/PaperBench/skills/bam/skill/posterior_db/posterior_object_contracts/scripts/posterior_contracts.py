#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _first(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _dimension_total(dimensions: Any) -> int:
    if isinstance(dimensions, dict):
        total = 0
        for value in dimensions.values():
            if isinstance(value, list):
                product = 1
                for item in value:
                    product *= int(item)
                total += product
            elif isinstance(value, (int, float)):
                total += int(value)
        return total
    if isinstance(dimensions, list):
        return sum(int(item) for item in dimensions if isinstance(item, (int, float)))
    if isinstance(dimensions, (int, float)):
        return int(dimensions)
    return 0


def normalize_contract(database_root: str | Path, posterior_name: str) -> dict[str, Any]:
    root = Path(database_root)
    posterior_path = root / "posteriors" / f"{posterior_name}.json"
    errors: list[str] = []
    if not posterior_path.exists():
        return {"valid": False, "posterior_name": posterior_name, "errors": [f"missing posterior file: {posterior_path}"]}

    posterior = _load_json(posterior_path)
    model_name = _first(posterior, "model_name", "model")
    data_name = _first(posterior, "data_name", "data")
    reference_name = _first(posterior, "reference_posterior_name", "reference_posterior")
    dimensions = _first(posterior, "dimensions", "dimension") or {}

    if not model_name:
        errors.append("missing model_name")
    if not data_name:
        errors.append("missing data_name")

    linked_paths: dict[str, str] = {"posterior": str(posterior_path)}
    expected = []
    if model_name:
        expected.append(("model_info", root / "models" / "info" / f"{model_name}.info.json"))
    if data_name:
        expected.append(("data_info", root / "data" / "info" / f"{data_name}.info.json"))
    if reference_name:
        expected.append(("reference_info", root / "reference_posteriors" / "info" / f"{reference_name}.info.json"))

    for label, path in expected:
        if label == "reference_info" and not path.exists():
            summary_info = root / "reference_posteriors" / "summary_statistics" / "mean_value" / "info" / f"{reference_name}.info.json"
            if summary_info.exists():
                linked_paths[label] = str(summary_info)
                linked_paths["reference_info_kind"] = "summary_statistics_mean_value"
                continue
        linked_paths[label] = str(path)
        if not path.exists():
            errors.append(f"missing {label}: {path}")

    return {
        "valid": not errors,
        "name": posterior.get("name", posterior_name),
        "posterior_name": posterior_name,
        "model_name": model_name,
        "data_name": data_name,
        "reference_posterior_name": reference_name,
        "dimensions": dimensions,
        "total_dimension": _dimension_total(dimensions),
        "keywords": posterior.get("keywords", []),
        "linked_paths": linked_paths,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-root", required=True)
    parser.add_argument("--posterior", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = normalize_contract(args.database_root, args.posterior)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
