#!/usr/bin/env python3
"""Apply torchtune-style config overrides and report config/component shape without launching recipes."""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any

try:
    from omegaconf import OmegaConf
except Exception as exc:  # pragma: no cover - environment dependent
    raise SystemExit(f"omegaconf is required: {type(exc).__name__}: {exc}") from exc


def registry_config_path(name: str) -> Path:
    try:
        import torchtune
        from torchtune._recipe_registry import get_all_recipes
    except Exception as exc:  # pragma: no cover - environment dependent
        raise SystemExit(f"Could not import torchtune registry: {type(exc).__name__}: {exc}") from exc
    root = Path(torchtune.__file__).resolve().parent.parent
    for recipe in get_all_recipes():
        for config in recipe.configs:
            if config.name == name:
                return root / "recipes" / "configs" / config.file_path
    raise SystemExit(f"No built-in config named {name!r}. Run inspect_tune_registry.py first.")


def remove_key(container: Any, path: str) -> None:
    if path.endswith("._component_") or path == "_component_":
        raise ValueError("Removing _component_ is not supported; override the parent component or edit YAML directly.")
    parts = path.split(".")
    node = container
    parents = []
    for part in parts[:-1]:
        if part not in node:
            raise KeyError(path)
        parents.append((node, part))
        node = node[part]
    leaf = parts[-1]
    if leaf not in node:
        raise KeyError(path)
    del node[leaf]
    for parent, key in reversed(parents):
        child = parent.get(key)
        if isinstance(child, dict) and not child:
            del parent[key]


def set_dot(container: dict[str, Any], key: str, value: Any) -> None:
    parts = key.split(".")
    node = container
    for part in parts[:-1]:
        current = node.get(part)
        if not isinstance(current, dict):
            current = {}
            node[part] = current
        node = current
    if isinstance(node.get(parts[-1]), dict) and "_component_" in node[parts[-1]] and isinstance(value, str):
        node[parts[-1]]["_component_"] = value
    else:
        node[parts[-1]] = value


def parse_value(raw: str) -> Any:
    if raw == "None":
        raw = "null"
    return OmegaConf.to_container(OmegaConf.create({"value": raw}), resolve=False)["value"]


def apply_overrides(data: dict[str, Any], tokens: list[str]) -> list[str]:
    notes = []
    for token in tokens:
        if token.startswith("~"):
            target = token[1:]
            remove_key(data, target)
            notes.append(f"removed {target}")
            continue
        if token.startswith("--") or "=" not in token:
            raise ValueError(f"Unsupported override token {token!r}; use key=value or ~field.")
        key, raw = token.split("=", 1)
        set_dot(data, key, parse_value(raw))
        notes.append(f"set {key}")
    return notes


def walk_components(node: Any, prefix: str = ""):
    if isinstance(node, dict):
        if "_component_" in node:
            kwargs = sorted(key for key in node if key != "_component_")
            yield {"path": prefix or ".", "component": node["_component_"], "kwargs": kwargs}
        for key, value in node.items():
            child = f"{prefix}.{key}" if prefix else key
            yield from walk_components(value, child)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_components(value, f"{prefix}[{index}]")


def resolve_component(path: str) -> dict[str, Any]:
    module_name, _, attr = path.rpartition(".")
    if not module_name:
        return {"ok": False, "error": "component is not a module dotpath"}
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, attr)
        try:
            signature = str(inspect.signature(obj))
        except Exception:
            signature = None
        return {"ok": True, "signature": signature}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load a torchtune YAML config, apply override tokens, and report component shape without launching training.")
    parser.add_argument("config", help="Local YAML path, or built-in config name with --from-registry.")
    parser.add_argument("--from-registry", action="store_true", help="Resolve config as a built-in registry config name.")
    parser.add_argument("--resolve-components", action="store_true", help="Import component dotpaths and print signatures when safe dependencies are installed.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args, overrides = parser.parse_known_args(argv)
    args.overrides = overrides

    config_path = registry_config_path(args.config) if args.from_registry else Path(args.config)
    if not config_path.exists():
        raise SystemExit(f"Config file does not exist: {config_path}")

    cfg = OmegaConf.load(config_path)
    data = OmegaConf.to_container(cfg, resolve=False)
    if not isinstance(data, dict):
        raise SystemExit("Top-level config must be a YAML mapping.")

    try:
        notes = apply_overrides(data, args.overrides)
    except Exception as exc:
        raise SystemExit(f"Override error: {type(exc).__name__}: {exc}") from exc

    components = list(walk_components(data))
    if args.resolve_components:
        for component in components:
            component["resolve"] = resolve_component(str(component["component"]))

    result = {
        "config": args.config,
        "resolved_path": str(config_path),
        "override_notes": notes,
        "top_level_keys": sorted(data),
        "components": components,
    }
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Config: {args.config}")
        print(f"Path: {config_path}")
        if notes:
            print("Overrides:")
            for note in notes:
                print(f"- {note}")
        print("Top-level keys:", ", ".join(result["top_level_keys"]))
        print("Components:")
        for component in components:
            line = f"- {component['path']}: {component['component']}"
            if component["kwargs"]:
                line += f" ({', '.join(component['kwargs'])})"
            print(line)
            if args.resolve_components:
                status = component["resolve"]
                if status["ok"]:
                    print(f"  resolves: ok {status.get('signature') or ''}".rstrip())
                else:
                    print(f"  resolves: {status['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
