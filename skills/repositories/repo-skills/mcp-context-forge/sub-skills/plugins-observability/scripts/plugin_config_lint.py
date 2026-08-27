#!/usr/bin/env python3
"""Summarize and lint a ContextForge plugin YAML file without importing plugins.

Examples:
  python plugin_config_lint.py --config plugins/config.yaml
  python plugin_config_lint.py --config plugins/config.yaml --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - depends on environment
    yaml = None  # type: ignore[assignment]

VALID_HOOKS = {
    "prompt_pre_fetch",
    "prompt_post_fetch",
    "tool_pre_invoke",
    "tool_post_invoke",
    "resource_pre_fetch",
    "resource_post_fetch",
    "http_pre_request",
    "http_auth_resolve_user",
    "http_auth_check_permission",
    "http_post_request",
}
VALID_MODES = {"enforce", "enforce_ignore_error", "permissive", "disabled", "sequential", "transform"}


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise SystemExit("PyYAML is required to read plugin config YAML. Install PyYAML or run inside the ContextForge environment.")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise SystemExit("plugin config root must be a mapping")
    return data


def lint_plugin(index: int, item: Any) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(item, dict):
        return {"index": index}, [f"plugins[{index}] is not a mapping"], warnings

    name = item.get("name")
    kind = item.get("kind")
    hooks = item.get("hooks") or []
    mode = item.get("mode", "enforce")
    priority = item.get("priority")
    conditions = item.get("conditions") or []

    if not isinstance(name, str) or not name:
        errors.append(f"plugins[{index}] missing non-empty name")
    if not isinstance(kind, str) or not kind:
        errors.append(f"plugins[{index}] missing non-empty kind")
    if not isinstance(hooks, list) or not all(isinstance(h, str) for h in hooks):
        errors.append(f"plugins[{index}] hooks must be a list of strings")
        hooks = []
    else:
        unknown = sorted(set(hooks) - VALID_HOOKS)
        if unknown:
            warnings.append(f"{name or index}: unknown hook(s): {', '.join(unknown)}")
    if mode not in VALID_MODES:
        warnings.append(f"{name or index}: unusual mode {mode!r}; expected one of {sorted(VALID_MODES)}")
    if priority is not None and not isinstance(priority, int):
        warnings.append(f"{name or index}: priority is not an integer")
    if conditions and not isinstance(conditions, list):
        warnings.append(f"{name or index}: conditions should be a list")
    if kind == "external" and not item.get("mcp"):
        errors.append(f"{name or index}: external plugin requires an mcp block")

    summary = {
        "index": index,
        "name": name,
        "kind": kind,
        "mode": mode,
        "priority": priority,
        "hooks": hooks,
        "conditions": len(conditions) if isinstance(conditions, list) else "invalid",
        "external": kind == "external",
    }
    return summary, errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only ContextForge plugin config lint and summary.")
    parser.add_argument("--config", required=True, help="Path to plugin YAML config.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    path = Path(args.config)
    if not path.exists():
        raise SystemExit(f"config file not found: {path}")

    data = load_yaml(path)
    plugins = data.get("plugins", [])
    errors: list[str] = []
    warnings: list[str] = []
    summaries: list[dict[str, Any]] = []

    if not isinstance(plugins, list):
        errors.append("top-level 'plugins' must be a list")
        plugins = []

    names: set[str] = set()
    for index, item in enumerate(plugins):
        summary, item_errors, item_warnings = lint_plugin(index, item)
        summaries.append(summary)
        errors.extend(item_errors)
        warnings.extend(item_warnings)
        name = summary.get("name")
        if isinstance(name, str):
            if name in names:
                errors.append(f"duplicate plugin name: {name}")
            names.add(name)

    result = {
        "config": str(path),
        "plugin_count": len(summaries),
        "plugins": summaries,
        "warnings": warnings,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Config: {path}")
        print(f"Plugins: {len(summaries)}")
        for item in summaries:
            print(f"- {item.get('name') or '<missing>'}: kind={item.get('kind')} mode={item.get('mode')} hooks={','.join(item.get('hooks') or [])}")
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
        for error in errors:
            print(f"error: {error}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
