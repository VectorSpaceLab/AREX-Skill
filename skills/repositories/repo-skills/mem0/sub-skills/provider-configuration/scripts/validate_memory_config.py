#!/usr/bin/env python3
"""Read-only validation for Mem0 Python OSS MemoryConfig dictionaries."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROVIDER_DEPENDENCY_HINTS: Dict[Tuple[str, str], List[str]] = {
    ("vector_store", "chroma"): ["chromadb"],
    ("vector_store", "faiss"): ["faiss"],
    ("vector_store", "pgvector"): ["psycopg"],
    ("vector_store", "redis"): ["redis"],
    ("vector_store", "valkey"): ["valkey"],
    ("vector_store", "elasticsearch"): ["elasticsearch"],
    ("vector_store", "opensearch"): ["opensearchpy"],
    ("vector_store", "milvus"): ["pymilvus"],
    ("vector_store", "mongodb"): ["pymongo"],
    ("vector_store", "weaviate"): ["weaviate"],
    ("vector_store", "pinecone"): ["pinecone"],
    ("vector_store", "upstash_vector"): ["upstash_vector"],
    ("vector_store", "azure_ai_search"): ["azure.search.documents"],
    ("embedder", "fastembed"): ["fastembed"],
    ("embedder", "huggingface"): ["sentence_transformers"],
    ("embedder", "ollama"): ["ollama"],
    ("embedder", "aws_bedrock"): ["boto3"],
    ("llm", "ollama"): ["ollama"],
    ("llm", "groq"): ["groq"],
    ("llm", "litellm"): ["litellm"],
    ("llm", "together"): ["together"],
    ("llm", "aws_bedrock"): ["boto3"],
    ("llm", "langchain"): ["langchain"],
    ("reranker", "sentence_transformer"): ["sentence_transformers"],
    ("reranker", "huggingface"): ["sentence_transformers"],
    ("reranker", "cohere"): ["cohere"],
}

REMOVED_GRAPH_KEYS = {"enable_graph", "graph_store", "enableGraph", "graphStore"}
PYTHON_PROVIDER_KEYS = {"vector_store", "embedder", "llm", "reranker"}
TS_STYLE_KEYS = {"vectorStore", "historyDbPath", "customInstructions"}
STATIC_PROVIDERS: Dict[str, set] = {
    "vector_store": {
        "azure_ai_search",
        "azure_mysql",
        "baidu",
        "cassandra",
        "chroma",
        "databricks",
        "elasticsearch",
        "faiss",
        "langchain",
        "milvus",
        "mongodb",
        "neptune",
        "opensearch",
        "pgvector",
        "pinecone",
        "qdrant",
        "redis",
        "s3_vectors",
        "supabase",
        "turbopuffer",
        "upstash_vector",
        "valkey",
        "vertex_ai_vector_search",
        "weaviate",
    },
    "embedder": {
        "aws_bedrock",
        "azure_openai",
        "fastembed",
        "gemini",
        "huggingface",
        "langchain",
        "lmstudio",
        "ollama",
        "openai",
        "together",
        "upstash_vector",
        "vertexai",
    },
    "llm": {
        "anthropic",
        "aws_bedrock",
        "azure_openai",
        "azure_openai_structured",
        "deepseek",
        "gemini",
        "groq",
        "langchain",
        "litellm",
        "lmstudio",
        "minimax",
        "ollama",
        "openai",
        "openai_structured",
        "sarvam",
        "together",
        "vllm",
        "xai",
    },
    "reranker": {"cohere", "huggingface", "llm_reranker", "sentence_transformer", "zero_entropy"},
}


def load_config(path: str) -> Dict[str, Any]:
    if path == "-":
        raw = sys.stdin.read()
        source = "stdin"
    else:
        raw = Path(path).read_text(encoding="utf-8")
        source = path
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{source}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{source}: top-level config must be a JSON object")
    return value


def provider_name(config: Dict[str, Any], section: str) -> Optional[str]:
    block = config.get(section)
    if isinstance(block, dict):
        provider = block.get("provider")
        if provider is not None:
            return str(provider)
    return None


def import_check(config: Dict[str, Any]) -> List[str]:
    messages: List[str] = []
    for section in PYTHON_PROVIDER_KEYS:
        provider = provider_name(config, section)
        if not provider:
            continue
        hints = PROVIDER_DEPENDENCY_HINTS.get((section, provider), [])
        for module_name in hints:
            try:
                importlib.import_module(module_name)
            except Exception as exc:
                messages.append(
                    f"missing optional dependency for {section}.{provider}: import {module_name!r} failed ({exc.__class__.__name__})"
                )
    return messages


def dimension_warnings(config: Dict[str, Any]) -> List[str]:
    messages: List[str] = []
    vector_config = config.get("vector_store", {}).get("config", {}) if isinstance(config.get("vector_store"), dict) else {}
    embedder_config = config.get("embedder", {}).get("config", {}) if isinstance(config.get("embedder"), dict) else {}
    if not isinstance(vector_config, dict) or not isinstance(embedder_config, dict):
        return messages

    vector_dim = vector_config.get("embedding_model_dims") or vector_config.get("dimension")
    embedder_dim = embedder_config.get("embedding_dims") or embedder_config.get("embeddingDims")
    if vector_dim and embedder_dim and int(vector_dim) != int(embedder_dim):
        messages.append(f"dimension mismatch: vector_store dimension {vector_dim} != embedder dimension {embedder_dim}")
    if "dimension" in vector_config and "embedding_model_dims" not in vector_config:
        messages.append("Python vector store configs usually use embedding_model_dims; dimension is TypeScript-style")
    if "embeddingDims" in embedder_config and "embedding_dims" not in embedder_config:
        messages.append("Python embedder configs usually use embedding_dims; embeddingDims is TypeScript-style")
    return messages


def static_warnings(config: Dict[str, Any]) -> List[str]:
    messages: List[str] = []
    for key in sorted(REMOVED_GRAPH_KEYS & set(config.keys())):
        messages.append(f"removed graph config key present: {key}; current OSS graph memory is built-in entity linking")
    for key in sorted(TS_STYLE_KEYS & set(config.keys())):
        messages.append(f"TypeScript-style key in Python config: {key}")
    for section in PYTHON_PROVIDER_KEYS:
        block = config.get(section)
        if block is not None and not isinstance(block, dict):
            messages.append(f"{section} must be an object with provider/config fields")
    messages.extend(dimension_warnings(config))
    return messages


def add_import_roots(roots: List[str]) -> List[str]:
    added: List[str] = []
    for root in roots:
        if not root:
            continue
        path = Path(root).expanduser().resolve()
        if not path.exists():
            continue
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
            added.append(str(path))
    return added


def static_validate(config: Dict[str, Any]) -> Tuple[bool, str]:
    errors: List[str] = []
    for section, allowed in STATIC_PROVIDERS.items():
        block = config.get(section)
        if block is None:
            continue
        if not isinstance(block, dict):
            errors.append(f"{section} must be an object")
            continue
        provider = block.get("provider")
        if provider is not None and str(provider) not in allowed:
            errors.append(f"unsupported {section} provider: {provider}")
        provider_config = block.get("config")
        if provider_config is not None and not isinstance(provider_config, dict):
            errors.append(f"{section}.config must be an object when supplied as JSON")

    vector_provider = provider_name(config, "vector_store")
    vector_config = config.get("vector_store", {}).get("config", {}) if isinstance(config.get("vector_store"), dict) else {}
    if isinstance(vector_config, dict):
        if vector_provider == "chroma":
            has_cloud = bool(vector_config.get("api_key") and vector_config.get("tenant"))
            has_local = bool(vector_config.get("path") or (vector_config.get("host") and vector_config.get("port")))
            if has_cloud and has_local:
                errors.append("chroma config cannot mix cloud api_key/tenant with local path or host/port")
        if vector_provider == "pgvector":
            has_connection = bool(vector_config.get("connection_pool") or vector_config.get("connection_string"))
            has_parts = bool(vector_config.get("user") and vector_config.get("password") and vector_config.get("host") and vector_config.get("port"))
            if not has_connection and not has_parts:
                errors.append("pgvector config needs connection_pool, connection_string, or user/password/host/port")
        if vector_provider == "faiss" and vector_config.get("distance_strategy"):
            if vector_config["distance_strategy"] not in {"euclidean", "inner_product", "cosine"}:
                errors.append("faiss distance_strategy must be euclidean, inner_product, or cosine")

    if errors:
        return False, "; ".join(errors)
    return True, "static validation passed; install mem0ai or use --package-root with installed metadata for full Pydantic validation"


def pydantic_validate(config: Dict[str, Any]) -> Tuple[Optional[bool], str]:
    try:
        from mem0.configs.base import MemoryConfig
    except Exception as exc:
        return None, f"could not import mem0.configs.base.MemoryConfig: {exc}"
    try:
        parsed = MemoryConfig(**config)
    except Exception as exc:
        return False, str(exc)
    summary = {
        "vector_store": getattr(parsed.vector_store, "provider", None),
        "embedder": getattr(parsed.embedder, "provider", None),
        "llm": getattr(parsed.llm, "provider", None),
        "reranker": getattr(parsed.reranker, "provider", None) if parsed.reranker else None,
        "version": parsed.version,
    }
    return True, json.dumps(summary, sort_keys=True)


def env_presence(names: List[str]) -> Dict[str, str]:
    return {name: "set" if os.environ.get(name) else "missing" for name in names}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to JSON config file, or '-' for stdin.")
    parser.add_argument(
        "--package-root",
        action="append",
        default=[],
        help="Optional directory to add to sys.path before importing mem0, useful for an editable checkout or unpacked wheel.",
    )
    parser.add_argument("--import-check", action="store_true", help="Check likely optional dependency imports.")
    parser.add_argument(
        "--env",
        nargs="*",
        default=[],
        metavar="NAME",
        help="Report presence/absence of environment variables without printing values.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    args = parser.parse_args()

    config = load_config(args.config)
    added_roots = add_import_roots(args.package_root)
    warnings = static_warnings(config)
    valid, validation_message = pydantic_validate(config)
    validation_mode = "pydantic"
    if valid is None:
        validation_mode = "static"
        static_valid, static_message = static_validate(config)
        valid = static_valid
        validation_message = f"{validation_message}; {static_message}"
    dependency_messages = import_check(config) if args.import_check else []
    env = env_presence(args.env)

    result = {
        "valid": valid,
        "validation_mode": validation_mode,
        "validation": validation_message,
        "warnings": warnings,
        "dependency_messages": dependency_messages,
        "env": env,
        "import_roots_added_count": len(added_roots),
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"valid: {valid}")
        print(f"validation-mode: {validation_mode}")
        print(f"validation: {validation_message}")
        for warning in warnings:
            print(f"warning: {warning}")
        for message in dependency_messages:
            print(f"dependency: {message}")
        for name, state in env.items():
            print(f"env: {name}={state}")
        if added_roots:
            print(f"import-roots-added-count: {len(added_roots)}")

    return 0 if valid and not dependency_messages else 1


if __name__ == "__main__":
    sys.exit(main())
