#!/usr/bin/env python3
"""Inspect OpenFE protocol default settings without running simulations."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROTOCOL_ALIASES = {
    "rbfe": "RelativeHybridTopologyProtocol",
    "rfe": "RelativeHybridTopologyProtocol",
    "relative-hybrid-topology": "RelativeHybridTopologyProtocol",
    "abfe": "AbsoluteBindingProtocol",
    "absolute-binding": "AbsoluteBindingProtocol",
    "ahfe": "AbsoluteSolvationProtocol",
    "absolute-solvation": "AbsoluteSolvationProtocol",
    "solvation": "AbsoluteSolvationProtocol",
    "septop": "SepTopProtocol",
    "separated-topologies": "SepTopProtocol",
    "plain-md": "PlainMDProtocol",
    "md": "PlainMDProtocol",
}

CLASS_IMPORTS = {
    "RelativeHybridTopologyProtocol": ("openfe.protocols.openmm_rfe", "RelativeHybridTopologyProtocol"),
    "AbsoluteBindingProtocol": ("openfe.protocols.openmm_afe", "AbsoluteBindingProtocol"),
    "AbsoluteSolvationProtocol": ("openfe.protocols.openmm_afe", "AbsoluteSolvationProtocol"),
    "SepTopProtocol": ("openfe.protocols.openmm_septop", "SepTopProtocol"),
    "PlainMDProtocol": ("openfe.protocols.openmm_md", "PlainMDProtocol"),
}

DEFAULT_FIELDS = (
    "protocol_repeats",
    "engine_settings",
    "simulation_settings",
    "solvent_simulation_settings",
    "complex_simulation_settings",
    "vacuum_simulation_settings",
    "lambda_settings",
    "solvent_lambda_settings",
    "complex_lambda_settings",
    "alchemical_settings",
    "partial_charge_settings",
    "output_settings",
    "solvent_output_settings",
    "complex_output_settings",
    "vacuum_output_settings",
)


def import_protocol_class(class_name: str):
    module_name, attr_name = CLASS_IMPORTS[class_name]
    module = __import__(module_name, fromlist=[attr_name])
    return getattr(module, attr_name)


def to_plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return to_plain(value.model_dump())
    if isinstance(value, Mapping):
        return {str(key): to_plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [to_plain(item) for item in value]
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, set):
        return sorted(to_plain(item) for item in value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def select_fields(settings_data: Mapping[str, Any], fields: Sequence[str] | None) -> dict[str, Any]:
    if not fields:
        return dict(settings_data)
    selected: dict[str, Any] = {}
    for field in fields:
        if field in settings_data:
            selected[field] = settings_data[field]
    return selected


def dependency_hint(exc: Exception, class_name: str) -> str | None:
    message = str(exc)
    if isinstance(exc, ModuleNotFoundError):
        missing_name = getattr(exc, "name", "")
        if not missing_name and "'" in message:
            missing_name = message.split("'")[1]
        if missing_name == "openfe_analysis":
            return "SepTop requires an OpenFE environment with openfe-analysis>=0.5.0."
        if missing_name:
            return f"Activate an OpenFE environment that includes the missing dependency: {missing_name}."
        if class_name == "SepTopProtocol":
            return "SepTop requires an OpenFE environment with openfe-analysis>=0.5.0."
    return None


def inspect_one(alias: str, fields: Sequence[str] | None) -> dict[str, Any]:
    class_name = PROTOCOL_ALIASES[alias]
    try:
        protocol_cls = import_protocol_class(class_name)
        settings = protocol_cls.default_settings()
    except Exception as exc:  # pragma: no cover - import/runtime environment boundary
        result = {
            "alias": alias,
            "class": class_name,
            "error": f"{type(exc).__name__}: {exc}",
        }
        hint = dependency_hint(exc, class_name)
        if hint:
            result["hint"] = hint
        return result

    settings_data = to_plain(settings)
    return {
        "alias": alias,
        "class": class_name,
        "settings_type": type(settings).__name__,
        "settings": select_fields(settings_data, fields),
    }


def summarize_value(value: Any) -> str:
    if isinstance(value, Mapping):
        parts = []
        for key in DEFAULT_FIELDS:
            if key in value:
                parts.append(f"{key}={summarize_value(value[key])}")
        if parts:
            return "; ".join(parts)
        keys = list(value)[:6]
        suffix = "..." if len(value) > 6 else ""
        return "{" + ", ".join(map(str, keys)) + suffix + "}"
    if isinstance(value, list):
        if len(value) > 8:
            return f"list(len={len(value)}, first={value[:3]}, last={value[-3:]})"
        return repr(value)
    return str(value)


def format_summary(results: Sequence[Mapping[str, Any]]) -> str:
    lines: list[str] = []
    for result in results:
        if "error" in result:
            lines.append(f"{result['alias']}: {result['class']} failed")
            lines.append(f"  error: {result['error']}")
            if "hint" in result:
                lines.append(f"  hint: {result['hint']}")
            continue
        lines.append(f"{result['alias']}: {result['class']} ({result['settings_type']})")
        settings = result["settings"]
        if not settings:
            lines.append("  no selected fields found")
            continue
        for key, value in settings.items():
            lines.append(f"  {key}: {summarize_value(value)}")
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print OpenFE protocol default settings safely. This helper imports protocol "
            "classes and calls default_settings(); it does not create systems, run OpenMM, "
            "submit jobs, download data, or mutate external state."
        )
    )
    parser.add_argument(
        "protocol",
        choices=["all", *sorted(PROTOCOL_ALIASES)],
        help="Protocol alias to inspect, or 'all' for canonical aliases.",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Output format. Default: summary.",
    )
    parser.add_argument(
        "--fields",
        nargs="+",
        help="Optional top-level settings fields to include, such as protocol_repeats engine_settings simulation_settings.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file path for output. Parent directory must already exist.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    aliases = ["rbfe", "abfe", "ahfe", "septop", "plain-md"] if args.protocol == "all" else [args.protocol]

    results = [inspect_one(alias, args.fields) for alias in aliases]

    if args.format == "json":
        payload: Any = results[0] if len(results) == 1 else results
        text = json.dumps(payload, indent=2, sort_keys=True)
    else:
        text = format_summary(results)

    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)

    return 1 if all("error" in result for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
