#!/usr/bin/env python3
"""Safely inspect MedRAX orchestration files and lightweight imports.

This checker deliberately avoids importing ``main`` (which imports the UI and
all tool modules) and never constructs ChatOpenAI, Agent, or a model-backed
tool. It parses signatures from source when available and imports only the
small orchestration modules.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any


EXPECTED_TOOLS = [
    "ChestXRayClassifierTool",
    "ChestXRaySegmentationTool",
    "LlavaMedTool",
    "XRayVQATool",
    "ChestXRayReportGeneratorTool",
    "XRayPhraseGroundingTool",
    "ChestXRayGeneratorTool",
    "ImageVisualizerTool",
    "DicomProcessorTool",
]


def _signature_from_ast(path: Path, function_name: str) -> str | None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        return f"unavailable: {type(exc).__name__}: {exc}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            args = []
            positional = list(node.args.posonlyargs) + list(node.args.args)
            defaults = [None] * (len(positional) - len(node.args.defaults)) + list(node.args.defaults)
            for arg, default in zip(positional, defaults):
                text = arg.arg
                if default is not None:
                    text += "=" + ast.unparse(default)
                args.append(text)
            if node.args.vararg:
                args.append("*" + node.args.vararg.arg)
            for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
                text = arg.arg
                if default is not None:
                    text += "=" + ast.unparse(default)
                args.append(text)
            if node.args.kwarg:
                args.append("**" + node.args.kwarg.arg)
            return f"{function_name}({', '.join(args)})"
    return None


def _prompt_sections(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "missing", "path": str(path)}
    sections: list[str] = []
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("[") and line.endswith("]"):
                sections.append(line[1:-1])
    except OSError as exc:
        return {"status": "error", "path": str(path), "error": str(exc)}
    return {
        "status": "ok" if "MEDICAL_ASSISTANT" in sections else "missing-section",
        "path": str(path),
        "sections": sections,
    }


def _import_report(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        return {"module": module_name, "status": "ok", "file": getattr(module, "__file__", None)}
    except Exception as exc:  # imports are diagnostics; do not hide the cause
        return {"module": module_name, "status": "error", "error": f"{type(exc).__name__}: {exc}"}


def inspect_project(root: Path) -> dict[str, Any]:
    root = root.resolve()
    result: dict[str, Any] = {
        "project_root": str(root),
        "safe_mode": True,
        "remote_models_constructed": False,
        "network_calls_made": False,
        "files": {},
        "imports": [],
        "signatures": {},
        "registry": EXPECTED_TOOLS,
    }

    # Prefer the requested project package without making the import mandatory.
    if (root / "medrax").is_dir() and str(root) not in sys.path:
        sys.path.insert(0, str(root))

    main_file = root / "main.py"
    agent_file = root / "medrax" / "agent" / "agent.py"
    prompt_file = root / "medrax" / "docs" / "system_prompts.txt"
    result["files"]["main"] = {"status": "ok" if main_file.is_file() else "missing"}
    result["files"]["agent"] = {"status": "ok" if agent_file.is_file() else "missing"}
    result["files"]["prompt"] = _prompt_sections(prompt_file)

    if main_file.is_file():
        result["signatures"]["initialize_agent"] = _signature_from_ast(main_file, "initialize_agent")
    if agent_file.is_file():
        result["signatures"]["Agent.__init__"] = _signature_from_ast(agent_file, "__init__")

    # These modules define orchestration contracts but do not instantiate tools.
    for module_name in ("medrax.agent", "medrax.utils.utils"):
        report = _import_report(module_name)
        result["imports"].append(report)
        if report["status"] == "ok" and module_name == "medrax.agent":
            try:
                result["signatures"]["Agent"] = str(inspect.signature(getattr(importlib.import_module(module_name), "Agent")))
            except (AttributeError, TypeError, ValueError) as exc:
                result["signatures"]["Agent"] = f"unavailable: {type(exc).__name__}: {exc}"

    result["dependency_probe"] = {
        name: importlib.util.find_spec(name) is not None
        for name in ("langchain_core", "langgraph", "langchain_openai")
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = inspect_project(args.project_root)
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("MedRAX orchestration check (safe mode)")
        print(f"project_root: {report['project_root']}")
        print("remote_models_constructed: false; network_calls_made: false")
        for key, value in report["signatures"].items():
            print(f"{key}: {value}")
        print("prompt:", report["files"]["prompt"])
        for item in report["imports"]:
            print(f"import {item['module']}: {item['status']}")
        print("dependency_probe:", report["dependency_probe"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
