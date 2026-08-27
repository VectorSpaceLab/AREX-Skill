#!/usr/bin/env python3
"""Safe Habitat-HITL import and config probe.

This script intentionally does not call hitl_main, instantiate HITL drivers,
open a graphics window, construct a Habitat environment, or start networking.
It is meant for fast diagnostics in the Python environment where Habitat-HITL
is expected to run.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_MODULES = [
    "habitat_hitl",
    "habitat_hitl.core.hitl_main",
    "habitat_hitl.app_states.app_state_abc",
    "habitat_hitl.app_states.app_service",
    "habitat_hitl.core.gui_input",
    "habitat_hitl.core.client_message_manager",
    "habitat_hitl.environment.controllers.controller_helper",
]

OPTIONAL_DEPENDENCIES = ["websockets", "aiohttp", "hydra", "omegaconf"]


def import_module(name: str) -> dict[str, Any]:
    result: dict[str, Any] = {"module": name, "ok": False}
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostics should report any import failure.
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    result["ok"] = True
    result["file"] = getattr(module, "__file__", None)
    return result


def nested_get(data: Any, path: list[str]) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "~", "null", "None"}:
        return None
    if value in {"True", "true"}:
        return True
    if value in {"False", "false"}:
        return False
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def scan_yaml_text(text: str) -> dict[str, Any]:
    """Best-effort dependency-free scan for simple Habitat-HITL YAML files."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    current_list_key_by_indent: dict[int, str] = {}

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if stripped.startswith("- "):
            item = stripped[2:].strip()
            list_key = current_list_key_by_indent.get(indent)
            if list_key is None:
                continue
            parent_list = parent.setdefault(list_key, [])
            if isinstance(parent_list, list):
                parent_list.append(parse_scalar(item))
            continue

        if ":" not in stripped:
            continue

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            current_list_key_by_indent[indent + 2] = key
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value)

    return root


def load_config(path: Path) -> tuple[Any, str]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        return json.loads(text), "json"

    try:
        import yaml  # type: ignore[import-not-found]
    except Exception:
        yaml = None

    if yaml is not None:
        return yaml.safe_load(text), "yaml"

    try:
        from omegaconf import OmegaConf
    except Exception:
        return scan_yaml_text(text), "text-scan"

    cfg = OmegaConf.load(path)
    return OmegaConf.to_container(cfg, resolve=False), "omegaconf"


def probe_config(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "ok": False}
    if not path.exists():
        result["error"] = "config path does not exist"
        return result

    try:
        data, parser = load_config(path)
    except Exception as exc:  # noqa: BLE001 - diagnostics should report parse failures.
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    result["ok"] = True
    result["parser"] = parser
    result["top_level_keys"] = sorted(data.keys()) if isinstance(data, dict) else []

    hitl = nested_get(data, ["habitat_hitl"])
    result["has_habitat_hitl"] = isinstance(hitl, dict)
    if isinstance(hitl, dict):
        networking = hitl.get("networking") or {}
        experimental = hitl.get("experimental") or {}
        headless = experimental.get("headless") if isinstance(experimental, dict) else None
        result["hitl_summary"] = {
            "driver": hitl.get("driver"),
            "target_sps": hitl.get("target_sps"),
            "window_present": hitl.get("window") is not None,
            "networking_enable": networking.get("enable") if isinstance(networking, dict) else None,
            "networking_port": networking.get("port") if isinstance(networking, dict) else None,
            "headless_enable": headless.get("do_headless") if isinstance(headless, dict) else None,
            "gui_controlled_agents_count": len(hitl.get("gui_controlled_agents") or []),
            "disable_policies_and_stepping": hitl.get("disable_policies_and_stepping"),
        }
    else:
        result["note"] = "No top-level habitat_hitl section found. Hydra defaults may compose it at runtime."

    defaults = data.get("defaults") if isinstance(data, dict) else None
    if isinstance(defaults, list):
        result["defaults_mentions_hitl"] = any(
            item == "hitl_defaults"
            or (isinstance(item, dict) and "hitl_defaults" in item.values())
            for item in defaults
        )

    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely import Habitat-HITL modules and optionally summarize a YAML/JSON config."
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional YAML or JSON config file to inspect without composing Hydra or launching HITL.",
    )
    parser.add_argument(
        "--modules",
        nargs="*",
        default=DEFAULT_MODULES,
        help="Python modules to import. Defaults cover practical Habitat-HITL entry points.",
    )
    parser.add_argument(
        "--skip-optional-deps",
        action="store_true",
        help="Do not probe direct optional/runtime dependency imports.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a concise text report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    module_results = [import_module(module_name) for module_name in args.modules]
    dependency_results = [] if args.skip_optional_deps else [
        import_module(module_name) for module_name in OPTIONAL_DEPENDENCIES
    ]
    config_result = probe_config(args.config) if args.config else None

    payload: dict[str, Any] = {
        "python": sys.version.split()[0],
        "modules": module_results,
        "dependencies": dependency_results,
        "config": config_result,
    }

    failures = [item for item in module_results + dependency_results if not item["ok"]]
    if config_result is not None and not config_result["ok"]:
        failures.append(config_result)

    payload["ok"] = not failures

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Python: {payload['python']}")
        print("Module imports:")
        for item in module_results:
            status = "ok" if item["ok"] else "FAIL"
            detail = item.get("file") or item.get("error", "")
            print(f"  {status:4} {item['module']} {detail}")
        if dependency_results:
            print("Dependency imports:")
            for item in dependency_results:
                status = "ok" if item["ok"] else "FAIL"
                detail = item.get("file") or item.get("error", "")
                print(f"  {status:4} {item['module']} {detail}")
        if config_result is not None:
            print("Config probe:")
            print(json.dumps(config_result, indent=2, sort_keys=True))
        print(f"Overall: {'ok' if payload['ok'] else 'FAIL'}")

    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
