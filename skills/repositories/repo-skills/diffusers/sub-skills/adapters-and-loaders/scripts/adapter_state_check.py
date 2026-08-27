#!/usr/bin/env python3
"""No-download Diffusers adapter/checkpoint preflight checks."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
from pathlib import Path


EXPECTED_EXTENSIONS = {
    "lora": {".safetensors", ".bin", ".pt", ".pth"},
    "textual-inversion": {".safetensors", ".bin", ".pt", ".pth"},
    "ip-adapter": {".safetensors", ".bin", ".pt", ".pth"},
    "t2i-adapter": {".safetensors", ".bin", ".json", ""},
    "controlnet": {".safetensors", ".bin", ".json", ""},
    "single-file": {".safetensors", ".ckpt", ".pt", ".pth", ".gguf"},
}

DEFAULT_CLASSES = [
    "StableDiffusionPipeline",
    "StableDiffusionXLPipeline",
    "ControlNetModel",
    "T2IAdapter",
]

METHODS = [
    "load_lora_weights",
    "set_adapters",
    "fuse_lora",
    "unfuse_lora",
    "unload_lora_weights",
    "delete_adapters",
    "get_list_adapters",
    "get_active_adapters",
    "enable_lora_hotswap",
    "load_lora_adapter",
    "load_textual_inversion",
    "maybe_convert_prompt",
    "load_ip_adapter",
    "set_ip_adapter_scale",
    "unload_ip_adapter",
    "from_single_file",
    "from_pretrained",
]


def import_status(module_name: str) -> dict:
    try:
        module = importlib.import_module(module_name)
    except Exception as error:
        return {"available": False, "error": f"{type(error).__name__}: {error}"}
    return {"available": True, "version": getattr(module, "__version__", None)}


def signature_text(obj) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as error:
        return f"<signature unavailable: {type(error).__name__}: {error}>"


def class_report(class_name: str) -> dict:
    try:
        diffusers = importlib.import_module("diffusers")
        cls = getattr(diffusers, class_name)
    except Exception as error:
        return {"available": False, "error": f"{type(error).__name__}: {error}"}

    methods = {}
    for method_name in METHODS:
        if hasattr(cls, method_name):
            methods[method_name] = signature_text(getattr(cls, method_name))
    return {
        "available": True,
        "module": getattr(cls, "__module__", None),
        "init": signature_text(cls) if callable(cls) else None,
        "methods": methods,
    }


def module_report(module_name: str) -> dict:
    try:
        module = importlib.import_module(module_name)
    except Exception as error:
        return {"available": False, "error": f"{type(error).__name__}: {error}"}
    public = [name for name in dir(module) if not name.startswith("_")]
    return {"available": True, "public_sample": public[:80]}


def path_report(path_text: str, expect_kind: str | None) -> dict:
    path = Path(path_text).expanduser()
    exists = path.exists()
    report = {
        "path": path_text,
        "exists": exists,
        "is_file": path.is_file() if exists else False,
        "is_dir": path.is_dir() if exists else False,
    }
    if not exists:
        report["ok"] = False
        report["error"] = "path does not exist"
        return report

    if path.is_file():
        suffixes = "".join(path.suffixes[-2:]) if path.name.endswith(".index.json") else path.suffix.lower()
        report["extension"] = suffixes
        if expect_kind:
            allowed = EXPECTED_EXTENSIONS[expect_kind]
            report["expected_extensions"] = sorted(allowed)
            report["extension_ok"] = suffixes in allowed or path.suffix.lower() in allowed
    else:
        children = sorted(child.name for child in path.iterdir())[:100]
        report["children_sample"] = children
        if expect_kind:
            allowed = EXPECTED_EXTENSIONS[expect_kind]
            matches = [name for name in children if Path(name).suffix.lower() in allowed]
            report["matching_children"] = matches
            report["extension_ok"] = bool(matches) or expect_kind in {"t2i-adapter", "controlnet"}

    report["ok"] = report.get("extension_ok", True)
    return report


def config_report(config_text: str | None) -> dict | None:
    if config_text is None:
        return None
    path = Path(config_text).expanduser()
    exists = path.exists()
    report = {"path": config_text, "exists": exists, "is_dir": path.is_dir() if exists else False}
    if exists and path.is_dir():
        json_files = sorted(str(child.relative_to(path)) for child in path.rglob("*.json"))[:100]
        report["json_files_sample"] = json_files
        report["has_model_index"] = (path / "model_index.json").exists()
        report["ok"] = bool(json_files)
    elif exists:
        report["ok"] = path.suffix.lower() in {".json", ".yaml", ".yml"}
    else:
        report["ok"] = False
        report["error"] = "config path does not exist"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Diffusers adapter/checkpoint paths and import surfaces without downloads.")
    parser.add_argument("--path", action="append", default=[], help="Local adapter/checkpoint path to validate. Repeatable.")
    parser.add_argument(
        "--expect-kind",
        choices=sorted(EXPECTED_EXTENSIONS),
        help="Expected kind for --path extension checks.",
    )
    parser.add_argument("--config", help="Local config path for single-file loading checks.")
    parser.add_argument("--class", dest="classes", action="append", default=[], help="Diffusers public class to inspect. Repeatable.")
    parser.add_argument("--module", action="append", default=[], help="Python module to import and summarize. Repeatable.")
    parser.add_argument("--require-import", action="append", default=[], help="Module that must import successfully. Repeatable.")
    parser.add_argument("--no-default-classes", action="store_true", help="Only inspect classes passed with --class.")
    args = parser.parse_args()

    required_imports = ["diffusers", *args.require_import]
    result = {
        "imports": {module_name: import_status(module_name) for module_name in required_imports},
        "paths": [path_report(path, args.expect_kind) for path in args.path],
        "config": config_report(args.config),
        "classes": {},
        "modules": {},
    }

    class_names = args.classes if args.no_default_classes else [*DEFAULT_CLASSES, *args.classes]
    for class_name in dict.fromkeys(class_names):
        result["classes"][class_name] = class_report(class_name)

    for module_name in args.module:
        result["modules"][module_name] = module_report(module_name)

    ok = all(item["available"] for item in result["imports"].values())
    ok = ok and all(item.get("ok", False) for item in result["paths"])
    if result["config"] is not None:
        ok = ok and result["config"].get("ok", False)
    result["ok"] = ok

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
