#!/usr/bin/env python3
"""Safely inspect Dream Textures public backend API signatures.

The script is intentionally read-only: it performs no model downloads, does not
start Blender UI, and does not run generation. It can inspect an installed
`dream_textures` package or a supplied add-on source directory.
"""

from __future__ import annotations

import argparse
import enum
import importlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys
import types
from multiprocessing import current_process
from typing import Any


PUBLIC_DATACLASSES = [
    "GenerationArguments",
    "Prompt",
    "Model",
    "ControlNet",
    "GenerationResult",
    "PromptToImage",
    "ImageToImage",
    "Inpaint",
    "DepthToImage",
    "Outpaint",
    "Upscale",
]

MODEL_EXPORT_MODULES = {
    "ControlNet": "control_net",  # not re-exported by api.models in this Dream Textures release
}

BACKEND_METHODS = [
    "list_models",
    "list_controlnet_models",
    "list_schedulers",
    "draw_prompt",
    "draw_advanced",
    "draw_speed_optimizations",
    "draw_memory_optimizations",
    "draw_extra",
    "get_batch_size",
    "generate",
    "validate",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Dream Textures backend API signatures/enums without Blender UI or model downloads."
    )
    parser.add_argument(
        "--addon-dir",
        type=Path,
        default=None,
        help=(
            "Optional Dream Textures add-on source directory, or a parent directory containing "
            "a dream_textures package. If a direct source directory has another basename, it is "
            "loaded under the requested package name for inspection without creating symlinks, "
            "copies, or source mutations. If omitted, imports the installed dream_textures package."
        ),
    )
    parser.add_argument(
        "--package",
        default="dream_textures",
        help="Import package name to inspect (default: dream_textures).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a concise text report.",
    )
    return parser.parse_args()


def install_inspection_environment() -> None:
    """Set the minimum process state expected by backend-safe Dream Textures imports."""
    try:
        current_process().name = "__actor__"
    except Exception:
        pass
    os.environ.setdefault("BLENDER_VERSION", "3.4.0")
    os.environ.setdefault("BLENDER_OCIO_CONFIG", "")

    if "bpy" in sys.modules:
        return

    bpy = types.ModuleType("bpy")
    bpy.__dream_textures_inspection_stub__ = True

    class PropertyGroup:
        pass

    def pointer_property(*_args: Any, **_kwargs: Any) -> None:
        return None

    bpy.types = types.SimpleNamespace(PropertyGroup=PropertyGroup)
    bpy.props = types.SimpleNamespace(PointerProperty=pointer_property)
    bpy.app = types.SimpleNamespace(version=tuple(int(x) for x in os.environ["BLENDER_VERSION"].split(".")[:3]))
    bpy.utils = types.SimpleNamespace(resource_path=lambda _kind: "")
    sys.modules["bpy"] = bpy


def resolve_addon_dir(addon_dir: Path, package: str) -> tuple[Path, bool]:
    addon_dir = addon_dir.expanduser().resolve()
    nested = addon_dir / package
    if (nested / "__init__.py").is_file():
        return nested, False
    if (addon_dir / "__init__.py").is_file():
        # The official Blender add-on folder should normally be named dream_textures.
        # Some source checkouts use a different directory name; for inspection only,
        # load the package from __init__.py under the requested package name. No symlink,
        # copy, or source mutation is performed.
        return addon_dir, addon_dir.name != package
    raise FileNotFoundError(
        f"{addon_dir} is neither a package directory nor a parent containing {package}/__init__.py"
    )


def clear_package_modules(package: str) -> None:
    for name in list(sys.modules):
        if name == package or name.startswith(package + "."):
            del sys.modules[name]


def import_source_as_package(package: str, package_dir: Path) -> Any:
    clear_package_modules(package)
    spec = importlib.util.spec_from_file_location(
        package,
        package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"could not create import spec for {package_dir}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[package] = module
    spec.loader.exec_module(module)
    return module


def import_package(package: str, addon_dir: Path | None) -> tuple[Any, str]:
    if addon_dir is None:
        return importlib.import_module(package), "installed-package"

    package_dir, requires_alias = resolve_addon_dir(addon_dir, package)
    sys.path.insert(0, str(package_dir.parent))
    if requires_alias:
        return import_source_as_package(package, package_dir), "importlib-source"
    return importlib.import_module(package), "sys-path"


def signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:
        return f"<unavailable: {type(exc).__name__}: {exc}>"


def enum_values(cls: type[enum.Enum]) -> list[Any]:
    values: list[Any] = []
    for item in cls:
        row: dict[str, Any] = {"name": item.name, "value": item.value}
        if hasattr(item, "id"):
            row["id"] = item.id
        if hasattr(item, "text"):
            row["text"] = item.text
        if hasattr(item, "x"):
            row["x"] = item.x
        if hasattr(item, "y"):
            row["y"] = item.y
        if hasattr(item, "recommended_model"):
            try:
                row["recommended_model"] = item.recommended_model()
            except Exception as exc:
                row["recommended_model_error"] = repr(exc)
        values.append(row)
    return values


def inspect_public_api(package: str, source_mode: str) -> dict[str, Any]:
    api = importlib.import_module(f"{package}.api")
    api_models = importlib.import_module(f"{package}.api.models")
    gp_models = importlib.import_module(f"{package}.generator_process.models")
    image_utils = importlib.import_module(f"{package}.image_utils")

    dataclass_signatures: dict[str, str] = {}
    model_objects: dict[str, Any] = {}
    for name in PUBLIC_DATACLASSES:
        obj = getattr(api_models, name, None)
        if obj is None and name in MODEL_EXPORT_MODULES:
            module = importlib.import_module(f"{package}.api.models.{MODEL_EXPORT_MODULES[name]}")
            obj = getattr(module, name, None)
        if obj is not None:
            model_objects[name] = obj
            dataclass_signatures[name] = signature(obj)

    backend = getattr(api, "Backend", None)
    backend_methods: dict[str, str] = {}
    if backend is not None:
        backend_methods = {
            name: signature(getattr(backend, name))
            for name in BACKEND_METHODS
            if hasattr(backend, name)
        }

    inpaint = model_objects["Inpaint"]

    try:
        import numpy as np

        arr = np.zeros((4, 5, 3), dtype=np.float32)
        image_smoke: dict[str, Any] = {
            "size": list(image_utils.size(arr)),
            "channels": image_utils.channels(arr),
            "ensure_alpha_shape": list(image_utils.ensure_alpha(arr).shape),
        }
    except Exception as exc:
        image_smoke = {"error": f"{type(exc).__name__}: {exc}"}

    return {
        "source_mode": source_mode,
        "inspected_package": package,
        "backend_class_available": backend is not None,
        "backend_methods": backend_methods,
        "dataclass_signatures": dataclass_signatures,
        "task_names": {
            name: model_objects[name].name()
            for name in ["PromptToImage", "ImageToImage", "Inpaint", "DepthToImage", "Outpaint", "Upscale"]
            if name in model_objects and hasattr(model_objects[name], "name")
        },
        "enums": {
            "Inpaint.MaskSource": enum_values(inpaint.MaskSource),
            "SeamlessAxes": enum_values(getattr(api_models, "SeamlessAxes")),
            "StepPreviewMode": enum_values(getattr(api_models, "StepPreviewMode")),
            "Scheduler": enum_values(getattr(gp_models, "Scheduler")),
            "ModelType": enum_values(getattr(gp_models, "ModelType")),
            "CPUOffload": enum_values(getattr(gp_models, "CPUOffload")),
            "ModelConfig": enum_values(getattr(gp_models, "ModelConfig")),
        },
        "optimizations_signature": signature(getattr(gp_models, "Optimizations")),
        "checkpoint_signature": signature(getattr(gp_models, "Checkpoint")),
        "image_utils_smoke": image_smoke,
        "notes": [
            "No Blender UI runtime was imported intentionally.",
            "No Diffusers pipeline, model cache, network, or generation path was executed.",
        ],
    }


def print_text(data: dict[str, Any]) -> None:
    print("Dream Textures public API inspection")
    print(f"source_mode: {data['source_mode']}")
    print(f"inspected_package: {data['inspected_package']}")
    print(f"backend_class_available: {data['backend_class_available']}")
    print("\nBackend methods:")
    for name, sig in data["backend_methods"].items():
        print(f"  {name}{sig}")
    print("\nDataclass/task signatures:")
    for name, sig in data["dataclass_signatures"].items():
        print(f"  {name}{sig}")
    print("\nEnum values:")
    for enum_name, values in data["enums"].items():
        rendered = ", ".join(str(v.get("value")) for v in values)
        print(f"  {enum_name}: {rendered}")
    print(f"\nOptimizations{data['optimizations_signature']}")
    print(f"Checkpoint{data['checkpoint_signature']}")
    print(f"image_utils_smoke: {data['image_utils_smoke']}")
    for note in data["notes"]:
        print(f"note: {note}")


def main() -> int:
    args = parse_args()
    install_inspection_environment()
    try:
        _pkg, source_mode = import_package(args.package, args.addon_dir)
        data = inspect_public_api(args.package, source_mode)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2, sort_keys=True))
        else:
            print(f"inspection failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"ok": True, **data}, indent=2, sort_keys=True))
    else:
        print_text(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
