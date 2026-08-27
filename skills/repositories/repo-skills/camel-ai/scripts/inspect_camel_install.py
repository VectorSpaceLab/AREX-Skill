#!/usr/bin/env python3
"""No-network CAMEL-AI installation and route inspector."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
from typing import Any

ROUTES = {
    "agents-and-societies": [
        ("camel.agents", "ChatAgent"),
        ("camel.societies", "RolePlaying"),
        ("camel.societies", "Workforce"),
        ("camel.tasks", "Task"),
    ],
    "models-and-configuration": [
        ("camel.models", "ModelFactory"),
        ("camel.models", "ModelManager"),
        ("camel.models", "BaseModelBackend"),
        ("camel.types", "ModelPlatformType"),
    ],
    "tools-runtimes-and-services": [
        ("camel.toolkits", "FunctionTool"),
        ("camel.toolkits", "MCPToolkit"),
        ("camel.runtimes", "BaseRuntime"),
        ("camel.interpreters", "InternalPythonInterpreter"),
    ],
    "memory-rag-and-data": [
        ("camel.memories", "ChatHistoryMemory"),
        ("camel.retrievers", "VectorRetriever"),
        ("camel.embeddings", "OpenAIEmbedding"),
        ("camel.storages", "VectorRecord"),
    ],
    "datagen-evaluation-and-benchmarks": [
        ("camel.extractors", "BoxedStrategy"),
        ("camel.verifiers", "MathVerifier"),
        ("camel.environments", "TicTacToeEnv"),
    ],
}


def inspect_symbol(module_name: str, symbol_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        symbol = getattr(module, symbol_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    try:
        signature = str(inspect.signature(symbol))
    except Exception:
        signature = None
    return {"ok": True, "signature": signature}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect CAMEL-AI imports and route owners without network calls."
    )
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()

    report: dict[str, Any] = {"distribution": "camel-ai", "routes": {}}
    try:
        report["version"] = metadata.version("camel-ai")
    except metadata.PackageNotFoundError:
        report["version"] = None
        report["package_error"] = "camel-ai distribution metadata not found"

    for route, symbols in ROUTES.items():
        report["routes"][route] = {
            f"{module}.{symbol}": inspect_symbol(module, symbol)
            for module, symbol in symbols
        }

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report.get("version") else 1

    print(f"camel-ai version: {report.get('version') or 'not installed'}")
    for route, symbols in report["routes"].items():
        ok_count = sum(1 for item in symbols.values() if item["ok"])
        print(f"{route}: {ok_count}/{len(symbols)} imports ok")
        for name, result in symbols.items():
            marker = "ok" if result["ok"] else "missing"
            detail = result.get("signature") or result.get("error") or ""
            print(f"  - {name}: {marker} {detail}")
    return 0 if report.get("version") else 1


if __name__ == "__main__":
    raise SystemExit(main())
