#!/usr/bin/env python3
"""Build and query a tiny in-memory LlamaIndex index with no network calls."""

from __future__ import annotations


def main() -> None:
    from llama_index.core import Document, Settings, VectorStoreIndex
    from llama_index.core.embeddings.mock_embed_model import MockEmbedding
    from llama_index.core.llms.mock import MockLLM

    Settings.embed_model = MockEmbedding(embed_dim=8)
    Settings.llm = MockLLM(max_tokens=64)

    documents = [
        Document(text="LlamaIndex indexes transform documents into searchable nodes."),
        Document(text="Retrievers select relevant nodes before response synthesis."),
        Document(text="StorageContext can persist index, docstore, and vector data."),
    ]

    index = VectorStoreIndex.from_documents(documents)
    retriever = index.as_retriever(similarity_top_k=2)
    nodes = retriever.retrieve("How does querying use retrievers?")

    query_engine = index.as_query_engine(similarity_top_k=2, response_mode="compact")
    response = query_engine.query("How does querying use retrievers?")

    print(f"retrieved_nodes={len(nodes)}")
    print(f"response={response}")


if __name__ == "__main__":
    try:
        main()
    except ImportError as exc:
        raise SystemExit(
            "This script requires llama-index-core with MockEmbedding and MockLLM. "
            "Install/verify llama-index-core, or adapt the script to pass another "
            "local embedding model and local/mock LLM. Original import error: "
            f"{exc}"
        ) from exc
