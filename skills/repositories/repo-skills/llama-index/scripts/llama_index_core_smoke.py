#!/usr/bin/env python3
"""Run a tiny LlamaIndex core smoke check with mock models and no network calls."""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", default="What does LlamaIndex connect?", help="Question for the tiny query engine.")
    args = parser.parse_args()

    try:
        from llama_index.core import Document, Settings, VectorStoreIndex
        from llama_index.core.embeddings import MockEmbedding
        from llama_index.core.llms import MockLLM
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        print(f"LlamaIndex core import failed: {type(exc).__name__}: {exc}")
        print("Install `llama-index-core` or `llama-index`, then retry in that Python environment.")
        return 1

    Settings.llm = MockLLM(max_tokens=32)
    Settings.embed_model = MockEmbedding(embed_dim=8)
    index = VectorStoreIndex.from_documents(
        [Document(text="LlamaIndex connects private data to LLM applications through indexes, retrievers, query engines, and agents.")]
    )
    retriever = index.as_retriever(similarity_top_k=1)
    nodes = retriever.retrieve(args.question)
    query_engine = index.as_query_engine(similarity_top_k=1)
    response = query_engine.query(args.question)
    print(f"retrieved_nodes={len(nodes)}")
    print(f"response={response}")
    return 0 if nodes else 2


if __name__ == "__main__":
    raise SystemExit(main())
