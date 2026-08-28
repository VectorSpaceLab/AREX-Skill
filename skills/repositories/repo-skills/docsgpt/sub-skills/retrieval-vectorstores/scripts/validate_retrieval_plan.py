#!/usr/bin/env python3
"""Validate a DocsGPT vector-store/retriever feature combination offline."""

from __future__ import annotations

import argparse
import sys

STORES = {"faiss", "elasticsearch", "mongodb", "qdrant", "milvus", "pgvector"}
RETRIEVERS = {"classic", "default", "hybrid", "graphrag"}
THRESHOLD_STORES = {"pgvector", "mongodb"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vector-store", required=True, choices=sorted(STORES))
    parser.add_argument("--retriever", default="classic", choices=sorted(RETRIEVERS))
    parser.add_argument("--graphrag-enabled", action="store_true")
    parser.add_argument("--score-threshold", type=float)
    parser.add_argument("--embedding-dimension", type=int)
    parser.add_argument("--existing-dimension", type=int)
    parser.add_argument("--require-keyword", action="store_true", help="Require a real keyword half for hybrid retrieval")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    if args.retriever == "graphrag":
        if args.vector_store != "pgvector":
            errors.append("GraphRAG requires vector-store=pgvector")
        if not args.graphrag_enabled:
            errors.append("GraphRAG requires --graphrag-enabled")
    if args.graphrag_enabled and args.vector_store != "pgvector":
        errors.append("GRAPHRAG_ENABLED is incompatible with a non-pgvector plan")
    if args.retriever == "hybrid" and args.vector_store != "pgvector":
        message = "hybrid keyword retrieval is pgvector-only; this plan degrades to vector-only behavior"
        (errors if args.require_keyword else warnings).append(message)
    if args.score_threshold is not None and args.vector_store not in THRESHOLD_STORES:
        warnings.append(f"score_threshold is not honored by {args.vector_store}")
    if args.embedding_dimension is not None and args.embedding_dimension < 1:
        errors.append("embedding dimension must be positive")
    if args.existing_dimension is not None and args.existing_dimension < 1:
        errors.append("existing dimension must be positive")
    if (
        args.embedding_dimension is not None
        and args.existing_dimension is not None
        and args.embedding_dimension != args.existing_dimension
    ):
        errors.append("embedding dimension changed; provision a matching target and re-embed/re-ingest")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Retrieval plan is structurally compatible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
