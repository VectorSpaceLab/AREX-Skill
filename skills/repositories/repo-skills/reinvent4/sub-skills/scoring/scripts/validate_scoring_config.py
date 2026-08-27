#!/usr/bin/env python3
"""Summarize REINVENT4 scoring config structure without running scoring.

The script parses TOML (or JSON/YAML when PyYAML is installed for YAML), finds
``[scoring]`` and ``[stage.scoring]`` blocks, and reports components,
endpoints, transforms, weights, and likely structural issues. It does not call
REINVENT, score molecules, import scoring plugins, or contact external services.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tomllib
from typing import Any


KNOWN_AGGREGATORS = {"geometric_mean", "custom_product", "arithmetic_mean", "custom_sum"}
KNOWN_TRANSFORMS = {
    "sigmoid",
    "reverse_sigmoid",
    "double_sigmoid",
    "right_step",
    "left_step",
    "step",
    "exponential_decay",
    "value_mapping",
}
COMMON_FILTERS = {"customalerts", "custom_alerts", "reactionfilter", "reaction_filter"}
COMMON_PENALTIES = {"matchingsubstructure", "matching_substructure"}


def clean_name(name: str) -> str:
    return name.lower().replace("-", "").replace("_", "")


def load_config(path: pathlib.Path, fmt: str | None) -> dict[str, Any]:
    suffix = path.suffix.lower().lstrip(".")
    config_format = (fmt or suffix or "toml").lower()
    if config_format == "toml":
        with path.open("rb") as file_handle:
            return tomllib.load(file_handle)
    if config_format == "json":
        with path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    if config_format in {"yaml", "yml"}:
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("YAML parsing requires PyYAML in this environment") from exc
        with path.open("r", encoding="utf-8") as file_handle:
            loaded = yaml.safe_load(file_handle)
            return loaded or {}
    raise ValueError(f"Unsupported config format: {config_format}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse and summarize REINVENT4 scoring blocks without executing scoring."
    )
    parser.add_argument("config", type=pathlib.Path, help="Path to a TOML, JSON, or YAML config.")
    parser.add_argument(
        "--config-format",
        choices=["toml", "json", "yaml", "yml"],
        help="Override config format detection from file suffix.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--show-params",
        action="store_true",
        help="Include endpoint and component parameter keys in text output.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when warnings are found.",
    )
    return parser.parse_args()


def find_scoring_blocks(data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    blocks: list[tuple[str, dict[str, Any]]] = []
    scoring = data.get("scoring")
    if isinstance(scoring, dict):
        blocks.append(("scoring", scoring))

    stages = data.get("stage")
    if isinstance(stages, list):
        for index, stage in enumerate(stages, start=1):
            if isinstance(stage, dict) and isinstance(stage.get("scoring"), dict):
                blocks.append((f"stage[{index}].scoring", stage["scoring"]))
    elif isinstance(stages, dict) and isinstance(stages.get("scoring"), dict):
        blocks.append(("stage.scoring", stages["scoring"]))

    if isinstance(data.get("component"), list):
        blocks.append(("component_fragment", {"component": data["component"]}))

    return blocks


def component_items(component_entry: Any) -> tuple[str | None, dict[str, Any] | None, list[str]]:
    warnings: list[str] = []
    if not isinstance(component_entry, dict):
        return None, None, ["component entry is not a table"]

    keys = list(component_entry.keys())
    if len(keys) != 1:
        warnings.append(f"component entry should contain exactly one component key, found {keys}")
    if not keys:
        return None, None, warnings

    name = keys[0]
    value = component_entry[name]
    if not isinstance(value, dict):
        return name, None, warnings + [f"component {name} body is not a table"]
    return name, value, warnings


def summarize_block(label: str, block: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    aggregation = block.get("type")
    if label != "component_fragment":
        if not aggregation:
            warnings.append(f"{label}: missing aggregation type")
        elif str(aggregation) not in KNOWN_AGGREGATORS:
            warnings.append(f"{label}: unusual aggregation type {aggregation!r}")

    parallel = block.get("parallel")
    if parallel is not None:
        if not isinstance(parallel, int) or not (1 <= parallel <= 40):
            warnings.append(f"{label}: parallel should be an integer from 1 to 40")

    component_entries = block.get("component")
    component_source = block.get("filename")
    if not isinstance(component_entries, list) or not component_entries:
        if component_source:
            component_entries = []
        else:
            warnings.append(f"{label}: no component list found")
            component_entries = []

    components: list[dict[str, Any]] = []
    for index, entry in enumerate(component_entries, start=1):
        component_name, component_body, item_warnings = component_items(entry)
        warnings.extend(f"{label}.component[{index}]: {warning}" for warning in item_warnings)
        if component_name is None or component_body is None:
            continue

        endpoints = component_body.get("endpoint")
        if not isinstance(endpoints, list) or not endpoints:
            warnings.append(f"{label}.{component_name}: missing endpoint list")
            endpoints = []

        component_params = component_body.get("params", {})
        if component_params is not None and not isinstance(component_params, dict):
            warnings.append(f"{label}.{component_name}: component-level params should be a table")
            component_params = {}

        endpoint_summaries: list[dict[str, Any]] = []
        for endpoint_index, endpoint in enumerate(endpoints, start=1):
            if not isinstance(endpoint, dict):
                warnings.append(f"{label}.{component_name}.endpoint[{endpoint_index}]: endpoint is not a table")
                continue
            name = endpoint.get("name", component_name)
            weight = endpoint.get("weight", 1.0)
            if not isinstance(weight, (int, float)):
                warnings.append(f"{label}.{component_name}.{name}: weight is not numeric")
            elif weight < 0:
                warnings.append(f"{label}.{component_name}.{name}: weight must be non-negative")

            transform = endpoint.get("transform")
            transform_type = None
            transform_keys: list[str] = []
            if transform is not None:
                if not isinstance(transform, dict):
                    warnings.append(f"{label}.{component_name}.{name}: transform should be a table")
                else:
                    transform_type = transform.get("type")
                    transform_keys = sorted(str(key) for key in transform.keys())
                    clean_transform = clean_name(str(transform_type)) if transform_type else ""
                    clean_known = {clean_name(item) for item in KNOWN_TRANSFORMS}
                    if not transform_type:
                        warnings.append(f"{label}.{component_name}.{name}: transform missing type")
                    elif clean_transform not in clean_known:
                        warnings.append(
                            f"{label}.{component_name}.{name}: unusual transform type {transform_type!r}"
                        )

            endpoint_params = endpoint.get("params", {})
            if endpoint_params is not None and not isinstance(endpoint_params, dict):
                warnings.append(f"{label}.{component_name}.{name}: params should be a table")
                endpoint_params = {}

            endpoint_summaries.append(
                {
                    "name": name,
                    "weight": weight,
                    "params": sorted(str(key) for key in endpoint_params.keys()),
                    "transform": transform_type,
                    "transform_keys": transform_keys,
                }
            )

        role_hint = "scorer"
        cleaned = clean_name(component_name)
        if cleaned in {clean_name(item) for item in COMMON_FILTERS}:
            role_hint = "filter"
        elif cleaned in {clean_name(item) for item in COMMON_PENALTIES}:
            role_hint = "penalty"

        components.append(
            {
                "index": index,
                "name": component_name,
                "lookup_key": cleaned,
                "role_hint": role_hint,
                "component_params": sorted(str(key) for key in component_params.keys()),
                "endpoints": endpoint_summaries,
            }
        )

    return {
        "label": label,
        "aggregation": aggregation,
        "parallel": parallel,
        "use_pumas": block.get("use_pumas", False),
        "component_source": component_source,
        "component_filetype": block.get("filetype"),
        "component_count": len(components),
        "endpoint_count": sum(len(component["endpoints"]) for component in components),
        "components": components,
        "warnings": warnings,
    }


def print_text(payload: dict[str, Any], show_params: bool) -> None:
    print(f"Config: {payload['config']}")
    print(f"run_type: {payload.get('run_type')!r}")
    if not payload["blocks"]:
        print("No scoring blocks found.")
    for block in payload["blocks"]:
        print()
        print(f"[{block['label']}]")
        print(f"  aggregation: {block['aggregation']!r}")
        print(f"  parallel: {block['parallel']!r}")
        print(f"  use_pumas: {block['use_pumas']!r}")
        if block.get("component_source"):
            print(
                f"  component_source: {block['component_source']!r} "
                f"filetype={block.get('component_filetype')!r}"
            )
        print(f"  components: {block['component_count']}; endpoints: {block['endpoint_count']}")
        for component in block["components"]:
            params = f" params={component['component_params']}" if show_params else ""
            print(
                f"  - {component['name']} "
                f"lookup={component['lookup_key']} "
                f"role_hint={component['role_hint']} "
                f"endpoints={len(component['endpoints'])}{params}"
            )
            for endpoint in component["endpoints"]:
                transform = endpoint["transform"] or "none"
                extra = ""
                if show_params:
                    extra = f" params={endpoint['params']} transform_keys={endpoint['transform_keys']}"
                print(
                    f"      endpoint {endpoint['name']!r} "
                    f"weight={endpoint['weight']!r} transform={transform!r}{extra}"
                )
    warnings = payload["warnings"]
    print()
    print(f"Warnings: {len(warnings)}")
    for warning in warnings:
        print(f"  - {warning}")


def main() -> int:
    args = parse_args()
    try:
        data = load_config(args.config, args.config_format)
    except Exception as exc:
        print(f"Failed to parse config: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("Top-level config must be a table/object", file=sys.stderr)
        return 2

    blocks = [summarize_block(label, block) for label, block in find_scoring_blocks(data)]
    warnings = [warning for block in blocks for warning in block["warnings"]]

    run_type = data.get("run_type")
    if run_type is not None and run_type != "scoring" and any(b["label"] == "scoring" for b in blocks):
        warnings.append(
            f"top-level run_type is {run_type!r}; standalone scoring configs should use 'scoring'"
        )

    payload = {
        "config": str(args.config),
        "run_type": run_type,
        "blocks": blocks,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(payload, args.show_params)

    if warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
