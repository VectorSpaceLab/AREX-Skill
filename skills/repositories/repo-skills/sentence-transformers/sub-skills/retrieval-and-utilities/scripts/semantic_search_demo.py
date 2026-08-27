#!/usr/bin/env python3
"""Tiny semantic-search demo for sentence-transformers utilities.

The default --toy-tensors mode avoids network and model downloads. Pass --model to
run the same retrieval pattern with a local or downloadable SentenceTransformer.
"""

from __future__ import annotations

import argparse
from typing import Iterable


CORPUS = [
    "Neural networks learn representations from data.",
    "Mars rovers collect scientific measurements on another planet.",
    "Solar and wind power are renewable energy sources.",
    "A cross encoder can rerank retrieved candidates.",
]
QUERIES = [
    "How do machine learning models represent information?",
    "What explores Mars?",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny sentence-transformers semantic_search demo.",
    )
    parser.add_argument(
        "--toy-tensors",
        action="store_true",
        help="Use deterministic precomputed tensors and avoid loading any model. This is the default when --model is omitted.",
    )
    parser.add_argument(
        "--model",
        help="SentenceTransformer model name or local path. May download unless --local-files-only is used.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Only load the supplied model from local cache/files.",
    )
    parser.add_argument("--top-k", type=int, default=2, help="Number of corpus hits per query.")
    parser.add_argument(
        "--score-function",
        choices=["cosine", "dot"],
        default="cosine",
        help="Similarity function for semantic_search. Use dot only for normalized embeddings.",
    )
    parser.add_argument("--query-chunk-size", type=int, default=100, help="semantic_search query chunk size.")
    parser.add_argument("--corpus-chunk-size", type=int, default=500000, help="semantic_search corpus chunk size.")
    return parser.parse_args()


def toy_embeddings():
    import torch

    corpus_embeddings = torch.tensor(
        [
            [0.95, 0.05, 0.00, 0.00],
            [0.00, 0.95, 0.05, 0.00],
            [0.00, 0.00, 0.95, 0.05],
            [0.45, 0.00, 0.00, 0.89],
        ],
        dtype=torch.float32,
    )
    query_embeddings = torch.tensor(
        [
            [0.90, 0.10, 0.00, 0.00],
            [0.00, 0.90, 0.10, 0.00],
        ],
        dtype=torch.float32,
    )
    return query_embeddings, corpus_embeddings


def model_embeddings(model_name_or_path: str, local_files_only: bool):
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name_or_path, local_files_only=local_files_only)
    encode_document = getattr(model, "encode_document", model.encode)
    encode_query = getattr(model, "encode_query", model.encode)
    corpus_embeddings = encode_document(CORPUS, convert_to_tensor=True, normalize_embeddings=True)
    query_embeddings = encode_query(QUERIES, convert_to_tensor=True, normalize_embeddings=True)
    return query_embeddings, corpus_embeddings


def print_hits(hits_by_query: Iterable[list[dict[str, int | float]]]) -> None:
    for query, hits in zip(QUERIES, hits_by_query):
        print(f"\nQuery: {query}")
        for rank, hit in enumerate(hits, start=1):
            corpus_id = int(hit["corpus_id"])
            score = float(hit["score"])
            print(f"{rank}. corpus_id={corpus_id} score={score:.4f} text={CORPUS[corpus_id]}")


def main() -> None:
    args = parse_args()

    from sentence_transformers.util import cos_sim, dot_score, semantic_search
    if args.top_k <= 0:
        raise SystemExit("--top-k must be positive")
    if args.query_chunk_size <= 0 or args.corpus_chunk_size <= 0:
        raise SystemExit("chunk sizes must be positive")

    if args.model:
        query_embeddings, corpus_embeddings = model_embeddings(args.model, args.local_files_only)
    else:
        query_embeddings, corpus_embeddings = toy_embeddings()

    score_function = cos_sim if args.score_function == "cosine" else dot_score
    hits_by_query = semantic_search(
        query_embeddings=query_embeddings,
        corpus_embeddings=corpus_embeddings,
        top_k=min(args.top_k, len(CORPUS)),
        query_chunk_size=args.query_chunk_size,
        corpus_chunk_size=args.corpus_chunk_size,
        score_function=score_function,
    )
    print_hits(hits_by_query)


if __name__ == "__main__":
    main()
