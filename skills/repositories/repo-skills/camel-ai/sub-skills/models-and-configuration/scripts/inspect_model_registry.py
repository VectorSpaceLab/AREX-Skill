#!/usr/bin/env python3
"""Inspect CAMEL model registry metadata without provider calls."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib import metadata
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class BackendRecord:
    platform_name: str
    platform_value: str
    backend_class: str
    backend_module: str
    import_ok: bool
    error: str | None = None


@dataclass
class ConfigRecord:
    name: str
    fields: list[str]
    params_constant: str | None
    params: list[str]


def _safe_import_camel() -> tuple[Any, list[str]]:
    warnings: list[str] = []
    try:
        import camel  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise SystemExit(f"Unable to import camel: {exc}") from exc
    return camel, warnings


def _collect_backends() -> tuple[list[BackendRecord], list[str]]:
    warnings: list[str] = []
    try:
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType
    except Exception as exc:  # pragma: no cover - depends on optional deps
        raise SystemExit(f"Unable to import CAMEL model registry: {exc}") from exc

    records: list[BackendRecord] = []
    platform_map = getattr(ModelFactory, "_MODEL_PLATFORM_TO_CLASS_MAP", {})
    for platform in ModelPlatformType:
        backend_class = platform_map.get(platform)
        if backend_class is None:
            records.append(
                BackendRecord(
                    platform_name=platform.name,
                    platform_value=str(platform.value),
                    backend_class="<not factory-mapped>",
                    backend_module="",
                    import_ok=False,
                    error="No entry in ModelFactory._MODEL_PLATFORM_TO_CLASS_MAP",
                )
            )
            continue
        records.append(
            BackendRecord(
                platform_name=platform.name,
                platform_value=str(platform.value),
                backend_class=getattr(backend_class, "__name__", str(backend_class)),
                backend_module=getattr(backend_class, "__module__", ""),
                import_ok=True,
            )
        )
    return records, warnings


def _collect_model_types() -> dict[str, Any]:
    from camel.types import ModelType

    values = [str(member.value) for member in ModelType]
    return {
        "count": len(values),
        "default": str(ModelType.DEFAULT.value),
        "first_values": values[:25],
        "last_values": values[-25:],
    }


def _collect_configs() -> list[ConfigRecord]:
    configs_module = importlib.import_module("camel.configs")
    records: list[ConfigRecord] = []
    exported = getattr(configs_module, "__all__", [])
    constants = {
        name: getattr(configs_module, name)
        for name in exported
        if name.endswith("_API_PARAMS") and hasattr(configs_module, name)
    }
    for name in exported:
        obj = getattr(configs_module, name, None)
        if not inspect.isclass(obj):
            continue
        fields = sorted(getattr(obj, "model_fields", {}).keys())
        if not fields:
            continue
        params_constant = None
        params: list[str] = []
        for const_name, const_values in constants.items():
            try:
                const_as_list = sorted(str(value) for value in const_values)
            except TypeError:
                continue
            if const_as_list == fields:
                params_constant = const_name
                params = const_as_list
                break
        records.append(
            ConfigRecord(
                name=name,
                fields=fields,
                params_constant=params_constant,
                params=params or fields,
            )
        )
    return sorted(records, key=lambda record: record.name.lower())


def collect_registry() -> dict[str, Any]:
    camel, import_warnings = _safe_import_camel()
    backend_records, backend_warnings = _collect_backends()
    try:
        version = metadata.version("camel-ai")
    except Exception:
        version = getattr(camel, "__version__", "unknown")

    return {
        "distribution": "camel-ai",
        "version": version,
        "backend_platforms": [asdict(record) for record in backend_records],
        "model_types": _collect_model_types(),
        "config_classes": [asdict(record) for record in _collect_configs()],
        "warnings": import_warnings + backend_warnings,
    }


def print_text(registry: dict[str, Any]) -> None:
    print(f"camel-ai version: {registry['version']}")
    print("\nFactory-backed platforms:")
    for record in registry["backend_platforms"]:
        status = "ok" if record["import_ok"] else "missing"
        print(
            f"- {record['platform_name']} ({record['platform_value']}): "
            f"{record['backend_class']} [{status}]"
        )
        if record.get("error"):
            print(f"  error: {record['error']}")
    model_types = registry["model_types"]
    print(f"\nModelType count: {model_types['count']}")
    print(f"ModelType.DEFAULT: {model_types['default']}")
    print("First ModelType values: " + ", ".join(model_types["first_values"]))
    print("\nConfig classes:")
    for record in registry["config_classes"]:
        constant = record["params_constant"] or "<no matching *_API_PARAMS>"
        print(f"- {record['name']} ({constant}): {', '.join(record['fields'])}")
    if registry["warnings"]:
        print("\nWarnings:")
        for warning in registry["warnings"]:
            print(f"- {warning}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect installed CAMEL model platforms, backend classes, "
            "ModelType enum metadata, and config classes without creating "
            "provider clients or making API calls."
        )
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Defaults to text.",
    )
    args = parser.parse_args(argv)

    registry = collect_registry()
    if args.format == "json":
        print(json.dumps(registry, indent=2, sort_keys=True))
    else:
        print_text(registry)
    return 0


if __name__ == "__main__":
    sys.exit(main())
