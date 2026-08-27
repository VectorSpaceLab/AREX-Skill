#!/usr/bin/env python3
"""No-network Langroid environment check.

This helper verifies importability, core config defaults, and optional-dependency
availability without making provider calls, launching services, downloading
models, or writing outside the current process.
"""

from __future__ import annotations

import argparse
import importlib
import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check a Langroid install without network or services.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--optional",
        action="store_true",
        help="Probe optional modules and report missing extras as non-fatal findings.",
    )
    return parser


def try_import(module: str) -> dict[str, Any]:
    try:
        importlib.import_module(module)
        return {"module": module, "ok": True, "error": None}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run(probe_optional: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "ok": True,
        "api_calls_made": False,
        "version": None,
        "core": {},
        "imports": [],
        "optional": [],
        "warnings": [],
    }

    try:
        report["version"] = version("langroid")
    except PackageNotFoundError:
        report["ok"] = False
        report["warnings"].append("Distribution metadata for 'langroid' was not found.")

    core_modules = [
        "langroid",
        "langroid.agent.chat_agent",
        "langroid.agent.task",
        "langroid.agent.tool_message",
        "langroid.language_models.openai_gpt",
        "langroid.language_models.mock_lm",
        "langroid.agent.special.doc_chat_agent",
        "langroid.vector_store.base",
        "langroid.agent.tools.mcp.fastmcp_client",
    ]
    for module in core_modules:
        item = try_import(module)
        report["imports"].append(item)
        if not item["ok"]:
            report["ok"] = False

    if report["ok"]:
        import langroid as lr
        from langroid.agent.task import TaskConfig
        from langroid.agent.chat_agent import ChatAgentConfig
        from langroid.agent.special.doc_chat_agent import DocChatAgentConfig
        from langroid.language_models.openai_gpt import OpenAIGPTConfig
        from langroid.vector_store.base import VectorStoreConfig

        report["core"] = {
            "ChatAgent": str(lr.ChatAgent),
            "Task": str(lr.Task),
            "ToolMessage": str(lr.ToolMessage),
            "ChatAgentConfig.use_tools": ChatAgentConfig().use_tools,
            "ChatAgentConfig.use_functions_api": ChatAgentConfig().use_functions_api,
            "TaskConfig.done_sequences": TaskConfig().done_sequences,
            "OpenAIGPTConfig.chat_model": OpenAIGPTConfig().chat_model,
            "OpenAIGPTConfig.timeout": OpenAIGPTConfig().timeout,
            "DocChatAgentConfig.n_relevant_chunks": DocChatAgentConfig().n_relevant_chunks,
            "VectorStoreConfig.full_eval": VectorStoreConfig().full_eval,
        }

    if probe_optional:
        optional_modules = [
            "sqlalchemy",
            "pymysql",
            "psycopg2",
            "neo4j",
            "arango",
            "chainlit",
            "lancedb",
            "chromadb",
            "weaviate",
            "pinecone",
            "pgvector",
            "sentence_transformers",
            "torch",
            "docling",
            "pypdf",
            "fitz",
            "pymupdf4llm",
            "markitdown",
            "unstructured",
            "crawl4ai",
            "fastmcp",
        ]
        report["optional"] = [try_import(module) for module in optional_modules]

    return report


def main() -> int:
    args = build_parser().parse_args()
    report = run(args.optional)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Langroid version: {report['version']}")
        print(f"Core ok: {report['ok']}")
        for item in report["imports"]:
            status = "ok" if item["ok"] else item["error"]
            print(f"  {item['module']}: {status}")
        if report["optional"]:
            print("Optional modules:")
            for item in report["optional"]:
                status = "ok" if item["ok"] else "missing"
                print(f"  {item['module']}: {status}")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
