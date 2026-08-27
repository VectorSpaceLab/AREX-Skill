#!/usr/bin/env python3
"""Inspect the verified public DataFlow surface.

The script prints class/function signatures for the core package families that
matter most to the root skill. It is safe, offline, and does not start models or
services.

Examples:
  python scripts/inspect_dataflow_surface.py
  python scripts/inspect_dataflow_surface.py --json
  python scripts/inspect_dataflow_surface.py --module dataflow.cli --module dataflow.serving
  python scripts/inspect_dataflow_surface.py --self-check-help
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from pathlib import Path

REQUIRED_MODULES = [
    "dataflow.core.operator",
    "dataflow.core.prompt",
    "dataflow.pipeline",
    "dataflow.utils.storage",
]

OPTIONAL_MODULES = [
    "dataflow.serving",
    "dataflow.rayorch",
]

DEFAULT_MODULES = REQUIRED_MODULES + OPTIONAL_MODULES

DEFAULT_SYMBOLS = {
    "dataflow.core.operator": ["OperatorABC", "get_operator"],
    "dataflow.core.prompt": ["PromptABC", "DIYPromptABC", "prompt_restrict"],
    "dataflow.pipeline": ["PipelineABC", "BatchedPipelineABC", "StreamBatchedPipelineABC"],
    "dataflow.utils.storage": [
        "DataFlowStorage",
        "FileStorage",
        "LazyFileStorage",
        "DummyStorage",
        "BatchedFileStorage",
        "StreamBatchedFileStorage",
        "MyScaleDBStorage",
    ],
    "dataflow.serving": [
        "APILLMServing_request",
        "LiteLLMServing",
        "LocalModelLLMServing_vllm",
        "LocalModelLLMServing_sglang",
        "APIVLMServing_openai",
        "PerspectiveAPIServing",
        "LocalEmbeddingServing",
        "LightRAGServing",
        "APIGoogleVertexAIServing",
        "LocalHostLLMAPIServing_vllm",
        "LocalModelLALMServing_vllm",
        "LocalVLMServing_vllm",
    ],
    "dataflow.rayorch": ["RayAcceleratedOperator"],
}


def _maybe_add_repo_root(repo_root: Path | None) -> None:
    if repo_root is None:
        return
    repo_root = repo_root.expanduser().resolve()
    if (repo_root / "dataflow" / "__init__.py").is_file() and str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect the public DataFlow surface and signatures.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional checkout root to add to sys.path before import.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human-readable summary.")
    parser.add_argument("--module", action="append", default=[], help="Extra module to inspect. Repeatable.")
    parser.add_argument("--self-check-help", action="store_true", help="Verify argparse help text and exit.")
    return parser


def _describe_module(module_name: str) -> dict[str, object]:
    info: dict[str, object] = {"symbols": {}}
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001
        info["ok"] = False
        info["error"] = f"{exc.__class__.__name__}: {exc}"
        return info

    info["ok"] = True
    info["file"] = getattr(module, "__file__", None)
    symbol_names = DEFAULT_SYMBOLS.get(module_name, [])
    if not symbol_names:
        symbol_names = [name for name in dir(module) if not name.startswith("_")]

    for name in symbol_names:
        if not hasattr(module, name):
            continue
        obj = getattr(module, name)
        if inspect.isclass(obj) or inspect.isfunction(obj):
            try:
                sig = str(inspect.signature(obj))
            except Exception:
                sig = "(?)"
            info["symbols"][name] = {
                "kind": "class" if inspect.isclass(obj) else "function",
                "signature": sig,
            }
    return info


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.self_check_help:
        help_text = parser.format_help()
        if "--module" not in help_text or "--repo-root" not in help_text:
            raise AssertionError("argparse help text did not include expected options")
        print("OK: argparse --help text is available.")
        return 0

    _maybe_add_repo_root(args.repo_root)

    module_names = list(dict.fromkeys(DEFAULT_MODULES + list(args.module)))
    result = {
        "python_version": sys.version.split()[0],
        "required_modules": {},
        "optional_modules": {},
    }

    for name in REQUIRED_MODULES:
        result["required_modules"][name] = _describe_module(name)
    for name in OPTIONAL_MODULES:
        result["optional_modules"][name] = _describe_module(name)
    for name in args.module:
        if name not in REQUIRED_MODULES and name not in OPTIONAL_MODULES:
            result.setdefault("extra_modules", {})[name] = _describe_module(name)

    ok = all(bool(entry.get("ok", False)) for entry in result["required_modules"].values())

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python_version']}")
        print("Required modules:")
        for name, entry in result["required_modules"].items():
            if not entry.get("ok"):
                print(f"- {name}: FAIL ({entry.get('error')})")
                continue
            print(f"- {name}")
            for symbol, spec in entry["symbols"].items():
                print(f"  - {symbol}{spec['signature']}")
        if result["optional_modules"]:
            print("Optional modules:")
            for name, entry in result["optional_modules"].items():
                if not entry.get("ok"):
                    print(f"- {name}: MISSING ({entry.get('error')})")
                    continue
                print(f"- {name}")
                for symbol, spec in entry["symbols"].items():
                    print(f"  - {symbol}{spec['signature']}")
        extra_modules = result.get("extra_modules", {})
        if extra_modules:
            print("Extra modules:")
            for name, entry in extra_modules.items():
                if not entry.get("ok"):
                    print(f"- {name}: MISSING ({entry.get('error')})")
                    continue
                print(f"- {name}")
                for symbol, spec in entry["symbols"].items():
                    print(f"  - {symbol}{spec['signature']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
