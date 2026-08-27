#!/usr/bin/env python3
"""Safely summarize Megatron-LM recipe YAML scope coverage.

The script is read-only: it opens YAML files, counts recipe scope/platform/
environment/test-case entries, and prints a compact summary. It does not import
repo-local CI helpers and does not mutate recipe files.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised only in minimal envs.
    raise SystemExit(
        "PyYAML is required for this script. Install a YAML parser in the current "
        "environment, then rerun."
    ) from exc

KNOWN_PLATFORMS = {
    "dgx_a100",
    "dgx_h100",
    "dgx_gb200",
    "cpu_eos",
    "cpu_coreweave",
    "cpu_dracooci",
    "cpu_oci-hsg",
    "ghci",
}

LEGACY_SCOPE_ALIASES = {
    "mr-github-slim": "L0",
    "mr-github": "L1",
    "nightly": "L2",
    "weekly": "L3",
}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _safe_load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"top-level document is {type(data).__name__}, expected mapping")
    return data


def _product_size(values: dict[str, Any]) -> int:
    size = 1
    for key, value in values.items():
        if key == "cadence":
            # Cadence is a list-valued selector, not a cartesian dimension in
            # Megatron-LM's recipe parser.
            continue
        choices = _as_list(value)
        size *= max(1, len(choices))
    return size


def _iter_recipe_paths(inputs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for item in inputs:
        if item.is_dir():
            paths.extend(sorted(item.rglob("*.yaml")))
            paths.extend(sorted(item.rglob("*.yml")))
        elif item.is_file():
            paths.append(item)
        else:
            raise FileNotFoundError(item)
    return sorted(set(paths))


def summarize(paths: list[Path]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "files": 0,
        "recipe_files": [],
        "test_case_groups": 0,
        "inner_product_rows": 0,
        "approx_expanded_rows": 0,
        "scope_counts": collections.Counter(),
        "scope_alias_counts": collections.Counter(),
        "environment_counts": collections.Counter(),
        "platform_counts": collections.Counter(),
        "cadence_counts": collections.Counter(),
        "model_counts": collections.Counter(),
        "broken_or_disabled_scopes": collections.Counter(),
        "missing_scope_rows": [],
        "unknown_platform_rows": [],
        "errors": [],
    }

    for path in paths:
        summary["files"] += 1
        summary["recipe_files"].append(path.as_posix())
        try:
            doc = _safe_load(path)
        except Exception as exc:  # noqa: BLE001 - report all malformed files.
            summary["errors"].append({"file": path.as_posix(), "error": str(exc)})
            continue

        spec = doc.get("spec") or {}
        if isinstance(spec, dict) and spec.get("model"):
            summary["model_counts"][str(spec["model"])] += 1

        for product in _as_list(doc.get("products")):
            if not isinstance(product, dict):
                continue
            test_cases = [str(v) for v in _as_list(product.get("test_case"))]
            summary["test_case_groups"] += len(test_cases)
            for inner in _as_list(product.get("products")):
                if not isinstance(inner, dict):
                    continue
                summary["inner_product_rows"] += 1
                expanded = _product_size(inner)
                summary["approx_expanded_rows"] += expanded

                scopes = [str(v) for v in _as_list(inner.get("scope"))]
                if not scopes:
                    summary["missing_scope_rows"].append(
                        {"file": path.as_posix(), "test_case": test_cases}
                    )
                for scope in scopes:
                    summary["scope_counts"][scope] += expanded
                    alias = LEGACY_SCOPE_ALIASES.get(scope, scope)
                    summary["scope_alias_counts"][alias] += expanded
                    if "broken" in scope or "disabled" in scope:
                        summary["broken_or_disabled_scopes"][scope] += expanded

                for env in [str(v) for v in _as_list(inner.get("environment"))]:
                    summary["environment_counts"][env] += expanded

                for platform in [str(v) for v in _as_list(inner.get("platforms"))]:
                    summary["platform_counts"][platform] += expanded
                    if platform not in KNOWN_PLATFORMS:
                        summary["unknown_platform_rows"].append(
                            {"file": path.as_posix(), "test_case": test_cases, "platform": platform}
                        )

                for cadence in [str(v) for v in _as_list(inner.get("cadence"))]:
                    summary["cadence_counts"][cadence] += expanded

    for key, value in list(summary.items()):
        if isinstance(value, collections.Counter):
            summary[key] = dict(sorted(value.items(), key=lambda item: (-item[1], item[0])))
    return summary


def _print_counter(title: str, data: dict[str, int], limit: int) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    if not data:
        print("(none)")
        return
    width = max(len(key) for key in data)
    for idx, (key, value) in enumerate(data.items()):
        if idx >= limit:
            print(f"... {len(data) - limit} more")
            break
        print(f"{key:<{width}}  {value}")


def print_text(summary: dict[str, Any], limit: int) -> None:
    print("Megatron-LM recipe scope summary")
    print("================================")
    print(f"Files scanned:            {summary['files']}")
    print(f"Test-case groups:         {summary['test_case_groups']}")
    print(f"Inner product rows:       {summary['inner_product_rows']}")
    print(f"Approx. expanded rows:    {summary['approx_expanded_rows']}")

    _print_counter("Scopes", summary["scope_counts"], limit)
    _print_counter("Scopes after common aliases", summary["scope_alias_counts"], limit)
    _print_counter("Environments", summary["environment_counts"], limit)
    _print_counter("Platforms", summary["platform_counts"], limit)
    _print_counter("Explicit cadences", summary["cadence_counts"], limit)
    _print_counter("Broken/disabled scopes", summary["broken_or_disabled_scopes"], limit)

    if summary["missing_scope_rows"]:
        print("\nRows missing scope")
        print("------------------")
        for row in summary["missing_scope_rows"][:limit]:
            print(f"{row['file']}: {', '.join(row['test_case'])}")
        if len(summary["missing_scope_rows"]) > limit:
            print(f"... {len(summary['missing_scope_rows']) - limit} more")

    if summary["unknown_platform_rows"]:
        print("\nUnknown platform rows")
        print("---------------------")
        for row in summary["unknown_platform_rows"][:limit]:
            print(f"{row['file']}: {row['platform']} ({', '.join(row['test_case'])})")
        if len(summary["unknown_platform_rows"]) > limit:
            print(f"... {len(summary['unknown_platform_rows']) - limit} more")

    if summary["errors"]:
        print("\nErrors")
        print("------")
        for row in summary["errors"][:limit]:
            print(f"{row['file']}: {row['error']}")
        if len(summary["errors"]) > limit:
            print(f"... {len(summary['errors']) - limit} more")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("tests/test_utils/recipes")],
        help="Recipe YAML files or directories to scan (default: tests/test_utils/recipes).",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--limit", type=int, default=30, help="Rows to print per section.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    paths = _iter_recipe_paths(args.paths)
    summary = summarize(paths)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary, max(1, args.limit))
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
