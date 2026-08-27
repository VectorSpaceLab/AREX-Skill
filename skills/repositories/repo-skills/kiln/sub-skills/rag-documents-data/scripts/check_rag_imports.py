#!/usr/bin/env python3
"""Import-check Kiln document/RAG modules without provider calls or network access."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

TARGET_MODULES: tuple[str, ...] = (
    "kiln_ai.datamodel.extraction",
    "kiln_ai.datamodel.chunk",
    "kiln_ai.datamodel.embedding",
    "kiln_ai.datamodel.vector_store",
    "kiln_ai.datamodel.rag",
    "kiln_ai.datamodel.reranker",
    "kiln_ai.adapters.extractors.base_extractor",
    "kiln_ai.adapters.extractors.litellm_extractor",
    "kiln_ai.adapters.extractors.extractor_registry",
    "kiln_ai.adapters.chunkers.base_chunker",
    "kiln_ai.adapters.chunkers.fixed_window_chunker",
    "kiln_ai.adapters.chunkers.semantic_chunker",
    "kiln_ai.adapters.chunkers.chunker_registry",
    "kiln_ai.adapters.embedding.base_embedding_adapter",
    "kiln_ai.adapters.embedding.litellm_embedding_adapter",
    "kiln_ai.adapters.embedding.embedding_registry",
    "kiln_ai.adapters.vector_store.base_vector_store_adapter",
    "kiln_ai.adapters.vector_store.lancedb_helpers",
    "kiln_ai.adapters.vector_store.lancedb_adapter",
    "kiln_ai.adapters.vector_store.vector_store_registry",
    "kiln_ai.adapters.vector_store_loaders.vector_store_loader",
    "kiln_ai.adapters.rag.deduplication",
    "kiln_ai.adapters.rag.progress",
    "kiln_ai.adapters.rag.rag_runners",
    "kiln_ai.adapters.rerankers.base_reranker",
    "kiln_ai.adapters.rerankers.litellm_reranker_adapter",
    "kiln_ai.adapters.rerankers.reranker_registry",
    "kiln_ai.tools.rag_tools",
    "kiln_server.document_api",
)

KNOWN_DEPENDENCY_HINTS: dict[str, str] = {
    "fastapi": "document API imports FastAPI route types",
    "lancedb": "LanceDB vector-store indexing/search",
    "litellm": "extractor, embedding, and reranker adapters",
    "llama_index": "chunkers, vector-store helpers, and LanceDB integration",
    "mcp": "keep MCP lock-compatible with current tool imports; 1.10.1 was verified",
    "openai": "provider SDK used by provider-backed adapters; optional unless live provider calls are required",
    "pandas": "LanceDB reconciliation can call a to_pandas() path",
    "starlette": "server import compatibility depends on the FastAPI/Starlette stack; 0.52.1 was verified",
}


@dataclass(frozen=True)
class ImportResult:
    module: str
    status: str
    missing: str | None = None
    detail: str | None = None
    hint: str | None = None


def discover_repo_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / "libs/core/kiln_ai").exists() and (
            candidate / "libs/server/kiln_server"
        ).exists():
            return candidate
    return None


def add_repo_paths(repo_root: Path | None) -> None:
    if repo_root is None:
        return
    for rel in ("libs/core", "libs/server"):
        package_root = repo_root / rel
        if package_root.exists():
            value = str(package_root)
            if value not in sys.path:
                sys.path.insert(0, value)


def root_package(name: str | None) -> str | None:
    if not name:
        return None
    return name.split(".", maxsplit=1)[0]


def import_one(module: str) -> ImportResult:
    try:
        importlib.import_module(module)
    except ModuleNotFoundError as exc:
        missing = exc.name or str(exc)
        root = root_package(missing)
        return ImportResult(
            module=module,
            status="missing_dependency",
            missing=missing,
            detail=str(exc),
            hint=KNOWN_DEPENDENCY_HINTS.get(root or ""),
        )
    except Exception as exc:  # noqa: BLE001 - importer should report all import-time failures
        return ImportResult(
            module=module,
            status="error",
            detail=f"{type(exc).__name__}: {exc}",
        )
    return ImportResult(module=module, status="ok")


def print_plain(results: Iterable[ImportResult]) -> None:
    ok_count = 0
    missing_count = 0
    error_count = 0
    for result in results:
        if result.status == "ok":
            ok_count += 1
            print(f"OK {result.module}")
        elif result.status == "missing_dependency":
            missing_count += 1
            message = f"MISSING {result.module}: {result.missing}"
            if result.hint:
                message = f"{message} ({result.hint})"
            print(message)
        else:
            error_count += 1
            print(f"ERROR {result.module}: {result.detail}")

    print(
        f"Summary: {ok_count} ok, {missing_count} missing dependency, {error_count} import error"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import-check Kiln document/RAG modules without network calls."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Optional Kiln checkout root. When omitted, the script auto-detects it from its own location.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of plain text.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero for missing dependencies as well as import errors.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root or discover_repo_root(Path(__file__).resolve())
    add_repo_paths(repo_root)

    results = [import_one(module) for module in TARGET_MODULES]

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
    else:
        print_plain(results)

    has_errors = any(result.status == "error" for result in results)
    has_missing = any(result.status == "missing_dependency" for result in results)
    if has_errors or (args.strict and has_missing):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
