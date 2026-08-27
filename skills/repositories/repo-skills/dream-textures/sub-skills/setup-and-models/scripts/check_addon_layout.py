#!/usr/bin/env python3
"""Static Dream Textures add-on layout checker.

This script is intentionally safe: it only reads files and directories. It does
not import Blender, import the add-on package, install dependencies, download
models, contact Hugging Face/DreamStudio, or execute add-on scripts.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
from typing import Any

EXPECTED_REQUIREMENTS = {
    "requirements/win-linux-cuda.txt": {
        "label": "Linux/Windows CUDA",
        "needles": ["diffusers==0.27.2", "torch==2.3.1", "cu118", "controlnet-aux==0.0.7"],
    },
    "requirements/linux-rocm.txt": {
        "label": "Linux ROCm",
        "needles": ["diffusers==0.27.2", "torch==2.3.1", "rocm6.1", "controlnet-aux==0.0.7"],
    },
    "requirements/mac-mps-cpu.txt": {
        "label": "macOS MPS/CPU",
        "needles": ["diffusers==0.27.2", "torch==2.3.1", "huggingface_hub"],
    },
    "requirements/win-dml.txt": {
        "label": "Windows DirectML",
        "needles": ["diffusers==0.27.2", "torch-directml", "torch==2.3.1"],
    },
}

BASIC_FILES = [
    "__init__.py",
    "preferences.py",
    "operators/install_dependencies.py",
    "generator_process/models/model_config.py",
    "generator_process/models/model_type.py",
]

KEY_DEPENDENCY_HINTS = [
    "torch",
    "diffusers",
    "huggingface_hub",
    "transformers",
    "accelerate",
    "controlnet_aux",
]


def literal_assignment(tree: ast.AST, name: str) -> Any | None:
    """Return ast.literal_eval(value) for a simple assignment if present."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        return None
    return None


def add(result: dict[str, list[dict[str, str]]], severity: str, message: str, path: Path | None = None) -> None:
    item = {"message": message}
    if path is not None:
        item["path"] = str(path)
    result[severity.lower()].append(item)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def inspect_python_metadata(addon_dir: Path, result: dict[str, Any]) -> None:
    init_py = addon_dir / "__init__.py"
    if not init_py.exists():
        return
    try:
        tree = ast.parse(read_text(init_py), filename=str(init_py))
    except SyntaxError as exc:
        add(result, "error", f"Could not parse __init__.py: {exc}", init_py)
        return

    bl_info = literal_assignment(tree, "bl_info")
    if isinstance(bl_info, dict):
        result["facts"]["bl_info"] = bl_info
        if bl_info.get("name") != "Dream Textures":
            add(result, "warn", f"Unexpected bl_info name: {bl_info.get('name')!r}", init_py)
    else:
        add(result, "warn", "Could not statically read bl_info from __init__.py", init_py)

    req_items = literal_assignment(tree, "requirements_path_items")
    if isinstance(req_items, (list, tuple)):
        advertised = []
        for item in req_items:
            if isinstance(item, (list, tuple)) and item:
                advertised.append(str(item[0]))
        result["facts"]["advertised_requirement_files"] = advertised
        for rel in advertised:
            if not (addon_dir / rel).exists():
                add(result, "warn", f"Requirement file is advertised by add-on registration but missing: {rel}", addon_dir / rel)
    else:
        add(result, "warn", "Could not statically read requirements_path_items from __init__.py", init_py)


def inspect_basic_layout(addon_dir: Path, result: dict[str, Any]) -> None:
    if not addon_dir.exists():
        add(result, "error", "Add-on directory does not exist", addon_dir)
        return
    if not addon_dir.is_dir():
        add(result, "error", "Path is not a directory", addon_dir)
        return

    if addon_dir.name != "dream_textures":
        add(
            result,
            "warn",
            "Blender add-on package folder is usually expected to be named 'dream_textures'; rename source/extracted folders that use hyphens or wrapper names.",
            addon_dir,
        )

    missing = [rel for rel in BASIC_FILES if not (addon_dir / rel).exists()]
    if missing:
        for rel in missing:
            add(result, "error", f"Missing basic Dream Textures file: {rel}", addon_dir / rel)
        nested = addon_dir / "dream_textures" / "__init__.py"
        if nested.exists():
            add(result, "warn", "This looks like a parent folder; try checking the nested 'dream_textures' directory instead.", nested.parent)
    else:
        add(result, "info", "Basic Dream Textures source files are present", addon_dir)


def inspect_requirements(addon_dir: Path, result: dict[str, Any]) -> None:
    req_summary: dict[str, Any] = {}
    for rel, spec in EXPECTED_REQUIREMENTS.items():
        path = addon_dir / rel
        if not path.exists():
            add(result, "error", f"Missing expected dependency variant: {rel}", path)
            continue
        text = read_text(path)
        missing_needles = [needle for needle in spec["needles"] if needle not in text]
        req_summary[rel] = {
            "label": spec["label"],
            "line_count": len([line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]),
            "missing_expected_markers": missing_needles,
        }
        if missing_needles:
            add(result, "warn", f"Requirement variant {rel} is present but missing expected markers: {', '.join(missing_needles)}", path)
    result["facts"]["requirements"] = req_summary


def inspect_python_dependencies(addon_dir: Path, result: dict[str, Any]) -> None:
    deps = addon_dir / ".python_dependencies"
    state: dict[str, Any] = {"exists": deps.exists(), "entry_count": None, "key_package_hints": {}}
    result["facts"]["python_dependencies"] = state
    if not deps.exists():
        add(result, "warn", ".python_dependencies is missing; release may be incomplete or source dependencies were not installed", deps)
        return
    if not deps.is_dir():
        add(result, "error", ".python_dependencies exists but is not a directory", deps)
        return

    entries = list(deps.iterdir())
    state["entry_count"] = len(entries)
    visible_entries = [p for p in entries if not p.name.startswith(".")]
    if len(entries) <= 2 or not visible_entries:
        add(
            result,
            "warn",
            ".python_dependencies appears effectively empty by Dream Textures' own setup heuristic; source installs need backend packages here and ordinary users should prefer a prebuilt release",
            deps,
        )
    else:
        add(result, "info", f".python_dependencies contains {len(entries)} entries", deps)

    lower_names = {p.name.lower().replace("-", "_") for p in entries}
    for package in KEY_DEPENDENCY_HINTS:
        present = any(name == package or name.startswith(package + ".") or name.startswith(package + "_") for name in lower_names)
        state["key_package_hints"][package] = present
    missing_hints = [pkg for pkg, present in state["key_package_hints"].items() if not present]
    if visible_entries and missing_hints:
        add(result, "warn", "Could not see expected local dependency folders/metadata for: " + ", ".join(missing_hints), deps)


def build_report(addon_dir: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "addon_dir": str(addon_dir),
        "status": "unknown",
        "error": [],
        "warn": [],
        "info": [],
        "facts": {},
    }
    inspect_basic_layout(addon_dir, result)
    inspect_python_metadata(addon_dir, result)
    inspect_requirements(addon_dir, result)
    inspect_python_dependencies(addon_dir, result)
    if result["error"]:
        result["status"] = "error"
    elif result["warn"]:
        result["status"] = "warn"
    else:
        result["status"] = "ok"
    return result


def print_text(report: dict[str, Any]) -> None:
    print(f"Dream Textures add-on layout check: {report['status'].upper()}")
    print(f"Add-on directory: {report['addon_dir']}")
    bl_info = report.get("facts", {}).get("bl_info")
    if isinstance(bl_info, dict):
        print(f"Declared add-on: {bl_info.get('name', '<unknown>')} version={bl_info.get('version', '<unknown>')} blender={bl_info.get('blender', '<unknown>')}")
    advertised = report.get("facts", {}).get("advertised_requirement_files")
    if advertised:
        print("Advertised requirement files: " + ", ".join(advertised))
    deps = report.get("facts", {}).get("python_dependencies", {})
    if deps:
        print(f".python_dependencies: exists={deps.get('exists')} entries={deps.get('entry_count')}")
        hints = deps.get("key_package_hints") or {}
        if hints:
            present = [name for name, ok in hints.items() if ok]
            missing = [name for name, ok in hints.items() if not ok]
            print("Dependency hints present: " + (", ".join(present) if present else "none detected"))
            print("Dependency hints missing: " + (", ".join(missing) if missing else "none"))
    for severity in ["error", "warn", "info"]:
        for item in report[severity]:
            path = f" [{item['path']}]" if "path" in item else ""
            print(f"{severity.upper()}: {item['message']}{path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely inspect a Dream Textures Blender add-on directory layout without importing or installing anything.")
    parser.add_argument("addon_dir", type=Path, help="Path to the Dream Textures add-on package folder, usually named dream_textures")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text")
    args = parser.parse_args(argv)

    report = build_report(args.addon_dir.expanduser().resolve())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print_text(report)
    return 2 if report["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
