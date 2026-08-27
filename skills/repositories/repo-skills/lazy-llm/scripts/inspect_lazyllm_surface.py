#!/usr/bin/env python3
"""Inspect public LazyLLM API signatures without running models or services.

Examples:
  python scripts/inspect_lazyllm_surface.py
  python scripts/inspect_lazyllm_surface.py --json
  python scripts/inspect_lazyllm_surface.py --repo-root /path/to/LazyLLM --include-optional
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from typing import Any, Dict, Iterable, Optional


CORE_OBJECTS = [
    ("lazyllm", "pipeline"),
    ("lazyllm", "parallel"),
    ("lazyllm", "diverter"),
    ("lazyllm", "switch"),
    ("lazyllm", "ifs"),
    ("lazyllm", "loop"),
    ("lazyllm", "bind"),
    ("lazyllm", "TrainableModule"),
    ("lazyllm", "OnlineModule"),
    ("lazyllm", "OnlineChatModule"),
    ("lazyllm", "ServerModule"),
    ("lazyllm", "ActionModule"),
]

OPTIONAL_OBJECTS = [
    ("lazyllm.tools", "Document"),
    ("lazyllm.tools", "Retriever"),
    ("lazyllm.tools", "Reranker"),
    ("lazyllm.tools", "fc_register"),
    ("lazyllm.tools", "ToolManager"),
    ("lazyllm.tools", "SkillManager"),
    ("lazyllm.tools", "ReactAgent"),
    ("lazyllm.tools", "ReWOOAgent"),
    ("lazyllm.tools", "PlanAndSolveAgent"),
    ("lazyllm.tools", "MCPClient"),
    ("lazyllm.tools.writer.tools.base", "WriterToolBase"),
]


def _add_repo_root(repo_root: Optional[str]) -> None:
    if repo_root:
        root = os.path.abspath(repo_root)
        if root not in sys.path:
            sys.path.insert(0, root)


def _signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # noqa: BLE001 - diagnostic script should preserve the failure
        return f"<signature unavailable: {type(exc).__name__}: {exc}>"


def _inspect_objects(items: Iterable[tuple[str, str]]) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for module_name, attr_name in items:
        key = f"{module_name}.{attr_name}"
        try:
            module = importlib.import_module(module_name)
            obj = getattr(module, attr_name)
            out[key] = {"ok": "true", "signature": _signature(obj), "module": getattr(obj, "__module__", module_name)}
        except Exception as exc:  # noqa: BLE001
            out[key] = {"ok": "false", "error": f"{type(exc).__name__}: {exc}"}
    return out


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect LazyLLM public surface signatures safely.")
    parser.add_argument("--repo-root", help="Optional source checkout root to prepend to sys.path before imports.")
    parser.add_argument("--include-optional", action="store_true", help="Inspect optional tools/RAG/agent/writer objects too.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)

    _add_repo_root(args.repo_root)
    lazyllm = importlib.import_module("lazyllm")
    result: Dict[str, Any] = {
        "lazyllm_version": getattr(lazyllm, "__version__", "unknown"),
        "python": sys.version.split()[0],
        "core": _inspect_objects(CORE_OBJECTS),
    }
    if args.include_optional:
        result["optional"] = _inspect_objects(OPTIONAL_OBJECTS)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"LazyLLM version: {result['lazyllm_version']}")
        print(f"Python: {result['python']}")
        for section in ("core", "optional"):
            if section not in result:
                continue
            print(f"\n[{section}]")
            for key, value in result[section].items():
                if value.get("ok") == "true":
                    print(f"- {key}: {value['signature']}")
                else:
                    print(f"- {key}: ERROR {value['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
