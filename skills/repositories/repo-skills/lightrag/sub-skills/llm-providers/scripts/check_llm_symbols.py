#!/usr/bin/env python3
"""Safely inspect installed LightRAG LLM provider symbols.

This script performs import/signature checks only. It does not call provider
APIs, read credentials, start services, initialize storages, or mutate data.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SymbolStatus:
    name: str
    present: bool
    signature: str | None = None
    error: str | None = None


@dataclass
class ModuleStatus:
    module: str
    imported: bool
    error: str | None = None
    symbols: list[SymbolStatus] = field(default_factory=list)


PROVIDER_SYMBOLS: dict[str, list[str]] = {
    "lightrag.llm.openai": [
        "openai_complete_if_cache",
        "openai_complete",
        "gpt_4o_complete",
        "gpt_4o_mini_complete",
        "nvidia_openai_complete",
        "openai_embed",
        "azure_openai_complete_if_cache",
        "azure_openai_complete",
        "azure_openai_embed",
    ],
    "lightrag.llm.azure_openai": [
        "azure_openai_complete_if_cache",
        "azure_openai_complete",
        "azure_openai_embed",
    ],
    "lightrag.llm.ollama": [
        "_ollama_model_if_cache",
        "ollama_model_complete",
        "ollama_embed",
    ],
    "lightrag.llm.gemini": [
        "gemini_complete_if_cache",
        "gemini_model_complete",
        "gemini_embed",
    ],
    "lightrag.llm.bedrock": [
        "bedrock_complete_if_cache",
        "bedrock_complete",
        "bedrock_embed",
    ],
    "lightrag.llm.jina": ["jina_embed"],
    "lightrag.llm.voyageai": ["voyageai_embed"],
    "lightrag.llm.lollms": [
        "lollms_model_if_cache",
        "lollms_model_complete",
        "lollms_embed",
    ],
    "lightrag.llm.anthropic": [
        "anthropic_complete_if_cache",
        "anthropic_complete",
        "claude_3_haiku_complete",
        "claude_3_sonnet_complete",
        "claude_3_opus_complete",
        "anthropic_embed",
    ],
    "lightrag.llm.hf": ["hf_model_complete", "hf_embed"],
    "lightrag.llm.llama_index_impl": ["llama_index_complete", "llama_index_embed"],
    "lightrag.llm.lmdeploy": ["lmdeploy_model_if_cache"],
    "lightrag.llm.nvidia_openai": ["nvidia_openai_embed"],
    "lightrag.llm.zhipu": [
        "zhipu_complete_if_cache",
        "zhipu_complete",
        "zhipu_embedding",
    ],
    "lightrag.rerank": [
        "cohere_rerank",
        "jina_rerank",
        "ali_rerank",
        "generic_rerank_api",
        "chunk_documents_for_rerank",
        "aggregate_chunk_scores",
    ],
    "lightrag.llm._vision_utils": ["normalize_image_inputs"],
}

CORE_SYMBOLS: dict[str, list[str]] = {
    "lightrag": ["LightRAG", "RoleLLMConfig", "RoleSpec", "ROLES"],
    "lightrag.utils": [
        "EmbeddingFunc",
        "wrap_embedding_func_with_attrs",
        "get_llm_cache_identity",
        "serialize_llm_cache_identity",
    ],
    "lightrag.api.config": [
        "normalize_binding_name",
        "get_default_host",
        "get_embedding_prefix_config",
        "resolve_asymmetric_embedding_opt_in",
        "validate_bedrock_auth_configuration",
        "OpenAILLMOptions",
        "OllamaLLMOptions",
        "OllamaEmbeddingOptions",
        "GeminiLLMOptions",
        "GeminiEmbeddingOptions",
        "BedrockLLMOptions",
    ],
}

EXPECTED_ROLES = ["extract", "keyword", "query", "vlm"]
EXPECTED_BINDINGS = {
    "llm": [
        "lollms",
        "ollama",
        "openai",
        "openai-ollama",
        "azure_openai",
        "bedrock",
        "gemini",
    ],
    "embedding": [
        "lollms",
        "ollama",
        "openai",
        "azure_openai",
        "bedrock",
        "jina",
        "gemini",
        "voyageai",
    ],
    "rerank": ["null", "cohere", "jina", "aliyun"],
}


def safe_signature(value: Any) -> str | None:
    """Return a readable signature without invoking the object."""
    try:
        return str(inspect.signature(value))
    except (TypeError, ValueError):
        return None


def inspect_module(module_name: str, symbol_names: list[str]) -> ModuleStatus:
    """Import one module and inspect expected symbols."""
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report optional dependency import failures.
        return ModuleStatus(module=module_name, imported=False, error=f"{type(exc).__name__}: {exc}")

    symbols: list[SymbolStatus] = []
    for symbol_name in symbol_names:
        try:
            value = getattr(module, symbol_name)
        except AttributeError:
            symbols.append(SymbolStatus(name=symbol_name, present=False))
        except Exception as exc:  # noqa: BLE001 - report lazy import/dependency failures.
            symbols.append(
                SymbolStatus(
                    name=symbol_name,
                    present=False,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
        else:
            symbols.append(
                SymbolStatus(
                    name=symbol_name,
                    present=True,
                    signature=safe_signature(value),
                )
            )

    return ModuleStatus(module=module_name, imported=True, symbols=symbols)


def collect_report(include_optional: bool) -> dict[str, Any]:
    """Collect all check results as JSON-serializable data."""
    modules_to_check = dict(CORE_SYMBOLS)
    if include_optional:
        modules_to_check.update(PROVIDER_SYMBOLS)

    modules = [inspect_module(name, symbols) for name, symbols in modules_to_check.items()]

    roles: list[str] = []
    roles_ok = False
    try:
        lightrag_module = importlib.import_module("lightrag")
        roles = [spec.name for spec in getattr(lightrag_module, "ROLES")]
        roles_ok = roles == EXPECTED_ROLES
    except Exception:  # noqa: BLE001 - module import status already reported.
        roles = []

    imported_count = sum(1 for module in modules if module.imported)
    missing_symbols = [
        f"{module.module}.{symbol.name}"
        for module in modules
        if module.imported
        for symbol in module.symbols
        if not symbol.present
    ]
    symbol_errors = [
        {
            "symbol": f"{module.module}.{symbol.name}",
            "error": symbol.error,
        }
        for module in modules
        if module.imported
        for symbol in module.symbols
        if symbol.error is not None
    ]
    import_errors = [
        {"module": module.module, "error": module.error}
        for module in modules
        if not module.imported
    ]

    status = "ok"
    if missing_symbols:
        status = "missing-symbols"
    if symbol_errors:
        status = "symbol-errors" if status == "ok" else "issues"
    if import_errors:
        status = "import-errors" if status == "ok" else "issues"
    if not roles_ok:
        status = "issues" if status != "ok" else "role-mismatch"

    return {
        "status": status,
        "safe_check": True,
        "network_calls": False,
        "provider_calls": False,
        "include_optional_provider_modules": include_optional,
        "expected_roles": EXPECTED_ROLES,
        "observed_roles": roles,
        "roles_ok": roles_ok,
        "expected_bindings": EXPECTED_BINDINGS,
        "summary": {
            "modules_checked": len(modules),
            "modules_imported": imported_count,
            "import_errors": len(import_errors),
            "missing_symbols": len(missing_symbols),
            "symbol_errors": len(symbol_errors),
        },
        "import_errors": import_errors,
        "missing_symbols": missing_symbols,
        "symbol_errors": symbol_errors,
        "modules": [
            {
                "module": module.module,
                "imported": module.imported,
                "error": module.error,
                "symbols": [asdict(symbol) for symbol in module.symbols],
            }
            for module in modules
        ],
    }


def print_text(report: dict[str, Any]) -> None:
    """Print a concise human-readable report."""
    summary = report["summary"]
    print("LightRAG LLM symbol check")
    print(f"status: {report['status']}")
    print("safe_check: no network/provider calls")
    print(
        "modules: "
        f"{summary['modules_imported']}/{summary['modules_checked']} imported, "
        f"{summary['import_errors']} import errors, "
        f"{summary['missing_symbols']} missing symbols, "
        f"{summary['symbol_errors']} symbol errors"
    )
    print(f"roles: {', '.join(report['observed_roles']) or '<unavailable>'}")

    if report["import_errors"]:
        print("\nImport errors:")
        for item in report["import_errors"]:
            print(f"- {item['module']}: {item['error']}")

    if report["missing_symbols"]:
        print("\nMissing symbols:")
        for symbol in report["missing_symbols"]:
            print(f"- {symbol}")

    if report["symbol_errors"]:
        print("\nSymbol errors:")
        for item in report["symbol_errors"]:
            print(f"- {item['symbol']}: {item['error']}")

    print("\nProvider modules:")
    for module in report["modules"]:
        symbol_count = sum(1 for symbol in module["symbols"] if symbol["present"])
        total = len(module["symbols"])
        state = "imported" if module["imported"] else "import-error"
        print(f"- {module['module']}: {state}, {symbol_count}/{total} symbols")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect installed LightRAG LLM, embedding, VLM, role, "
            "rerank, and API config symbols without contacting provider services."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable JSON instead of text",
    )
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="skip optional provider module imports and check only core symbols",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when imports, symbols, or role checks have issues",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = collect_report(include_optional=not args.core_only)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    if args.strict and report["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
