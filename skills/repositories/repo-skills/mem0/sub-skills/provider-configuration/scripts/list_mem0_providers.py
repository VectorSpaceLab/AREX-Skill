#!/usr/bin/env python3
"""List Mem0 OSS provider registry names without constructing providers."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any, Dict, Iterable, List

STATIC_FALLBACKS: Dict[str, List[str]] = {
    "llms": [
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
    ],
    "embedders": [
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
    ],
    "vector_stores": [
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
    ],
    "rerankers": [
        "cohere",
        "huggingface",
        "llm_reranker",
        "sentence_transformer",
        "zero_entropy",
    ],
}


def sorted_keys(value: Any) -> List[str]:
    if isinstance(value, dict):
        return sorted(str(key) for key in value.keys())
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return sorted(str(item) for item in value)
    return []


def inspect_installed() -> Dict[str, List[str]]:
    providers: Dict[str, List[str]] = {}
    try:
        factory = importlib.import_module("mem0.utils.factory")
    except Exception:
        return dict(STATIC_FALLBACKS)

    mappings = {
        "llms": ("LlmFactory", "provider_to_class"),
        "embedders": ("EmbedderFactory", "provider_to_class"),
        "vector_stores": ("VectorStoreFactory", "provider_to_class"),
        "rerankers": ("RerankerFactory", "provider_to_class"),
    }
    for output_name, (class_name, attr_name) in mappings.items():
        try:
            factory_class = getattr(factory, class_name)
            providers[output_name] = sorted_keys(getattr(factory_class, attr_name))
        except Exception:
            providers[output_name] = STATIC_FALLBACKS[output_name]

    try:
        vector_config = importlib.import_module("mem0.vector_stores.configs").VectorStoreConfig
        providers["vector_store_config_validators"] = sorted_keys(getattr(vector_config, "_provider_configs", {}))
    except Exception:
        providers["vector_store_config_validators"] = STATIC_FALLBACKS["vector_stores"]

    return providers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--category",
        choices=["llms", "embedders", "vector_stores", "rerankers", "all"],
        default="all",
        help="Limit output to one provider category.",
    )
    parser.add_argument(
        "--static",
        action="store_true",
        help="Use bundled fallback provider lists instead of importing mem0.",
    )
    args = parser.parse_args()

    providers = dict(STATIC_FALLBACKS) if args.static else inspect_installed()
    if args.category != "all":
        providers = {args.category: providers.get(args.category, [])}

    if args.json:
        print(json.dumps(providers, indent=2, sort_keys=True))
    else:
        for category, names in providers.items():
            print(f"{category} ({len(names)}):")
            for name in names:
                print(f"  - {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
