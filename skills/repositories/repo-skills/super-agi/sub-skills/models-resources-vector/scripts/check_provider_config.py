#!/usr/bin/env python3
"""Check SuperAGI provider/vector/resource config combinations without network calls.

Example:
  python check_provider_config.py --config config.yaml --provider openai
  python check_provider_config.py --config config.yaml --vector-store pinecone --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: PyYAML. Install with `python -m pip install PyYAML`.", file=sys.stderr)
    raise SystemExit(2)

PROVIDER_KEYS = {
    "openai": ["OPENAI_API_KEY"],
    "google palm": ["PALM_API_KEY"],
    "replicate": ["REPLICATE_API_TOKEN"],
    "hugging face": ["HUGGING_API_TOKEN"],
    "local llm": ["OPENAI_API_BASE"],
}
VECTOR_KEYS = {
    "pinecone": ["PINECONE_API_KEY", "PINECONE_ENVIRONMENT"],
    "weaviate": ["WEAVIATE_USE_EMBEDDED"],
    "qdrant": ["QDRANT_HOST_NAME", "QDRANT_PORT"],
    "redis": ["REDIS_URL"],
    "chroma": ["CHROMA_HOST_NAME", "CHROMA_PORT"],
}


def missing_or_placeholder(data: dict, key: str) -> bool:
    value = data.get(key)
    if value is None:
        return True
    if isinstance(value, str):
        stripped = value.strip()
        return stripped == "" or stripped.startswith("YOUR_") or stripped in {"YOUR_OPEN_API_KEY", "YOUR_SERPER_API_KEY"}
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SuperAGI provider/vector/resource config shape")
    parser.add_argument("--config", required=True)
    parser.add_argument("--provider", help="Provider name such as openai, replicate, google palm, hugging face, local llm")
    parser.add_argument("--vector-store", help="Vector store name such as pinecone, weaviate, qdrant, redis, chroma")
    parser.add_argument("--storage", help="Storage type FILE or S3; defaults to config value")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    path = Path(args.config)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    if data is None:
        data = {}
    if not isinstance(data, dict):
        print("config must be a YAML mapping", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    provider = args.provider.lower().strip() if args.provider else None
    vector = args.vector_store.lower().strip() if args.vector_store else None
    storage = (args.storage or data.get("STORAGE_TYPE") or "").upper()

    if provider:
        if provider not in PROVIDER_KEYS:
            errors.append(f"unknown provider {provider!r}; expected {sorted(PROVIDER_KEYS)}")
        else:
            for key in PROVIDER_KEYS[provider]:
                if missing_or_placeholder(data, key):
                    errors.append(f"provider {provider!r} needs non-placeholder {key}")
    if vector:
        if vector not in VECTOR_KEYS:
            errors.append(f"unknown vector store {vector!r}; expected {sorted(VECTOR_KEYS)}")
        else:
            for key in VECTOR_KEYS[vector]:
                if missing_or_placeholder(data, key):
                    warnings.append(f"vector store {vector!r} may need {key}; value is missing or placeholder")
    if storage:
        if storage not in {"FILE", "S3"}:
            errors.append(f"storage must be FILE or S3, got {storage!r}")
        elif storage == "S3":
            for key in ["BUCKET_NAME", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]:
                if missing_or_placeholder(data, key):
                    errors.append(f"S3 storage needs non-placeholder {key}")

    result = {"ok": not errors, "errors": errors, "warnings": warnings, "provider": provider, "vector_store": vector, "storage": storage}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("OK" if result["ok"] else "NOT OK")
        for item in errors:
            print(f"ERROR: {item}")
        for item in warnings:
            print(f"WARN: {item}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
