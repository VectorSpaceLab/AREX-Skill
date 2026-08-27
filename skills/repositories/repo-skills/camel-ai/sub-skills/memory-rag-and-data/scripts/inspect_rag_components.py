#!/usr/bin/env python3
"""Inspect CAMEL memory/RAG/data components without network access.

This script imports public CAMEL classes, reports constructor signatures, checks
optional dependency availability, and can run a tiny no-network schema smoke
check over key-value and vector record objects. It intentionally avoids creating
hosted embeddings, network loaders, or remote storage clients.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import platform
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SymbolSpec:
    label: str
    module: str
    name: str


SYMBOLS: list[SymbolSpec] = [
    SymbolSpec("ChatAgent", "camel.agents", "ChatAgent"),
    SymbolSpec("ChatHistoryMemory", "camel.memories", "ChatHistoryMemory"),
    SymbolSpec("VectorDBMemory", "camel.memories", "VectorDBMemory"),
    SymbolSpec("LongtermAgentMemory", "camel.memories", "LongtermAgentMemory"),
    SymbolSpec("MemoryRecord", "camel.memories", "MemoryRecord"),
    SymbolSpec(
        "ScoreBasedContextCreator",
        "camel.memories.context_creators",
        "ScoreBasedContextCreator",
    ),
    SymbolSpec("VectorRetriever", "camel.retrievers", "VectorRetriever"),
    SymbolSpec("AutoRetriever", "camel.retrievers", "AutoRetriever"),
    SymbolSpec("HybridRetriever", "camel.retrievers", "HybridRetriever"),
    SymbolSpec("BM25Retriever", "camel.retrievers", "BM25Retriever"),
    SymbolSpec("OpenAIEmbedding", "camel.embeddings", "OpenAIEmbedding"),
    SymbolSpec(
        "OpenAICompatibleEmbedding",
        "camel.embeddings",
        "OpenAICompatibleEmbedding",
    ),
    SymbolSpec("SentenceTransformerEncoder", "camel.embeddings", "SentenceTransformerEncoder"),
    SymbolSpec("VectorRecord", "camel.storages", "VectorRecord"),
    SymbolSpec("VectorDBQuery", "camel.storages", "VectorDBQuery"),
    SymbolSpec("QdrantStorage", "camel.storages", "QdrantStorage"),
    SymbolSpec("ChromaStorage", "camel.storages", "ChromaStorage"),
    SymbolSpec("FaissStorage", "camel.storages", "FaissStorage"),
    SymbolSpec("InMemoryKeyValueStorage", "camel.storages", "InMemoryKeyValueStorage"),
    SymbolSpec("JsonStorage", "camel.storages", "JsonStorage"),
    SymbolSpec("Neo4jGraph", "camel.storages.graph_storages", "Neo4jGraph"),
    SymbolSpec("NebulaGraph", "camel.storages.graph_storages", "NebulaGraph"),
    SymbolSpec("create_file_from_raw_bytes", "camel.loaders", "create_file_from_raw_bytes"),
    SymbolSpec("UnstructuredIO", "camel.loaders", "UnstructuredIO"),
    SymbolSpec("MarkItDownLoader", "camel.loaders", "MarkItDownLoader"),
    SymbolSpec("HuggingFaceDatasetManager", "camel.datahubs", "HuggingFaceDatasetManager"),
    SymbolSpec("StaticDataset", "camel.datasets", "StaticDataset"),
    SymbolSpec("FewShotGenerator", "camel.datasets", "FewShotGenerator"),
    SymbolSpec("SelfInstructGenerator", "camel.datasets", "SelfInstructGenerator"),
]

OPTIONAL_MODULES: dict[str, list[str]] = {
    "rag": [
        "qdrant_client",
        "pymilvus",
        "faiss",
        "weaviate",
        "neo4j",
        "nebula3",
        "rank_bm25",
        "cohere",
        "unstructured",
        "chromadb",
    ],
    "storage": [
        "qdrant_client",
        "pymilvus",
        "faiss",
        "neo4j",
        "nebula3",
        "redis",
        "boto3",
        "azure.storage.blob",
        "google.cloud.storage",
    ],
    "document_tools": [
        "docx2txt",
        "fitz",
        "unstructured",
        "markitdown",
        "openpyxl",
        "pptx",
    ],
    "loader_services": [
        "apify_client",
        "firecrawl",
        "chunkr_ai",
        "mistralai",
        "crawl4ai",
    ],
    "local_embeddings": ["sentence_transformers", "numpy"],
}


def import_symbol(spec: SymbolSpec) -> dict[str, Any]:
    try:
        module = importlib.import_module(spec.module)
        obj = getattr(module, spec.name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return {
            "label": spec.label,
            "module": spec.module,
            "name": spec.name,
            "available": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    try:
        signature = str(inspect.signature(obj))
    except (TypeError, ValueError):
        signature = None

    methods: dict[str, str | None] = {}
    for method_name in [
        "__init__",
        "process",
        "query",
        "embed",
        "embed_list",
        "get_output_dim",
        "add",
        "delete",
        "status",
        "clear",
        "load",
        "save",
        "parse_file_or_url",
        "parse_bytes",
        "convert_file",
        "convert_files",
        "get_context",
        "write_records",
        "retrieve",
    ]:
        if hasattr(obj, method_name):
            try:
                methods[method_name] = str(inspect.signature(getattr(obj, method_name)))
            except (TypeError, ValueError):
                methods[method_name] = None

    return {
        "label": spec.label,
        "module": spec.module,
        "name": spec.name,
        "available": True,
        "signature": signature,
        "methods": methods,
    }


def module_available(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    return {"available": True, "version": version}


def smoke_check() -> dict[str, Any]:
    checks: dict[str, Any] = {}
    try:
        from camel.storages import VectorDBQuery, VectorRecord
        from camel.storages.key_value_storages import InMemoryKeyValueStorage

        vector = VectorRecord(
            vector=[0.1, 0.2, 0.3, 0.4],
            payload={"text": "fixture", "metadata": {"source": "smoke"}},
        )
        query = VectorDBQuery(query_vector=[0.1, 0.2, 0.3, 0.4], top_k=1)
        kv = InMemoryKeyValueStorage()
        kv.save([{"role": "user", "content": "hello"}])
        loaded = kv.load()
        checks["schema_objects"] = {
            "ok": True,
            "vector_length": len(vector.vector),
            "payload_keys": sorted((vector.payload or {}).keys()),
            "query_top_k": query.top_k,
            "key_value_records": len(loaded),
        }
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        checks["schema_objects"] = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return checks


def build_report(include_smoke: bool) -> dict[str, Any]:
    try:
        import camel

        camel_imported = True
        camel_version = getattr(camel, "__version__", None)
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        camel_imported = False
        camel_version = None
        camel_error = f"{type(exc).__name__}: {exc}"
    else:
        camel_error = None

    report: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "camel": {"available": camel_imported, "version": camel_version},
        "symbols": [import_symbol(spec) for spec in SYMBOLS],
        "optional_modules": {
            group: {name: module_available(name) for name in names}
            for group, names in OPTIONAL_MODULES.items()
        },
        "notes": [
            "No network calls are made by this script.",
            "Hosted embeddings and remote storage clients are not instantiated.",
            "Install narrow extras such as camel-ai[rag], camel-ai[storage], or camel-ai[document_tools] for missing optional modules.",
        ],
    }
    if camel_error is not None:
        report["camel"]["error"] = camel_error
    if include_smoke:
        report["smoke"] = smoke_check()
    return report


def print_text(report: dict[str, Any]) -> None:
    camel = report["camel"]
    print(f"Python: {report['python']}")
    print(f"Platform: {report['platform']}")
    print(f"CAMEL import: {'ok' if camel['available'] else 'failed'}")
    if camel.get("version"):
        print(f"CAMEL version: {camel['version']}")
    if camel.get("error"):
        print(f"CAMEL error: {camel['error']}")

    print("\nSymbols:")
    for symbol in report["symbols"]:
        status = "ok" if symbol["available"] else "missing"
        line = f"- {symbol['label']}: {status}"
        if symbol.get("signature"):
            line += f" {symbol['signature']}"
        if symbol.get("error"):
            line += f" ({symbol['error']})"
        print(line)

    print("\nOptional modules:")
    for group, modules in report["optional_modules"].items():
        available = [name for name, info in modules.items() if info["available"]]
        missing = [name for name, info in modules.items() if not info["available"]]
        print(f"- {group}: {len(available)} available, {len(missing)} missing")
        if missing:
            print(f"  missing: {', '.join(missing)}")

    if "smoke" in report:
        print("\nSmoke checks:")
        for name, result in report["smoke"].items():
            print(f"- {name}: {'ok' if result.get('ok') else 'failed'}")
            if result.get("error"):
                print(f"  error: {result['error']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run no-network schema smoke checks for vector/key-value objects.",
    )
    args = parser.parse_args(argv)

    report = build_report(include_smoke=args.smoke)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["camel"]["available"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
