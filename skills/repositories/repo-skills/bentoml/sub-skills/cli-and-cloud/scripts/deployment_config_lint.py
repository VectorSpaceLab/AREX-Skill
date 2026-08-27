#!/usr/bin/env python3
"""Local BentoCloud deployment config linting with no network calls."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    yaml = None

SECRETISH = re.compile(r"(token|secret|password|apikey|api_key|credential|private[_-]?key)", re.IGNORECASE)
VALID_STRATEGIES = {
    "Recreate",
    "RollingUpdate",
    "RampedSlowRollout",
    "BestEffortControlledRollout",
}


def _load_config(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    if yaml is None:
        raise RuntimeError("PyYAML is required for YAML deployment config files")
    return yaml.safe_load(text)


def _walk(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = f"{path}.{key}" if path else str(key)
            yield next_path, key, item
            yield from _walk(item, next_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            next_path = f"{path}[{index}]"
            yield next_path, index, item
            yield from _walk(item, next_path)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def lint_config(config: Any) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(config, dict):
        return ["Top-level deployment config must be a mapping/object."], warnings

    name = config.get("name")
    if name is not None and not _is_non_empty_string(name):
        errors.append("`name` must be a non-empty string when provided.")

    bento = config.get("bento")
    if bento is not None and not _is_non_empty_string(bento):
        errors.append("`bento` must be a non-empty string when provided.")

    if "access_authorization" in config and not isinstance(config["access_authorization"], bool):
        errors.append("`access_authorization` must be true or false.")

    envs = config.get("envs")
    if envs is not None:
        _lint_envs(envs, "envs", errors, warnings)

    services = config.get("services")
    if services is not None:
        if not isinstance(services, dict) or not services:
            errors.append("`services` must be a non-empty mapping when provided.")
        else:
            for service_name, service_config in services.items():
                if not _is_non_empty_string(service_name):
                    errors.append("service names under `services` must be non-empty strings.")
                if not isinstance(service_config, dict):
                    errors.append(f"`services.{service_name}` must be a mapping/object.")
                    continue
                _lint_service(service_name, service_config, errors, warnings)

    for path, key, value in _walk(config):
        if isinstance(key, str) and SECRETISH.search(key) and isinstance(value, str) and value:
            warnings.append(f"`{path}` looks secret-like; prefer BentoCloud secrets or masked environment injection.")

    return errors, warnings


def _lint_envs(envs: Any, path: str, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(envs, list):
        errors.append(f"`{path}` must be a list of name/value mappings.")
        return
    seen: set[str] = set()
    for index, item in enumerate(envs):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"`{item_path}` must be a mapping/object.")
            continue
        name = item.get("name")
        if not _is_non_empty_string(name):
            errors.append(f"`{item_path}.name` must be a non-empty string.")
        elif name in seen:
            warnings.append(f"`{item_path}.name` duplicates environment variable `{name}`.")
        else:
            seen.add(name)
        if "value" not in item:
            warnings.append(f"`{item_path}` has no `value`; confirm this is intentional.")


def _lint_service(service_name: str, service_config: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    prefix = f"services.{service_name}"
    instance_type = service_config.get("instance_type")
    if instance_type is not None and not _is_non_empty_string(instance_type):
        errors.append(f"`{prefix}.instance_type` must be a non-empty string.")

    strategy = service_config.get("deployment_strategy")
    if strategy is not None and strategy not in VALID_STRATEGIES:
        warnings.append(
            f"`{prefix}.deployment_strategy` is `{strategy}`; known values are {', '.join(sorted(VALID_STRATEGIES))}."
        )

    scaling = service_config.get("scaling")
    if scaling is not None:
        if not isinstance(scaling, dict):
            errors.append(f"`{prefix}.scaling` must be a mapping/object.")
        else:
            min_replicas = scaling.get("min_replicas")
            max_replicas = scaling.get("max_replicas")
            for field_name, value in (("min_replicas", min_replicas), ("max_replicas", max_replicas)):
                if value is not None and (not isinstance(value, int) or value < 0):
                    errors.append(f"`{prefix}.scaling.{field_name}` must be a non-negative integer.")
            if isinstance(min_replicas, int) and isinstance(max_replicas, int) and min_replicas > max_replicas:
                errors.append(f"`{prefix}.scaling.min_replicas` cannot exceed `max_replicas`.")

    envs = service_config.get("envs")
    if envs is not None:
        _lint_envs(envs, f"{prefix}.envs", errors, warnings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Deployment YAML or JSON file to lint locally.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON result.")
    args = parser.parse_args(argv)

    try:
        config = _load_config(args.config)
        errors, warnings = lint_config(config)
    except Exception as exc:  # noqa: BLE001 - CLI helper should report parse/runtime issues clearly
        errors = [str(exc)]
        warnings = []

    result = {"ok": not errors, "errors": errors, "warnings": warnings}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if errors:
            print("Errors:")
            for error in errors:
                print(f"- {error}")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"- {warning}")
        if not errors and not warnings:
            print("OK: no obvious local deployment config issues found.")
        elif not errors:
            print("OK with warnings: review warnings before running cloud commands.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
