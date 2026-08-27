#!/usr/bin/env python3
"""Safely inspect a Feast feature repository configuration.

This script intentionally does not run Feast CLI commands, import Python files from
feature repositories, contact backend services, apply changes, or delete resources.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in minimal envs
    yaml = None  # type: ignore[assignment]


SENSITIVE_KEYS = {"password", "secret", "token", "key", "credential"}


def status(level: str, message: str) -> dict[str, str]:
    return {"level": level, "message": message}


def has_sensitive_name(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_KEYS)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "<redacted>" if has_sensitive_name(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def load_yaml(path: Path) -> tuple[Optional[dict[str, Any]], list[dict[str, str]]]:
    messages: list[dict[str, str]] = []
    if yaml is None:
        return None, [status("error", "PyYAML is not installed; install pyyaml to parse feature_store.yaml.")]
    try:
        raw = yaml.safe_load(path.read_text())
    except Exception as exc:  # noqa: BLE001 - show parser failure clearly
        return None, [status("error", f"Failed to parse YAML: {exc}")]
    if raw is None:
        return {}, [status("error", "feature_store.yaml is empty.")]
    if not isinstance(raw, dict):
        return None, [status("error", "feature_store.yaml must contain a top-level mapping.")]
    return raw, messages


def resolve_path(repo_path: Path, value: str) -> Optional[Path]:
    if "://" in value or value.startswith(("s3://", "gs://", "az://")):
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = repo_path / candidate
    return candidate


def inspect_config(repo_path: Path, config: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    messages: list[dict[str, str]] = []
    summary: dict[str, Any] = {
        "project": config.get("project"),
        "provider": config.get("provider"),
        "registry": config.get("registry"),
        "online_store": config.get("online_store"),
        "offline_store": config.get("offline_store"),
    }

    for required_key in ("project", "provider", "registry"):
        if required_key not in config:
            messages.append(status("error", f"Missing required top-level key: {required_key}"))

    project = config.get("project")
    if isinstance(project, str):
        if project.startswith(("_", "-")):
            messages.append(status("error", "Project name must not start with '_' or '-'."))
        if not project.replace("_", "").replace("-", "").isalnum():
            messages.append(status("error", "Project name should use only letters, numbers, underscores, and hyphens."))
    elif project is not None:
        messages.append(status("error", "Project must be a string."))

    provider = config.get("provider")
    if provider == "local":
        messages.append(status("ok", "Local provider selected."))
    elif provider is not None:
        messages.append(status("warn", f"Provider '{provider}' may require backend credentials and optional Feast extras."))

    registry = config.get("registry")
    registry_path = None
    if isinstance(registry, str):
        registry_path = registry
        summary["registry_type"] = "file"
    elif isinstance(registry, dict):
        summary["registry_type"] = registry.get("registry_type", "file")
        registry_path = registry.get("path")
        if summary["registry_type"] != "file":
            messages.append(status("warn", f"Registry type '{summary['registry_type']}' may require backend dependencies or credentials."))
    elif registry is not None:
        messages.append(status("error", "Registry must be a string path or mapping."))

    if isinstance(registry_path, str):
        local_registry = resolve_path(repo_path, registry_path)
        if local_registry is not None:
            summary["registry_resolved_path"] = str(local_registry)
            parent = local_registry.parent
            if parent.exists():
                messages.append(status("ok", f"Registry parent exists: {parent}"))
            else:
                messages.append(status("warn", f"Registry parent directory does not exist yet: {parent}"))

    online_store = config.get("online_store")
    if online_store is None and provider == "local":
        messages.append(status("warn", "No online_store block found; local repos commonly use sqlite."))
    elif isinstance(online_store, dict):
        online_type = online_store.get("type")
        summary["online_store_type"] = online_type
        if online_type is None:
            messages.append(status("warn", "online_store block has no explicit type."))
        elif online_type == "sqlite":
            sqlite_path = online_store.get("path")
            if isinstance(sqlite_path, str):
                local_sqlite = resolve_path(repo_path, sqlite_path)
                if local_sqlite is not None:
                    summary["online_store_resolved_path"] = str(local_sqlite)
                    if local_sqlite.parent.exists():
                        messages.append(status("ok", f"SQLite parent exists: {local_sqlite.parent}"))
                    else:
                        messages.append(status("warn", f"SQLite parent directory does not exist yet: {local_sqlite.parent}"))
            else:
                messages.append(status("warn", "sqlite online_store should include a path."))
        else:
            messages.append(status("warn", f"Online store '{online_type}' may require optional dependencies or services."))
    elif isinstance(online_store, str):
        summary["online_store_type"] = online_store
    elif online_store is not None:
        messages.append(status("error", "online_store must be a mapping or string when provided."))

    offline_store = config.get("offline_store")
    if isinstance(offline_store, dict):
        offline_type = offline_store.get("type")
        summary["offline_store_type"] = offline_type
        if offline_type and offline_type not in {"file", "dask", "duckdb"}:
            messages.append(status("warn", f"Offline store '{offline_type}' may require optional dependencies or services."))
    elif isinstance(offline_store, str):
        summary["offline_store_type"] = offline_store
    elif offline_store is not None:
        messages.append(status("error", "offline_store must be a mapping or string when provided."))

    return summary, messages


def inspect_repo_files(repo_path: Path) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    feastignore = repo_path / ".feastignore"
    if feastignore.exists():
        messages.append(status("ok", ".feastignore exists."))
    else:
        messages.append(status("warn", ".feastignore is missing; Feast will import Python files recursively except built-in ignored paths."))

    python_files = [path for path in repo_path.rglob("*.py") if "__pycache__" not in path.parts]
    if python_files:
        messages.append(status("info", f"Found {len(python_files)} Python file(s); plan/apply will import non-ignored files."))
    else:
        messages.append(status("info", "No Python feature definition files found."))
    return messages


def inspect_feast(require_feast: bool) -> tuple[dict[str, Any], list[dict[str, str]]]:
    messages: list[dict[str, str]] = []
    summary: dict[str, Any] = {"available": False}
    try:
        feast = importlib.import_module("feast")
    except Exception as exc:  # noqa: BLE001 - import failures are diagnostic output
        level = "error" if require_feast else "warn"
        messages.append(status(level, f"Could not import feast: {exc}"))
        return summary, messages

    summary["available"] = True
    summary["version"] = getattr(feast, "__version__", "unknown")
    messages.append(status("ok", f"Imported feast version {summary['version']}"))

    try:
        from feast import FeatureStore  # noqa: PLC0415

        summary["feature_store"] = str(FeatureStore)
    except Exception as exc:  # noqa: BLE001
        messages.append(status("warn", f"Imported feast but could not import FeatureStore: {exc}"))
    return summary, messages


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely inspect a Feast feature repository without applying changes or importing repo Python files."
    )
    parser.add_argument("repo", nargs="?", default=".", help="Feature repository directory containing feature_store.yaml.")
    parser.add_argument("--feature-store-yaml", "-f", help="Optional path to a specific feature_store.yaml file.")
    parser.add_argument("--require-feast", action="store_true", help="Return a non-zero exit code if the feast package cannot be imported.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of human-readable text.")
    args = parser.parse_args()

    repo_path = Path(args.repo).expanduser().resolve()
    yaml_path = Path(args.feature_store_yaml).expanduser().resolve() if args.feature_store_yaml else repo_path / "feature_store.yaml"

    report: dict[str, Any] = {
        "repo_path": str(repo_path),
        "feature_store_yaml": str(yaml_path),
        "messages": [],
        "config_summary": {},
        "feast": {},
    }

    if not repo_path.exists() or not repo_path.is_dir():
        report["messages"].append(status("error", f"Repo path does not exist or is not a directory: {repo_path}"))
    if not yaml_path.exists():
        report["messages"].append(status("error", f"feature_store.yaml not found: {yaml_path}"))

    if yaml_path.exists():
        config, messages = load_yaml(yaml_path)
        report["messages"].extend(messages)
        if config is not None:
            summary, config_messages = inspect_config(repo_path, config)
            report["config_summary"] = redact(summary)
            report["messages"].extend(config_messages)

    if repo_path.exists() and repo_path.is_dir():
        report["messages"].extend(inspect_repo_files(repo_path))

    feast_summary, feast_messages = inspect_feast(args.require_feast)
    report["feast"] = feast_summary
    report["messages"].extend(feast_messages)

    has_error = any(item["level"] == "error" for item in report["messages"])

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Feature repo: {report['repo_path']}")
        print(f"Config file:  {report['feature_store_yaml']}")
        if report["config_summary"]:
            print("\nConfig summary:")
            for key, value in report["config_summary"].items():
                print(f"  {key}: {value}")
        print("\nChecks:")
        for item in report["messages"]:
            print(f"  [{item['level'].upper()}] {item['message']}")

    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
