#!/usr/bin/env python3
"""Check a knowledge-storm runtime environment.

This script performs local import and environment checks only. It does not call
LLMs, embeddings, search APIs, Qdrant, or STORM/Co-STORM runners.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import sys
from typing import Any

REQUIRED_IMPORTS = [
    "knowledge_storm",
    "knowledge_storm.lm",
    "knowledge_storm.rm",
    "knowledge_storm.utils",
    "knowledge_storm.encoder",
    "knowledge_storm.storm_wiki.engine",
    "knowledge_storm.collaborative_storm.engine",
    "knowledge_storm.logging_wrapper",
]

OPTIONAL_IMPORTS = [
    "qdrant_client",
    "langchain_qdrant",
    "langchain_huggingface",
    "sentence_transformers",
    "duckduckgo_search",
    "tavily",
    "torch",
]

RETRIEVER_ENV = {
    "bing": ["BING_SEARCH_API_KEY"],
    "you": ["YDC_API_KEY"],
    "brave": ["BRAVE_API_KEY"],
    "serper": ["SERPER_API_KEY"],
    "duckduckgo": [],
    "tavily": ["TAVILY_API_KEY"],
    "searxng": ["SEARXNG_API_URL"],
    "azure_ai_search": ["AZURE_AI_SEARCH_API_KEY", "AZURE_AI_SEARCH_URL", "AZURE_AI_SEARCH_INDEX_NAME"],
}


def _import_status(module_names: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name in module_names:
        try:
            module = importlib.import_module(name)
            result[name] = {"ok": True, "module_file_present": bool(getattr(module, "__file__", None))}
        except Exception as exc:  # noqa: BLE001 - report import errors without hiding type/message.
            result[name] = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    return result


def _version_status() -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        out["distribution_version"] = importlib.metadata.version("knowledge-storm")
    except importlib.metadata.PackageNotFoundError:
        out["distribution_version"] = None
        out["distribution_error"] = "knowledge-storm distribution not found"
    try:
        import knowledge_storm

        out["package___version__"] = getattr(knowledge_storm, "__version__", None)
    except Exception as exc:  # noqa: BLE001
        out["package___version__"] = None
        out["package_error"] = f"{type(exc).__name__}: {exc}"
    out["version_mismatch"] = bool(
        out.get("distribution_version")
        and out.get("package___version__")
        and out["distribution_version"] != out["package___version__"]
    )
    return out


def _env_status(names: list[str]) -> dict[str, bool]:
    return {name: bool(os.getenv(name)) for name in names}


def _retriever_env_status() -> dict[str, dict[str, bool]]:
    return {retriever: _env_status(names) for retriever, names in RETRIEVER_ENV.items()}


def _encoder_env_status() -> dict[str, Any]:
    encoder_type = os.getenv("ENCODER_API_TYPE")
    if not encoder_type:
        return {"encoder_api_type": None, "ready": False, "missing": ["ENCODER_API_TYPE"]}
    lower = encoder_type.lower()
    if lower == "openai":
        missing = [name for name in ["OPENAI_API_KEY"] if not os.getenv(name)]
    elif lower == "azure":
        missing = [name for name in ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"] if not os.getenv(name)]
    else:
        return {
            "encoder_api_type": encoder_type,
            "ready": False,
            "missing": [],
            "error": "supported ENCODER_API_TYPE values are openai and azure in this package version",
        }
    return {"encoder_api_type": encoder_type, "ready": not missing, "missing": missing}


def _torch_status() -> dict[str, Any]:
    try:
        import torch

        cuda_available = bool(torch.cuda.is_available())
        info: dict[str, Any] = {
            "import_ok": True,
            "version": getattr(torch, "__version__", None),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": cuda_available,
            "cuda_device_count": int(torch.cuda.device_count()) if cuda_available else 0,
        }
        if cuda_available:
            info["cuda_device_0"] = torch.cuda.get_device_name(0)
        return info
    except Exception as exc:  # noqa: BLE001
        return {"import_ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def _all_required_imports_ok(imports: dict[str, dict[str, Any]]) -> bool:
    return all(item.get("ok") for item in imports.values())


def _build_report(args: argparse.Namespace) -> dict[str, Any]:
    required_imports = _import_status(REQUIRED_IMPORTS)
    optional_imports = _import_status(OPTIONAL_IMPORTS)
    report = {
        "versions": _version_status(),
        "required_imports": required_imports,
        "optional_imports": optional_imports,
        "retriever_env": _retriever_env_status(),
        "encoder_env": _encoder_env_status(),
        "torch": _torch_status(),
    }
    failures: list[str] = []
    if not _all_required_imports_ok(required_imports):
        failures.append("one or more required knowledge-storm imports failed")
    if args.require_cuda and not report["torch"].get("cuda_available"):
        failures.append("--require-cuda was set but torch CUDA is not available")
    if args.fail_on_missing_optional:
        missing_optional = [name for name, status in optional_imports.items() if not status.get("ok")]
        if missing_optional:
            failures.append("missing optional imports: " + ", ".join(missing_optional))
    report["ok"] = not failures
    report["failures"] = failures
    return report


def _print_human(report: dict[str, Any]) -> None:
    versions = report["versions"]
    print("knowledge-storm runtime check")
    print(f"  distribution version: {versions.get('distribution_version')}")
    print(f"  package __version__: {versions.get('package___version__')}")
    if versions.get("version_mismatch"):
        print("  warning: distribution version and package __version__ differ")
    print("  required imports:")
    for name, status in report["required_imports"].items():
        print(f"    {'ok' if status.get('ok') else 'FAIL'} {name}")
        if not status.get("ok"):
            print(f"      {status.get('error_type')}: {status.get('error')}")
    print("  optional imports:")
    for name, status in report["optional_imports"].items():
        print(f"    {'ok' if status.get('ok') else 'missing'} {name}")
    enc = report["encoder_env"]
    print(f"  encoder: type={enc.get('encoder_api_type')} ready={enc.get('ready')} missing={enc.get('missing')}")
    torch = report["torch"]
    print(f"  torch: import_ok={torch.get('import_ok')} cuda_available={torch.get('cuda_available')} device0={torch.get('cuda_device_0')}")
    if report["failures"]:
        print("  failures:")
        for failure in report["failures"]:
            print(f"    - {failure}")
    print(f"  overall: {'ok' if report['ok'] else 'failed'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check local knowledge-storm package imports and environment readiness.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail unless torch CUDA is available.")
    parser.add_argument("--fail-on-missing-optional", action="store_true", help="Fail if optional VectorRM/search acceleration imports are missing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = _build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
