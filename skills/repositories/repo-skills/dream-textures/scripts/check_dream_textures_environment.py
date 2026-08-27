#!/usr/bin/env python3
"""Safe Dream Textures environment diagnostic.

This helper is intentionally read-only. It does not import Blender UI modules,
install dependencies, download models, contact Hugging Face/DreamStudio, or run
Stable Diffusion. It checks whether an add-on folder/package is visible and
summarizes optional Python/backend modules that full Dream Textures workflows
may need.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

OPTIONAL_MODULES = [
    "bpy",
    "numpy",
    "PIL",
    "torch",
    "diffusers",
    "transformers",
    "accelerate",
    "huggingface_hub",
    "controlnet_aux",
    "torch_directml",
    "cv2",
]

EXPECTED_FILES = [
    "__init__.py",
    "preferences.py",
    "diffusers_backend.py",
    "api/models/generation_arguments.py",
    "generator_process/models/model_type.py",
    "requirements/win-linux-cuda.txt",
    "requirements/linux-rocm.txt",
    "requirements/mac-mps-cpu.txt",
    "requirements/win-dml.txt",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Dream Textures add-on/package visibility and optional backend modules without running generation."
    )
    parser.add_argument(
        "--addon-dir",
        type=Path,
        help="Optional Dream Textures add-on directory to inspect statically. Use the actual Blender add-on folder when available.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text report.")
    return parser.parse_args()


def module_status(name: str) -> dict[str, Any]:
    spec = importlib.util.find_spec(name)
    row: dict[str, Any] = {"module": name, "available": spec is not None}
    if spec is not None:
        row["origin_kind"] = "package" if spec.submodule_search_locations else "module"
    return row


def inspect_addon_dir(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    root = path.expanduser().resolve()
    files = {rel: (root / rel).exists() for rel in EXPECTED_FILES}
    deps = root / ".python_dependencies"
    dep_entries = []
    if deps.is_dir():
        try:
            dep_entries = sorted(p.name for p in deps.iterdir() if not p.name.startswith("."))[:25]
        except OSError:
            dep_entries = []
    info: dict[str, Any] = {
        "exists": root.exists(),
        "is_directory": root.is_dir(),
        "folder_name": root.name,
        "folder_name_ok_for_blender_import": root.name == "dream_textures",
        "expected_files": files,
        "missing_expected_files": [rel for rel, ok in files.items() if not ok],
        "python_dependencies_exists": deps.exists(),
        "python_dependencies_non_hidden_entry_count": len(dep_entries),
        "python_dependencies_sample_entries": dep_entries,
    }
    init_file = root / "__init__.py"
    if init_file.exists():
        text = init_file.read_text(encoding="utf-8", errors="replace")
        info["bl_info_mentions"] = {
            "Dream Textures": "Dream Textures" in text,
            "version_0_4_1": "(0, 4, 1)" in text,
            "blender_3_1_0": "(3, 1, 0)" in text,
        }
    return info


def torch_backend_probe() -> dict[str, Any]:
    if importlib.util.find_spec("torch") is None:
        return {"torch_available": False}
    try:
        import torch  # type: ignore

        out: dict[str, Any] = {
            "torch_available": True,
            "torch_version": getattr(torch, "__version__", None),
            "cuda_version": getattr(getattr(torch, "version", None), "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "mps_available": bool(getattr(getattr(torch, "backends", None), "mps", None) and torch.backends.mps.is_available()),
        }
        if out["cuda_available"]:
            out["cuda_device_name_0"] = torch.cuda.get_device_name(0)
        return out
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"torch_available": True, "probe_error": f"{type(exc).__name__}: {exc}"}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "executable_basename": Path(sys.executable).name,
        "blender_executable_on_path": shutil.which("blender") is not None,
        "addon_dir": inspect_addon_dir(args.addon_dir),
        "modules": [module_status(name) for name in OPTIONAL_MODULES],
        "torch_backends": torch_backend_probe(),
        "notes": [
            "This helper is a safe diagnostic, not proof that a full image generation workflow can run.",
            "Full local generation also needs Blender, a matching requirement variant, model weights, and enough memory/VRAM.",
            "DreamStudio workflows require a valid API key and network access.",
        ],
    }


def print_text(report: dict[str, Any]) -> None:
    print("Dream Textures environment diagnostic")
    print(f"Python: {report['python']} ({report['executable_basename']})")
    print(f"Blender executable on PATH: {report['blender_executable_on_path']}")
    addon = report.get("addon_dir")
    if addon is not None:
        print("\nAdd-on directory:")
        print(f"  exists: {addon['exists']}  is_directory: {addon['is_directory']}  folder_name: {addon['folder_name']}")
        print(f"  folder name ok for Blender import: {addon['folder_name_ok_for_blender_import']}")
        if addon["missing_expected_files"]:
            print("  missing expected files:")
            for rel in addon["missing_expected_files"]:
                print(f"    - {rel}")
        else:
            print("  expected core files: present")
        print(
            "  .python_dependencies: "
            f"exists={addon['python_dependencies_exists']} entries={addon['python_dependencies_non_hidden_entry_count']}"
        )
    print("\nPython modules:")
    for row in report["modules"]:
        print(f"  {row['module']}: {'available' if row['available'] else 'missing'}")
    print("\nTorch/backend probe:")
    for key, value in report["torch_backends"].items():
        print(f"  {key}: {value}")
    print("\nNotes:")
    for note in report["notes"]:
        print(f"  - {note}")


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
