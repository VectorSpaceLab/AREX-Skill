#!/usr/bin/env python3
"""Static TaskingAI inference catalog inspector.

Reads provider/model YAML and route decorators from a user-supplied TaskingAI
source tree. It does not import TaskingAI modules, read credentials, or make
network calls.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - reported in main for clean CLI behavior
    yaml = None

MODEL_TYPES = {"chat_completion", "text_embedding", "rerank", "wildcard"}
PROVIDER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required for YAML catalog inspection; install PyYAML or run in the inference environment.")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root is not a mapping: {_safe_rel(path, path.parent)}")
    return data


def _resolve_inference_root(repo_root: Path) -> Tuple[Path, Path]:
    repo_root = repo_root.resolve()
    if (repo_root / "inference" / "providers").is_dir():
        return repo_root, repo_root / "inference"
    if (repo_root / "providers").is_dir() and (repo_root / "app" / "routes").is_dir():
        return repo_root.parent, repo_root
    raise FileNotFoundError("Could not find an inference/providers catalog below --repo-root")


def _iter_provider_dirs(providers_dir: Path) -> Iterable[Path]:
    for entry in sorted(providers_dir.iterdir(), key=lambda p: p.name):
        if not entry.is_dir():
            continue
        if entry.name.startswith("template"):
            continue
        if not PROVIDER_ID_RE.match(entry.name):
            continue
        yield entry


def _route_facts(inference_root: Path, repo_root: Path) -> List[Dict[str, str]]:
    routes_dir = inference_root / "app" / "routes"
    facts: List[Dict[str, str]] = []
    if not routes_dir.is_dir():
        return facts

    for route_file in sorted(routes_dir.rglob("route.py")):
        try:
            tree = ast.parse(route_file.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            facts.append(
                {
                    "file": _safe_rel(route_file, repo_root),
                    "method": "PARSE_ERROR",
                    "path": str(exc),
                    "handler": "",
                    "mounted_path": "",
                }
            )
            continue

        mounted_prefix = "/images" if "/images/" in route_file.as_posix() else "/v1"
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
                    continue
                method = dec.func.attr.upper()
                if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                    continue
                if not dec.args or not isinstance(dec.args[0], ast.Constant) or not isinstance(dec.args[0].value, str):
                    continue
                raw_path = dec.args[0].value
                facts.append(
                    {
                        "file": _safe_rel(route_file, repo_root),
                        "method": method,
                        "path": raw_path,
                        "mounted_path": mounted_prefix + raw_path,
                        "handler": node.name,
                    }
                )
    facts.sort(key=lambda item: (item["mounted_path"], item["method"], item["handler"]))
    return facts


def inspect_catalog(repo_root_arg: Path) -> Dict[str, Any]:
    repo_root, inference_root = _resolve_inference_root(repo_root_arg)
    providers_dir = inference_root / "providers"

    providers: List[Dict[str, Any]] = []
    type_counts: Counter[str] = Counter()
    schema_ids: Dict[str, str] = {}
    duplicate_schema_ids: List[Dict[str, str]] = []
    invalid_model_types: List[Dict[str, str]] = []
    missing_icons: List[str] = []
    missing_provider_yml: List[str] = []
    missing_model_dirs: List[str] = []
    missing_required_provider_keys: List[Dict[str, str]] = []
    missing_adapter_files: List[Dict[str, str]] = []

    for provider_dir in _iter_provider_dirs(providers_dir):
        provider_id = provider_dir.name
        provider_yml = provider_dir / "resources" / "provider.yml"
        models_dir = provider_dir / "resources" / "models"
        icon_file = provider_dir / "resources" / "icon.svg"
        if not provider_yml.is_file():
            missing_provider_yml.append(provider_id)
            continue
        if not icon_file.is_file():
            missing_icons.append(provider_id)
        if not models_dir.is_dir():
            missing_model_dirs.append(provider_id)

        provider_data = _load_yaml(provider_yml)
        if provider_data.get("provider_id") != provider_id:
            missing_required_provider_keys.append(
                {
                    "provider_id": provider_id,
                    "problem": "provider.yml provider_id does not match directory name",
                }
            )
        for key in ("name", "description", "credentials_schema", "resources", "updated_timestamp"):
            if key not in provider_data:
                missing_required_provider_keys.append({"provider_id": provider_id, "problem": f"missing {key}"})

        credential_schema = provider_data.get("credentials_schema") or {}
        credential_properties = credential_schema.get("properties") or {}
        required_credentials = credential_schema.get("required") or []

        provider_type_counts: Counter[str] = Counter()
        model_rows: List[Dict[str, Any]] = []
        for model_yml in sorted(models_dir.glob("*.yml")) if models_dir.is_dir() else []:
            model_data = _load_yaml(model_yml)
            schema_id = str(model_data.get("model_schema_id") or "")
            model_type = str(model_data.get("type") or "")
            if schema_id:
                if schema_id in schema_ids:
                    duplicate_schema_ids.append(
                        {
                            "model_schema_id": schema_id,
                            "first": schema_ids[schema_id],
                            "duplicate": _safe_rel(model_yml, repo_root),
                        }
                    )
                else:
                    schema_ids[schema_id] = _safe_rel(model_yml, repo_root)
            if model_type not in MODEL_TYPES:
                invalid_model_types.append(
                    {
                        "model_schema_id": schema_id,
                        "type": model_type,
                        "file": _safe_rel(model_yml, repo_root),
                    }
                )
            provider_type_counts[model_type] += 1
            type_counts[model_type] += 1
            model_rows.append(
                {
                    "model_schema_id": schema_id,
                    "provider_model_id": model_data.get("provider_model_id"),
                    "type": model_type,
                    "has_properties": bool(model_data.get("properties")),
                    "config_ids": [item.get("config_id") for item in (model_data.get("config_schemas") or []) if isinstance(item, dict)],
                    "file": _safe_rel(model_yml, repo_root),
                }
            )

        adapter_files = {
            "chat_completion": (provider_dir / "chat_completion.py").is_file(),
            "text_embedding": (provider_dir / "text_embedding.py").is_file(),
            "rerank": (provider_dir / "rerank.py").is_file(),
        }
        for model_type, adapter_name in (
            ("chat_completion", "chat_completion.py"),
            ("text_embedding", "text_embedding.py"),
            ("rerank", "rerank.py"),
        ):
            if provider_type_counts.get(model_type, 0) and not adapter_files[model_type]:
                missing_adapter_files.append({"provider_id": provider_id, "model_type": model_type, "missing": adapter_name})

        providers.append(
            {
                "provider_id": provider_id,
                "model_count": sum(provider_type_counts.values()),
                "model_type_counts": dict(sorted(provider_type_counts.items())),
                "required_credentials": list(required_credentials),
                "credential_properties": sorted(credential_properties.keys()),
                "pass_provider_level_credential_check": bool(provider_data.get("pass_provider_level_credential_check", True)),
                "default_credential_verification_model_type": provider_data.get("default_credential_verification_model_type"),
                "default_credential_verification_provider_model_id": provider_data.get("default_credential_verification_provider_model_id"),
                "enable_proxy": bool(provider_data.get("enable_proxy", False)),
                "enable_custom_headers": bool(provider_data.get("enable_custom_headers", False)),
                "return_token_usage": bool(provider_data.get("return_token_usage", False)),
                "return_stream_token_usage": bool(provider_data.get("return_stream_token_usage", False)),
                "adapter_files": adapter_files,
                "models": model_rows,
            }
        )

    providers.sort(key=lambda item: item["provider_id"])
    route_facts = _route_facts(inference_root, repo_root)
    wildcard_schemas = [
        {"provider_id": provider["provider_id"], "model_schema_id": model["model_schema_id"]}
        for provider in providers
        for model in provider["models"]
        if model["type"] == "wildcard" or model["model_schema_id"].endswith("/wildcard")
    ]

    problems: Dict[str, Any] = {
        "missing_provider_yml": missing_provider_yml,
        "missing_model_dirs": missing_model_dirs,
        "missing_icons": missing_icons,
        "missing_required_provider_keys": missing_required_provider_keys,
        "duplicate_schema_ids": duplicate_schema_ids,
        "invalid_model_types": invalid_model_types,
        "missing_adapter_files": missing_adapter_files,
    }
    has_problems = any(bool(value) for value in problems.values())

    return {
        "summary": {
            "provider_count": len(providers),
            "model_schema_count": sum(provider["model_count"] for provider in providers),
            "model_type_counts": dict(sorted(type_counts.items())),
            "wildcard_schema_count": len(wildcard_schemas),
            "schema_only_provider_validation_count": sum(
                1 for provider in providers if provider["pass_provider_level_credential_check"]
            ),
            "providers_with_proxy_flag": [provider["provider_id"] for provider in providers if provider["enable_proxy"]],
            "providers_with_custom_headers_flag": [
                provider["provider_id"] for provider in providers if provider["enable_custom_headers"]
            ],
            "route_count": len(route_facts),
            "has_problems": has_problems,
        },
        "providers": providers,
        "wildcard_schemas": wildcard_schemas,
        "routes": route_facts,
        "problems": problems,
    }


def _print_human(report: Dict[str, Any]) -> None:
    summary = report["summary"]
    print("TaskingAI inference catalog static inspection")
    print("No TaskingAI modules imported; no credentials read; no network calls made.")
    print()
    print(f"Providers: {summary['provider_count']}")
    print(f"Model schemas: {summary['model_schema_count']}")
    print("Model type counts:")
    for key, value in summary["model_type_counts"].items():
        print(f"  - {key}: {value}")
    print(f"Wildcard schemas: {summary['wildcard_schema_count']}")
    print(f"Schema-only provider validation providers: {summary['schema_only_provider_validation_count']}")
    print(f"Providers with proxy flag: {', '.join(summary['providers_with_proxy_flag']) or '(none)'}")
    print(f"Providers with custom-header flag: {', '.join(summary['providers_with_custom_headers_flag']) or '(none)'}")
    print(f"Route decorators found: {summary['route_count']}")
    print()

    print("Provider table:")
    for provider in report["providers"]:
        counts = provider["model_type_counts"]
        count_text = ", ".join(f"{k}={v}" for k, v in counts.items()) or "none"
        req = ", ".join(provider["required_credentials"]) or "(none)"
        check = "schema-only" if provider["pass_provider_level_credential_check"] else "model-call"
        default = provider["default_credential_verification_model_type"] or "-"
        default_model = provider["default_credential_verification_provider_model_id"] or "-"
        print(f"  - {provider['provider_id']}: models={provider['model_count']} ({count_text}); required={req}; verify={check}; default={default}/{default_model}")
    print()

    print("Routes:")
    for route in report["routes"]:
        print(f"  - {route['method']} {route['mounted_path']} -> {route['handler']} ({route['file']})")
    print()

    problems = report["problems"]
    if any(bool(value) for value in problems.values()):
        print("Problems:")
        for key, value in problems.items():
            if value:
                print(f"  - {key}: {json.dumps(value, ensure_ascii=False)}")
    else:
        print("Problems: none detected")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Static TaskingAI inference provider/model catalog inspector")
    parser.add_argument("--repo-root", required=True, help="Path to a TaskingAI repository root, or to its inference/ directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if catalog consistency problems are detected")
    args = parser.parse_args(argv)

    try:
        report = inspect_catalog(Path(args.repo_root))
    except Exception as exc:
        print(f"inspect_inference_catalog.py: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)

    if args.strict and report["summary"]["has_problems"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
