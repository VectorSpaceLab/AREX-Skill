#!/usr/bin/env python3
"""Safely inspect a ComfyUI-LTXVideo custom-node checkout.

This script imports ComfyUI source/packages and the custom-node package by file
spec, then reports node mapping counts and selected node metadata. It does not
start ComfyUI, download models, run workflow JSONs, or write files.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect ComfyUI-LTXVideo custom-node mappings without running generation."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Path to the ComfyUI-LTXVideo custom-node folder (default: current directory).",
    )
    parser.add_argument(
        "--comfyui-root",
        type=Path,
        help="Optional path to the ComfyUI source root to add to sys.path before import.",
    )
    parser.add_argument(
        "--node",
        action="append",
        default=[],
        help="Specific node id to probe; may be passed multiple times. Defaults to a representative set.",
    )
    parser.add_argument(
        "--no-input-probe",
        action="store_true",
        help="Do not call INPUT_TYPES or define_schema on selected nodes.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text summary.",
    )
    return parser


def probe_torch() -> dict[str, Any]:
    try:
        import torch  # type: ignore[import-not-found]
    except Exception as exc:
        return {"imported": False, "error": f"{type(exc).__name__}: {exc}"}

    info: dict[str, Any] = {
        "imported": True,
        "version": getattr(torch, "__version__", None),
        "cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }
    if info["cuda_available"]:
        try:
            info["device0"] = torch.cuda.get_device_name(0)
            info["capability0"] = list(torch.cuda.get_device_capability(0))
        except Exception as exc:
            info["device_error"] = f"{type(exc).__name__}: {exc}"
    return info


def import_optional(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {"imported": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"imported": True, "module_file": getattr(module, "__file__", None)}


def load_repo_package(repo_root: Path) -> Any:
    init_path = repo_root / "__init__.py"
    if not init_path.exists():
        raise FileNotFoundError(f"{repo_root} does not contain __init__.py")
    spec = importlib.util.spec_from_file_location(
        "comfyui_ltxvideo_inspected",
        init_path,
        submodule_search_locations=[str(repo_root)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not create import spec for {init_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def safe_node_probe(node_id: str, cls: type, call_inputs: bool) -> dict[str, Any]:
    out: dict[str, Any] = {
        "node_id": node_id,
        "class_name": getattr(cls, "__name__", None),
        "module": getattr(cls, "__module__", None),
        "category": getattr(cls, "CATEGORY", None),
        "title": getattr(cls, "TITLE", None),
        "function": getattr(cls, "FUNCTION", None),
        "return_types": getattr(cls, "RETURN_TYPES", None),
        "return_names": getattr(cls, "RETURN_NAMES", None),
        "description": getattr(cls, "DESCRIPTION", None),
    }
    if call_inputs and hasattr(cls, "INPUT_TYPES"):
        try:
            inputs = cls.INPUT_TYPES()
            out["input_sections"] = sorted(inputs.keys()) if isinstance(inputs, dict) else str(type(inputs))
            if isinstance(inputs, dict):
                out["required_inputs"] = sorted((inputs.get("required") or {}).keys())
                out["optional_inputs"] = sorted((inputs.get("optional") or {}).keys())
        except Exception as exc:
            out["input_error"] = f"{type(exc).__name__}: {exc}"
    if call_inputs and hasattr(cls, "define_schema"):
        try:
            schema = cls.define_schema()
            out["schema_node_id"] = getattr(schema, "node_id", None)
            out["schema_category"] = getattr(schema, "category", None)
            out["schema_description"] = getattr(schema, "description", None)
        except Exception as exc:
            out["schema_error"] = f"{type(exc).__name__}: {exc}"
    return out


def inspect_package(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    repo_root = args.repo_root.resolve()
    if args.comfyui_root:
        sys.path.insert(0, str(args.comfyui_root.resolve()))

    report: dict[str, Any] = {
        "ok": False,
        "python": sys.version.split()[0],
        "repo_root_name": repo_root.name,
        "comfyui_root_name": args.comfyui_root.name if args.comfyui_root else None,
        "torch": probe_torch(),
        "imports": {
            "comfy": import_optional("comfy"),
            "comfy_extras": import_optional("comfy_extras"),
            "comfy_api.latest": import_optional("comfy_api.latest"),
        },
        "repo": {},
        "errors": [],
    }

    try:
        module = load_repo_package(repo_root)
        mappings = getattr(module, "NODE_CLASS_MAPPINGS")
        display = getattr(module, "NODE_DISPLAY_NAME_MAPPINGS")
        report["repo"] = {
            "module_name": getattr(module, "__name__", None),
            "node_class_mappings": len(mappings),
            "node_display_name_mappings": len(display),
            "web_directory": getattr(module, "WEB_DIRECTORY", None),
            "first_nodes": sorted(mappings.keys())[:20],
        }
        default_nodes = [
            "LTXVBaseSampler",
            "LTXVGemmaCLIPModelLoader",
            "LTXVAudioOnlyModel",
            "LTXVHDRDecodePostprocess",
            "LTXVSparseTrackEditor",
            "LTXQ8Patch",
        ]
        selected = args.node or [node for node in default_nodes if node in mappings]
        report["repo"]["selected_nodes"] = [
            safe_node_probe(node, mappings[node], not args.no_input_probe)
            if node in mappings
            else {"node_id": node, "error": "not in NODE_CLASS_MAPPINGS"}
            for node in selected
        ]
        report["ok"] = True
        return 0, report
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        return 1, report


def print_text(report: dict[str, Any]) -> None:
    print("OK" if report["ok"] else "FAILED")
    print(f"python: {report['python']}")
    torch_info = report["torch"]
    if torch_info.get("imported"):
        print(
            "torch: "
            f"{torch_info.get('version')} cuda={torch_info.get('cuda_version')} "
            f"available={torch_info.get('cuda_available')} devices={torch_info.get('device_count')}"
        )
    else:
        print(f"torch import failed: {torch_info.get('error')}")
    for name, info in report["imports"].items():
        print(f"{name}: {'ok' if info.get('imported') else 'failed'}")
        if info.get("error"):
            print(f"  {info['error']}")
    if report.get("repo"):
        repo = report["repo"]
        print(f"node_class_mappings: {repo.get('node_class_mappings')}")
        print(f"node_display_name_mappings: {repo.get('node_display_name_mappings')}")
        print(f"web_directory: {repo.get('web_directory')}")
        for node in repo.get("selected_nodes", []):
            print(f"- {node.get('node_id')}: {node.get('class_name')} ({node.get('category') or node.get('schema_category')})")
    for error in report.get("errors", []):
        print(f"error: {error}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, report = inspect_package(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print_text(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
