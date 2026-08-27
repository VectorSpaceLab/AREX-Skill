#!/usr/bin/env python3
"""Inspect LMDeploy backend config defaults without loading models."""

from __future__ import annotations

import argparse
import ast
import dataclasses
import enum
import importlib
import json
import sys
from pathlib import Path
from typing import Any


def _maybe_add_current_checkout() -> None:
    cwd = Path.cwd()
    if (cwd / "lmdeploy").is_dir() and str(cwd) not in sys.path:
        sys.path.insert(0, str(cwd))


def _safe_import(module_name: str):
    try:
        return importlib.import_module(module_name), None
    except Exception as exc:  # pragma: no cover - diagnostic path
        return None, f"{type(exc).__name__}: {exc}"


def _jsonable(value: Any) -> Any:
    if isinstance(value, enum.Enum):
        return {"name": value.name, "value": value.value}
    if isinstance(value, type):
        return f"{value.__module__}.{value.__qualname__}"
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _dataclass_defaults(cls: type) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for field in dataclasses.fields(cls):
        if field.default is not dataclasses.MISSING:
            defaults[field.name] = _jsonable(field.default)
        elif field.default_factory is not dataclasses.MISSING:  # type: ignore[attr-defined]
            defaults[field.name] = "<default_factory>"
        else:
            defaults[field.name] = "<required>"
    return defaults


def _enum_values(cls: type[enum.Enum]) -> dict[str, Any]:
    return {item.name: item.value for item in cls}


def _filter_map(data: dict[str, str], needle: str | None) -> dict[str, str]:
    if not needle:
        return dict(sorted(data.items()))
    lowered = needle.lower()
    return dict(sorted((key, value) for key, value in data.items()
                       if lowered in key.lower() or lowered in value.lower()))


def _literal_or_source(node: ast.AST | None) -> Any:
    if node is None:
        return "<required>"
    try:
        return ast.literal_eval(node)
    except Exception:
        return ast.unparse(node)


def _source_file(relative_path: str) -> Path | None:
    candidate = Path.cwd() / relative_path
    if candidate.exists():
        return candidate
    for parent in Path(__file__).resolve().parents:
        candidate = parent / relative_path
        if candidate.exists():
            return candidate
    return None


def _read_ast(relative_path: str) -> ast.Module | None:
    path = _source_file(relative_path)
    if path is None:
        return None
    return ast.parse(path.read_text(encoding="utf-8"))


def _source_dataclass_defaults(tree: ast.Module, class_name: str) -> dict[str, Any]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            defaults: dict[str, Any] = {}
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    defaults[item.target.id] = _literal_or_source(item.value)
            return defaults
    return {}


def _source_quant_policy(tree: ast.Module) -> dict[str, Any]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "QuantPolicy":
            values: dict[str, Any] = {}
            for item in node.body:
                if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                    values[item.targets[0].id] = _literal_or_source(item.value)
            return values
    return {}


def _eval_module_map_value(node: ast.AST) -> str:
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                parts.append("{...}")
            else:
                parts.append(ast.unparse(value))
        return "".join(parts)
    value = _literal_or_source(node)
    return str(value)


def _source_module_maps(tree: ast.Module) -> dict[str, dict[str, str]]:
    maps: dict[str, dict[str, str]] = {
        "MODULE_MAP": {},
        "CUSTOM_MODULE_MAP": {},
        "ASCEND_MODULE_MAP": {},
        "MACA_MODULE_MAP": {},
        "CAMB_MODULE_MAP": {},
    }
    constants = {"LMDEPLOY_PYTORCH_MODEL_PATH": "lmdeploy.pytorch.models"}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target = node.targets[0].id
            if target in constants:
                constants[target] = str(_literal_or_source(node.value))
            elif target in maps and isinstance(node.value, ast.Dict):
                for key_node, value_node in zip(node.value.keys, node.value.values):
                    if key_node is not None:
                        maps[target][str(_literal_or_source(key_node))] = _eval_module_map_value(value_node)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute) and call.func.attr == "update":
                base = call.func.value
                if isinstance(base, ast.Name) and base.id in maps and call.args and isinstance(call.args[0], ast.Dict):
                    for key_node, value_node in zip(call.args[0].keys, call.args[0].values):
                        if key_node is not None:
                            value = _eval_module_map_value(value_node)
                            for name, replacement in constants.items():
                                value = value.replace("{...}", replacement, 1)
                            maps[base.id][str(_literal_or_source(key_node))] = value
    return maps


def collect(args: argparse.Namespace) -> dict[str, Any]:
    _maybe_add_current_checkout()
    result: dict[str, Any] = {"imports": {}, "configs": {}, "module_maps": {}, "source_fallback": False}

    lmdeploy, error = _safe_import("lmdeploy")
    result["imports"]["lmdeploy"] = error or "ok"
    if lmdeploy is not None:
        result["lmdeploy_version"] = getattr(lmdeploy, "__version__", "unknown")

    messages, error = _safe_import("lmdeploy.messages")
    result["imports"]["lmdeploy.messages"] = error or "ok"
    if messages is not None:
        if args.backend in ("all", "pytorch") and hasattr(messages, "PytorchEngineConfig"):
            result["configs"]["PytorchEngineConfig"] = _dataclass_defaults(messages.PytorchEngineConfig)
        if args.backend in ("all", "turbomind") and hasattr(messages, "TurbomindEngineConfig"):
            result["configs"]["TurbomindEngineConfig"] = _dataclass_defaults(messages.TurbomindEngineConfig)
        if hasattr(messages, "QuantPolicy"):
            result["configs"]["QuantPolicy"] = _enum_values(messages.QuantPolicy)

    if not result["configs"]:
        tree = _read_ast("lmdeploy/messages.py")
        if tree is not None:
            result["source_fallback"] = True
            if args.backend in ("all", "pytorch"):
                result["configs"]["PytorchEngineConfig"] = _source_dataclass_defaults(tree, "PytorchEngineConfig")
            if args.backend in ("all", "turbomind"):
                result["configs"]["TurbomindEngineConfig"] = _source_dataclass_defaults(tree, "TurbomindEngineConfig")
            result["configs"]["QuantPolicy"] = _source_quant_policy(tree)

    if args.module_map:
        module_map, error = _safe_import("lmdeploy.pytorch.models.module_map")
        result["imports"]["lmdeploy.pytorch.models.module_map"] = error or "ok"
        if module_map is not None:
            result["module_maps"]["MODULE_MAP"] = _filter_map(getattr(module_map, "MODULE_MAP", {}), args.filter)
            result["module_maps"]["CUSTOM_MODULE_MAP"] = _filter_map(
                getattr(module_map, "CUSTOM_MODULE_MAP", {}), args.filter)
            device_maps = getattr(module_map, "DEVICE_SPECIAL_MODULE_MAP", {})
            result["module_maps"]["DEVICE_SPECIAL_MODULE_MAP"] = {
                str(device): _filter_map(mapping, args.filter)
                for device, mapping in sorted(device_maps.items())
            }
        if not result["module_maps"]:
            tree = _read_ast("lmdeploy/pytorch/models/module_map.py")
            if tree is not None:
                result["source_fallback"] = True
                maps = _source_module_maps(tree)
                result["module_maps"]["MODULE_MAP"] = _filter_map(maps["MODULE_MAP"], args.filter)
                result["module_maps"]["CUSTOM_MODULE_MAP"] = _filter_map(maps["CUSTOM_MODULE_MAP"], args.filter)
                result["module_maps"]["DEVICE_SPECIAL_MODULE_MAP"] = {
                    "ascend": _filter_map(maps["ASCEND_MODULE_MAP"], args.filter),
                    "maca": _filter_map(maps["MACA_MODULE_MAP"], args.filter),
                    "camb": _filter_map(maps["CAMB_MODULE_MAP"], args.filter),
                }

    return result


def print_text(result: dict[str, Any]) -> None:
    if "lmdeploy_version" in result:
        print(f"lmdeploy version: {result['lmdeploy_version']}")

    print("\nImports:")
    for name, status in result["imports"].items():
        print(f"  {name}: {status}")
    if result.get("source_fallback"):
        print("  source fallback: used local source files for unavailable imports")

    if result["configs"]:
        print("\nConfig defaults:")
        for config_name, fields in result["configs"].items():
            print(f"  {config_name}:")
            for key, value in fields.items():
                print(f"    {key}: {value}")

    if result["module_maps"]:
        print("\nModule maps:")
        for map_name, mapping in result["module_maps"].items():
            if isinstance(mapping, dict) and all(isinstance(value, str) for value in mapping.values()):
                print(f"  {map_name} ({len(mapping)} entries):")
                for key, value in mapping.items():
                    print(f"    {key}: {value}")
            else:
                print(f"  {map_name}:")
                for key, value in mapping.items():
                    print(f"    {key}: {len(value)} entries")
                    for sub_key, sub_value in value.items():
                        print(f"      {sub_key}: {sub_value}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect LMDeploy backend config dataclass defaults and PyTorch module-map registration keys "
                    "without loading models.")
    parser.add_argument("--backend", choices=("all", "pytorch", "turbomind"), default="all",
                        help="Config defaults to inspect.")
    parser.add_argument("--module-map", action="store_true",
                        help="Include PyTorch MODULE_MAP, CUSTOM_MODULE_MAP, and device-special maps.")
    parser.add_argument("--filter", metavar="TEXT",
                        help="Filter module-map keys/values by case-insensitive text.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = collect(args)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)
    failed_imports = [status for status in result["imports"].values() if status != "ok"]
    if failed_imports and not result.get("source_fallback"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
