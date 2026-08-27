#!/usr/bin/env python3
"""Read-only Krita AI Diffusion environment checker.

The default static mode parses local source files when available and avoids
import side effects. Use --strict to import key modules in an installed package
or development checkout.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import json
import sys
from pathlib import Path
from typing import Any


MODULES = [
    "ai_diffusion",
    "ai_diffusion.backend.api",
    "ai_diffusion.backend.resources",
    "ai_diffusion.backend.workflow",
    "ai_diffusion.backend.comfy_workflow",
    "ai_diffusion.backend.comfy_client",
    "ai_diffusion.backend.cloud_client",
    "ai_diffusion.backend.server",
    "ai_diffusion.image",
    "ai_diffusion.settings",
    "ai_diffusion.style",
    "ai_diffusion.text",
    "ai_diffusion.model.custom_workflow",
    "ai_diffusion.model.model",
]


def find_repo_root(start: Path) -> Path | None:
    for path in [start, *start.parents]:
        if (path / "ai_diffusion" / "__init__.py").exists():
            return path
    return None


def add_local_repo_to_path() -> Path | None:
    candidates = [Path.cwd(), Path(__file__).resolve()]
    for candidate in candidates:
        root = find_repo_root(candidate if candidate.is_dir() else candidate.parent)
        if root is not None:
            root_text = str(root)
            if root_text not in sys.path:
                sys.path.insert(0, root_text)
            return root
    return None


def static_string(path: Path, name: str) -> str | None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except OSError:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        return node.value.value
    return None


def enum_values(path: Path, enum_name: str) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except OSError:
        return []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == enum_name:
            names = []
            for child in node.body:
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name) and not target.id.startswith("_"):
                            names.append(target.id)
            return names
    return []


def report_item(status: str, name: str, detail: dict[str, Any] | str | None = None) -> None:
    print(f"[{status}] {name}")
    if detail is not None:
        if isinstance(detail, str):
            print(detail)
        else:
            print(json.dumps(detail, indent=2, sort_keys=True))


def run_static(repo_root: Path | None) -> bool:
    ok = True
    if repo_root is None:
        report_item("warn", "static_source", "No local ai_diffusion source tree found near the current directory.")
        return True

    init_py = repo_root / "ai_diffusion" / "__init__.py"
    resources_py = repo_root / "ai_diffusion" / "backend" / "resources.py"
    api_py = repo_root / "ai_diffusion" / "backend" / "api.py"
    model_py = repo_root / "ai_diffusion" / "model" / "model.py"
    settings_py = repo_root / "ai_diffusion" / "settings.py"

    plugin_version = static_string(init_py, "__version__")
    resource_version = static_string(resources_py, "version")
    websockets_src = repo_root / "ai_diffusion" / "websockets" / "src"

    detail = {
        "plugin_version": plugin_version,
        "resource_catalog_version": resource_version,
        "vendored_websockets_present": websockets_src.exists(),
        "workflow_kinds": enum_values(api_py, "WorkflowKind"),
        "workspaces": enum_values(model_py, "Workspace"),
        "server_modes": enum_values(settings_py, "ServerMode"),
    }
    if not plugin_version or not resource_version:
        ok = False
    report_item("pass" if ok else "fail", "static_source", detail)
    return ok


def ensure_qcore_application() -> None:
    try:
        from PyQt5.QtCore import QCoreApplication
    except Exception:
        return
    if QCoreApplication.instance() is None:
        QCoreApplication([])


def run_imports(strict: bool) -> bool:
    ensure_qcore_application()
    ok = True
    for module_name in MODULES:
        try:
            module = importlib.import_module(module_name)
            detail = {"module": module_name, "file_known": bool(getattr(module, "__file__", None))}
            if module_name == "ai_diffusion":
                detail["version"] = getattr(module, "__version__", None)
            if module_name == "ai_diffusion.backend.resources":
                detail["resource_catalog_version"] = getattr(module, "version", None)
            report_item("pass", module_name, detail)
        except Exception as exc:  # noqa: BLE001 - diagnostic script
            ok = False
            report_item("fail" if strict else "warn", module_name, {"error": f"{type(exc).__name__}: {exc}"})
            if strict:
                continue
    return ok


def run_round_trip() -> bool:
    try:
        from ai_diffusion.backend.api import CheckpointInput, ConditioningInput, ImageInput, SamplingInput, WorkflowInput, WorkflowKind
        from ai_diffusion.backend.resources import Arch, version as resource_version
        from ai_diffusion.image import Extent
        import ai_diffusion

        extent = Extent(64, 72)
        work = WorkflowInput(
            kind=WorkflowKind.generate,
            images=ImageInput.from_extent(extent),
            models=CheckpointInput("example.safetensors", Arch.sd15),
            sampling=SamplingInput("dpmpp_2m_sde_gpu", "normal", 7.0, 20, seed=1),
            conditioning=ConditioningInput("smoke test"),
        )
        data = work.to_dict(image_format=None)
        back = WorkflowInput.from_dict(data)
        detail = {
            "round_trip_kind": back.kind.name,
            "extent_multiple": list(extent.multiple_of(8)),
            "plugin_version": ai_diffusion.__version__,
            "resource_version": resource_version,
            "workflow_kinds": [kind.name for kind in WorkflowKind],
        }
        report_item("pass", "workflowinput_round_trip", detail)
        return True
    except Exception as exc:  # noqa: BLE001
        report_item("fail", "workflowinput_round_trip", {"error": f"{type(exc).__name__}: {exc}"})
        return False


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Read-only Krita AI Diffusion environment checker.")
    parser.add_argument("--static-only", action="store_true", help="Only parse nearby source files; do not import ai_diffusion.")
    parser.add_argument("--strict", action="store_true", help="Import modules and fail if any selected check fails.")
    args = parser.parse_args(argv)

    repo_root = find_repo_root(Path.cwd()) or find_repo_root(Path(__file__).resolve().parent)
    ok = run_static(repo_root)
    if not args.static_only:
        add_local_repo_to_path()
        ok = run_imports(args.strict) and ok
        ok = run_round_trip() and ok

    print("guidance:")
    print("- This helper is offline-only: no Krita launch, no ComfyUI/cloud connection, no model downloads, no generation.")
    print("- If ai_diffusion import fails with bundled websockets missing, use a release package or initialize the source checkout's vendored submodule.")
    print("- Set QT_QPA_PLATFORM=offscreen for headless import checks.")
    print("- Use sub-skills/server-resources for backend URL/model checks and sub-skills/inference-workflows for payload schema debugging.")
    return 0 if ok or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
