#!/usr/bin/env python3
"""Check an AdalFlow runtime environment without making network or provider calls.

Example:
    python check_adalflow_environment.py --json

The script verifies base imports, selected public APIs, and optional dependency
presence. It does not require API keys, vector-store services, datasets, MCP
servers, GPUs, or MLflow.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from typing import Any, Dict, List


OPTIONAL_MODULES = {
    "openai": "OpenAI/OpenAI-compatible clients and current top-level Generator import support",
    "groq": "Groq model client",
    "anthropic": "Anthropic model client",
    "google.generativeai": "Google Generative AI model client",
    "cohere": "Cohere model client",
    "ollama": "Ollama local/server model client",
    "together": "Together model client",
    "mistralai": "Mistral model client",
    "fireworks": "Fireworks model client",
    "azure.identity": "Azure model client authentication",
    "boto3": "Bedrock model client",
    "faiss": "FAISS vector retriever",
    "lancedb": "LanceDB retriever",
    "sqlalchemy": "SQLAlchemy database integration",
    "pgvector": "Postgres pgvector integration",
    "qdrant_client": "Qdrant retriever",
    "mcp": "MCP tools",
    "torch": "Torch/Transformers local model workflows",
    "transformers": "Transformers local model workflows",
    "datasets": "Dataset loaders and benchmarks",
    "mlflow": "MLflow tracing integration",
}


def module_status(name: str) -> Dict[str, Any]:
    try:
        importlib.import_module(name)
    except Exception as exc:  # optional modules may raise import-time dependency errors
        return {"installed": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"installed": True, "error": None}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    parser.add_argument(
        "--check-optional",
        action="append",
        default=[],
        metavar="MODULE",
        help="Check an extra optional module in addition to the built-in list.",
    )
    args = parser.parse_args(argv)

    result: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "status": "unknown",
        "adalflow": {},
        "api_imports": {},
        "optional_modules": {},
        "notes": [],
    }

    try:
        import adalflow as adal
    except Exception as exc:
        result["status"] = "failed"
        result["adalflow"] = {"imported": False, "error": f"{type(exc).__name__}: {exc}"}
        result["notes"].append(
            "If the error mentions openai, install the current practical minimum with: python -m pip install 'adalflow[openai]'"
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    result["adalflow"] = {
        "imported": True,
        "version_attr": getattr(adal, "__version__", None),
        "distribution_version": None,
    }
    try:
        result["adalflow"]["distribution_version"] = metadata.version("adalflow")
    except metadata.PackageNotFoundError:
        result["notes"].append("Distribution metadata for adalflow was not found; check installation source.")

    api_checks = {
        "Component": lambda: adal.Component,
        "DataClass": lambda: adal.DataClass,
        "DataClassParser": lambda: adal.DataClassParser,
        "Prompt": lambda: adal.Prompt,
        "Generator": lambda: adal.Generator,
        "ModelClient": lambda: adal.ModelClient,
        "Embedder": lambda: adal.Embedder,
        "Document": lambda: adal.Document,
        "TextSplitter": lambda: adal.TextSplitter,
        "FunctionTool": lambda: importlib.import_module("adalflow.core.func_tool").FunctionTool,
        "Agent": lambda: adal.Agent,
        "Runner": lambda: adal.Runner,
        "AnswerMatchAcc": lambda: importlib.import_module("adalflow.eval").AnswerMatchAcc,
        "RetrieverEvaluator": lambda: importlib.import_module("adalflow.eval").RetrieverEvaluator,
        "Parameter": lambda: adal.Parameter,
        "Trainer": lambda: adal.Trainer,
    }
    for name, loader in api_checks.items():
        try:
            loader()
        except Exception as exc:
            result["api_imports"][name] = f"{type(exc).__name__}: {exc}"
        else:
            result["api_imports"][name] = True

    optional = dict(OPTIONAL_MODULES)
    for name in args.check_optional:
        optional.setdefault(name, "user-requested optional module")
    for name, purpose in optional.items():
        status = module_status(name)
        status["purpose"] = purpose
        result["optional_modules"][name] = status

    missing_public = [name for name, ok in result["api_imports"].items() if ok is not True]
    if missing_public:
        result["status"] = "failed"
        result["notes"].append(f"Missing expected public API attributes: {', '.join(missing_public)}")
        code = 1
    else:
        result["status"] = "ok"
        result["notes"].append("Base AdalFlow import and public API checks passed; optional modules are workflow-specific.")
        code = 0

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"AdalFlow environment status: {result['status']}")
        print(f"AdalFlow version: {result['adalflow']['version_attr']}")
        installed = [name for name, item in result["optional_modules"].items() if item["installed"]]
        missing = [name for name, item in result["optional_modules"].items() if not item["installed"]]
        print(f"Optional modules installed ({len(installed)}): {', '.join(installed) if installed else 'none'}")
        print(f"Optional modules missing ({len(missing)}): {', '.join(missing) if missing else 'none'}")
        for note in result["notes"]:
            print(f"- {note}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
