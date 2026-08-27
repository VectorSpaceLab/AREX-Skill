#!/usr/bin/env python3
"""Safely inspect Kiln model/provider registries without external calls."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from typing import Any


def _enum_value(value: Any) -> str:
    return getattr(value, "value", str(value))


def _load_registries() -> dict[str, Any]:
    try:
        from kiln_ai.adapters import ml_embedding_model_list, ml_model_list, reranker_list
        from kiln_ai.adapters.provider_tools import provider_name_from_id, provider_warnings
        from kiln_ai.datamodel.datamodel_enums import ModelProviderName
    except Exception as exc:  # pragma: no cover - depends on caller environment
        raise RuntimeError(
            "Failed to import Kiln registries. Install kiln-ai in this Python "
            "environment before running this script. Original error: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    return {
        "ml_model_list": ml_model_list,
        "ml_embedding_model_list": ml_embedding_model_list,
        "reranker_list": reranker_list,
        "provider_name_from_id": provider_name_from_id,
        "provider_warnings": provider_warnings,
        "ModelProviderName": ModelProviderName,
    }


def _provider_counts(items: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for item in items:
        for provider in getattr(item, "providers", []) or []:
            counts[_enum_value(provider.name)] += 1
    return dict(sorted(counts.items()))


def _provider_feature_counts(models: list[Any]) -> dict[str, dict[str, int]]:
    features: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "structured_output": 0,
            "function_calling": 0,
            "thinking_levels": 0,
            "reasoning_capable": 0,
            "deprecated": 0,
        }
    )
    for model in models:
        for provider in getattr(model, "providers", []) or []:
            key = _enum_value(provider.name)
            if getattr(provider, "supports_structured_output", False):
                features[key]["structured_output"] += 1
            if getattr(provider, "supports_function_calling", False):
                features[key]["function_calling"] += 1
            if getattr(provider, "available_thinking_levels", None):
                features[key]["thinking_levels"] += 1
            if getattr(provider, "reasoning_capable", False):
                features[key]["reasoning_capable"] += 1
            if getattr(provider, "deprecated", False):
                features[key]["deprecated"] += 1
    return {key: features[key] for key in sorted(features)}


def _models_for_provider(items: list[Any], provider_filter: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model in items:
        for provider in getattr(model, "providers", []) or []:
            if _enum_value(provider.name) != provider_filter:
                continue
            rows.append(
                {
                    "name": str(getattr(model, "name", "")),
                    "friendly_name": getattr(model, "friendly_name", None),
                    "family": str(getattr(model, "family", "")),
                    "provider_model_id": getattr(provider, "model_id", None),
                    "structured_output_mode": _enum_value(
                        getattr(provider, "structured_output_mode", "")
                    ),
                    "supports_structured_output": bool(
                        getattr(provider, "supports_structured_output", False)
                    ),
                    "supports_function_calling": bool(
                        getattr(provider, "supports_function_calling", False)
                    ),
                    "default_thinking_level": getattr(
                        provider, "default_thinking_level", None
                    ),
                    "available_thinking_levels": getattr(
                        provider, "available_thinking_levels", None
                    ),
                    "deprecated": bool(getattr(provider, "deprecated", False)),
                }
            )
    return rows


def build_report(provider_filter: str | None = None, include_deprecated: bool = False) -> dict[str, Any]:
    registries = _load_registries()
    ml_model_list = registries["ml_model_list"]
    ml_embedding_model_list = registries["ml_embedding_model_list"]
    reranker_list = registries["reranker_list"]
    provider_name_from_id = registries["provider_name_from_id"]
    provider_warnings = registries["provider_warnings"]
    ModelProviderName = registries["ModelProviderName"]

    llm_models = list(ml_model_list.built_in_models)
    embedding_models = list(ml_embedding_model_list.built_in_embedding_models)
    rerankers = list(reranker_list.built_in_rerankers)

    llm_counts = _provider_counts(llm_models)
    embedding_counts = _provider_counts(embedding_models)
    reranker_counts = _provider_counts(rerankers)
    feature_counts = _provider_feature_counts(llm_models)

    providers: list[dict[str, Any]] = []
    for provider in ModelProviderName:
        provider_id = _enum_value(provider)
        if provider_filter and provider_id != provider_filter:
            continue
        warning = provider_warnings.get(provider)
        providers.append(
            {
                "id": provider_id,
                "friendly_name": provider_name_from_id(provider_id),
                "llm_models": llm_counts.get(provider_id, 0),
                "embedding_models": embedding_counts.get(provider_id, 0),
                "rerankers": reranker_counts.get(provider_id, 0),
                "features": feature_counts.get(provider_id, {}),
                "required_config_keys": list(warning.required_config_keys)
                if warning is not None
                else [],
            }
        )

    report: dict[str, Any] = {
        "summary": {
            "llm_models": len(llm_models),
            "embedding_models": len(embedding_models),
            "rerankers": len(rerankers),
            "providers": len(list(ModelProviderName)),
        },
        "providers": providers,
        "safety": {
            "external_provider_calls": False,
            "local_service_probes": False,
            "mcp_sessions": False,
            "credentials_read": False,
        },
    }

    if provider_filter:
        known_ids = {_enum_value(provider) for provider in ModelProviderName}
        if provider_filter not in known_ids:
            report["error"] = f"Unknown provider {provider_filter!r}. Valid providers: {', '.join(sorted(known_ids))}"
            return report
        models = _models_for_provider(llm_models, provider_filter)
        if not include_deprecated:
            models = [row for row in models if not row["deprecated"]]
        report["models"] = models

    return report


def _print_table(report: dict[str, Any], provider_filter: str | None, limit: int) -> None:
    summary = report["summary"]
    print(
        "Kiln registry summary: "
        f"{summary['llm_models']} LLM models, "
        f"{summary['embedding_models']} embedding models, "
        f"{summary['rerankers']} rerankers, "
        f"{summary['providers']} provider enum values"
    )
    print("Safety: no external provider calls, no local service probes, no MCP sessions")

    if report.get("error"):
        print(f"ERROR: {report['error']}", file=sys.stderr)
        return

    print()
    print("Providers:")
    print(
        f"{'provider':<24} {'llm':>5} {'embed':>5} {'rerank':>6} "
        f"{'struct':>6} {'tools':>6} {'think':>6} required_config_keys"
    )
    for provider in report["providers"]:
        features = provider.get("features", {})
        required = ",".join(provider["required_config_keys"])
        print(
            f"{provider['id']:<24} "
            f"{provider['llm_models']:>5} "
            f"{provider['embedding_models']:>5} "
            f"{provider['rerankers']:>6} "
            f"{features.get('structured_output', 0):>6} "
            f"{features.get('function_calling', 0):>6} "
            f"{features.get('thinking_levels', 0):>6} "
            f"{required}"
        )

    if provider_filter and "models" in report:
        models = report["models"]
        print()
        print(f"Models for provider {provider_filter} (showing {min(limit, len(models))} of {len(models)}):")
        for row in models[:limit]:
            thinking = row.get("default_thinking_level") or "-"
            mode = row.get("structured_output_mode") or "-"
            provider_model_id = row.get("provider_model_id") or "-"
            deprecated = " deprecated" if row.get("deprecated") else ""
            print(
                f"- {row['name']} ({row.get('friendly_name') or row['family']}): "
                f"provider_model_id={provider_model_id}, structured_mode={mode}, "
                f"default_thinking={thinking}{deprecated}"
            )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect installed Kiln model/provider registries without calling "
            "external providers, local model services, or MCP servers."
        )
    )
    parser.add_argument(
        "--provider",
        help="Optional ModelProviderName value to filter, for example openai or openrouter.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum models to print for --provider in text mode. Default: 25.",
    )
    parser.add_argument(
        "--include-deprecated",
        action="store_true",
        help="Include deprecated provider model entries in --provider model details.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a text table.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.limit < 0:
        print("--limit must be non-negative", file=sys.stderr)
        return 2

    try:
        report = build_report(args.provider, args.include_deprecated)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        _print_table(report, args.provider, args.limit)

    return 1 if report.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
