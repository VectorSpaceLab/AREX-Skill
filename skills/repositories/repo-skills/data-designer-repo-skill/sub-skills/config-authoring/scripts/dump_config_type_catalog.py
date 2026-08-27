#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Dump a live DataDesigner config type catalog from installed package imports.

This helper intentionally imports the installed ``data_designer`` package and
never reads a source checkout. Use it after package upgrades or in unfamiliar
environments to verify public config exports, Pydantic model fields, enum
values, builder signatures, and (when importable) interface signatures.

Examples:
    python dump_config_type_catalog.py
    python dump_config_type_catalog.py --family samplers --indent 0
    python dump_config_type_catalog.py --no-interface > datadesigner-config-catalog.json
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from importlib import metadata
from typing import Any

PACKAGE_NAMES = ("data-designer", "data-designer-config", "data-designer-engine")

FAMILIES: dict[str, list[str]] = {
    "columns": [
        "SamplerColumnConfig",
        "LLMTextColumnConfig",
        "LLMCodeColumnConfig",
        "LLMStructuredColumnConfig",
        "LLMJudgeColumnConfig",
        "EmbeddingColumnConfig",
        "ImageColumnConfig",
        "ValidationColumnConfig",
        "ExpressionColumnConfig",
        "SeedDatasetColumnConfig",
        "CustomColumnConfig",
        "Score",
        "SkipConfig",
    ],
    "samplers": [
        "UUIDSamplerParams",
        "CategorySamplerParams",
        "SubcategorySamplerParams",
        "UniformSamplerParams",
        "GaussianSamplerParams",
        "BernoulliSamplerParams",
        "BernoulliMixtureSamplerParams",
        "BinomialSamplerParams",
        "PoissonSamplerParams",
        "ScipySamplerParams",
        "DatetimeSamplerParams",
        "TimeDeltaSamplerParams",
        "PersonSamplerParams",
        "PersonFromFakerSamplerParams",
    ],
    "validators": ["CodeValidatorParams", "LocalCallableValidatorParams", "RemoteValidatorParams"],
    "processors": ["DropColumnsProcessorConfig", "SchemaTransformProcessorConfig"],
    "models_and_tools": [
        "ModelConfig",
        "ModelProvider",
        "ChatCompletionInferenceParams",
        "EmbeddingInferenceParams",
        "ImageInferenceParams",
        "ManualDistribution",
        "ManualDistributionParams",
        "UniformDistribution",
        "UniformDistributionParams",
        "ToolConfig",
        "MCPProvider",
        "LocalStdioMCPProvider",
        "ImageContext",
        "AudioContext",
        "VideoContext",
    ],
    "seed_sources": [
        "LocalFileSeedSource",
        "HuggingFaceSeedSource",
        "DataFrameSeedSource",
        "DirectorySeedSource",
        "FileContentsSeedSource",
        "AgentRolloutSeedSource",
        "SeedConfig",
        "IndexRange",
        "PartitionBlock",
    ],
    "constraints": ["ScalarInequalityConstraint", "ColumnInequalityConstraint"],
    "run_config": ["RunConfig", "ThrottleConfig", "RequestAdmissionTuningConfig"],
}

ENUM_NAMES = [
    "DataDesignerColumnType",
    "SamplerType",
    "ValidatorType",
    "ProcessorType",
    "SamplingStrategy",
    "AgentRolloutFormat",
    "GenerationType",
    "TraceType",
    "CodeLang",
]

BUILDER_METHODS = [
    "__init__",
    "add_column",
    "add_constraint",
    "add_processor",
    "add_profiler",
    "build",
    "delete_column",
    "delete_constraints",
    "delete_model_config",
    "delete_tool_config",
    "from_config",
    "get_column_config",
    "get_column_configs",
    "get_profilers",
    "with_seed_dataset",
]

INTERFACE_METHODS = [
    "__init__",
    "validate",
    "preview",
    "create",
    "acreate",
    "check_models",
    "compose_workflow",
    "list_mcp_tool_names",
    "set_run_config",
]


def _package_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for package_name in PACKAGE_NAMES:
        try:
            versions[package_name] = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            versions[package_name] = "<not-installed-as-distribution>"
    return versions


def _safe_repr(value: Any) -> str:
    try:
        text = repr(value)
    except Exception as exc:  # pragma: no cover - defensive for unusual defaults
        text = f"<repr-error {type(exc).__name__}: {exc}>"
    if len(text) > 180:
        text = text[:177] + "..."
    return text


def _signature_map(obj: Any, method_names: list[str]) -> dict[str, str]:
    signatures: dict[str, str] = {}
    for method_name in method_names:
        try:
            signatures[method_name] = str(inspect.signature(getattr(obj, method_name)))
        except Exception as exc:
            signatures[method_name] = f"<unavailable {type(exc).__name__}: {exc}>"
    return signatures


def _describe_model(cls: Any) -> dict[str, Any]:
    if not hasattr(cls, "model_fields"):
        return {
            "qualified_name": f"{getattr(cls, '__module__', '<unknown>')}.{getattr(cls, '__name__', repr(cls))}",
            "error": "object has no Pydantic model_fields",
        }

    fields: dict[str, dict[str, Any]] = {}
    for name, field in cls.model_fields.items():
        try:
            required = bool(field.is_required())
        except Exception:
            required = False
        default_factory = getattr(field, "default_factory", None)
        if required:
            default = "<required>"
        elif default_factory is not None:
            default = f"<factory {getattr(default_factory, '__name__', repr(default_factory))}>"
        else:
            default = _safe_repr(getattr(field, "default", None))
        fields[name] = {
            "annotation": str(getattr(field, "annotation", "")),
            "required": required,
            "default": default,
            "description": getattr(field, "description", None),
        }

    doc = inspect.getdoc(cls) or ""
    first_doc_line = doc.splitlines()[0] if doc else None
    return {
        "qualified_name": f"{cls.__module__}.{cls.__name__}",
        "doc": first_doc_line,
        "fields": fields,
    }


def _collect_family(dd: Any, names: list[str]) -> dict[str, Any]:
    family: dict[str, Any] = {}
    for name in names:
        try:
            cls = getattr(dd, name)
            family[name] = _describe_model(cls)
        except Exception as exc:
            family[name] = {"error": f"{type(exc).__name__}: {exc}"}
    return family


def _enum_values(dd: Any) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name in ENUM_NAMES:
        try:
            enum_cls = getattr(dd, name)
            values[name] = [member.value for member in enum_cls]
        except Exception as exc:
            values[name] = {"error": f"{type(exc).__name__}: {exc}"}
    return values


def _interface_signatures() -> dict[str, Any]:
    try:
        from data_designer.interface import DataDesigner  # type: ignore
    except Exception as exc:
        return {"_error": f"{type(exc).__name__}: {exc}"}
    return _signature_map(DataDesigner, INTERFACE_METHODS)


def collect_catalog(*, family: str, include_interface: bool) -> dict[str, Any]:
    try:
        import data_designer.config as dd  # type: ignore
    except Exception as exc:
        print(
            "Could not import data_designer.config. Install data-designer before running this helper. "
            f"Import error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    selected_families = FAMILIES if family == "all" else {family: FAMILIES[family]}
    catalog: dict[str, Any] = {
        "package_versions": _package_versions(),
        "exports_count": len(getattr(dd, "__all__", [])),
        "exports": sorted(getattr(dd, "__all__", [])),
        "builder_signatures": _signature_map(dd.DataDesignerConfigBuilder, BUILDER_METHODS),
        "enum_values": _enum_values(dd),
        "families": {name: _collect_family(dd, class_names) for name, class_names in selected_families.items()},
    }
    if include_interface:
        catalog["interface_signatures"] = _interface_signatures()
    return catalog


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=["all", *sorted(FAMILIES)], default="all", help="Catalog family to dump")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent; use 0 for compact single-line output")
    parser.add_argument(
        "--no-interface",
        action="store_true",
        help="Skip importing data_designer.interface; useful in config-only environments",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    catalog = collect_catalog(family=args.family, include_interface=not args.no_interface)
    indent = None if args.indent == 0 else args.indent
    print(json.dumps(catalog, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
