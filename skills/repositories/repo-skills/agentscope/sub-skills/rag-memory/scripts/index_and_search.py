#!/usr/bin/env python3
"""Standalone RAG indexing and search demo.

Prerequisites:
    - AgentScope installed with the RAG-related extras used by the script.
    - `DASHSCOPE_API_KEY` set for the embedding model.

The script builds a tiny in-memory corpus, parses it, chunks it, indexes it in
Qdrant, and runs a couple of searches.
"""
from __future__ import annotations

import asyncio
import os

from agentscope.credential import DashScopeCredential
from agentscope.embedding import DashScopeEmbeddingModel
from agentscope.message import TextBlock
from agentscope.rag import (
    ApproxTokenChunker,
    KnowledgeBase,
    QdrantStore,
    TextParser,
)


COLLECTION = "demo-kb"

DOCUMENTS: dict[str, bytes] = {
    "cats.md": (
        b"# Cats\n\n"
        b"Cats are small carnivorous mammals. They are popular as pets "
        b"because of their playful and affectionate nature.\n\n"
        b"Domestic cats sleep around 12-16 hours per day. They are most "
        b"active at dawn and dusk (crepuscular behaviour).\n"
    ),
    "agentscope.md": (
        b"# AgentScope\n\n"
        b"AgentScope is a developer-centric framework for building "
        b"multi-agent LLM applications. It emphasises transparency, "
        b"controllability, and a clear separation between agent logic "
        b"and infrastructure.\n\n"
        b"Its RAG module ships a parser/chunker/embedding/vector-store "
        b"pipeline that can be wired up without the FastAPI service.\n"
    ),
}


async def build_index(
    knowledge: KnowledgeBase,
    parser: TextParser,
    chunker: ApproxTokenChunker,
) -> None:
    for filename, file_bytes in DOCUMENTS.items():
        sections = await parser.parse(file=file_bytes, filename=filename)
        chunks = await chunker.chunk(sections)
        document_id = await knowledge.insert_document(
            chunks,
            document_metadata={"filename": filename},
        )
        print(
            f"indexed {filename!r} as document_id={document_id} ({len(chunks)} chunk(s))",
        )


async def search(
    knowledge: KnowledgeBase,
    query: str,
    top_k: int = 3,
) -> None:
    results = await knowledge.search(queries=[query], top_k=top_k)

    print(f"\nQuery: {query!r}")
    if not results:
        print("  (no hits)")
        return

    for rank, result in enumerate(results, start=1):
        snippet = (
            result.chunk.content.text
            if isinstance(result.chunk.content, TextBlock)
            else "<non-text chunk>"
        )
        snippet = snippet.replace("\n", " ").strip()
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        print(
            f"  [{rank}] score={result.score:.4f} source={result.chunk.source} document_id={result.document_id}\n"
            f"      {snippet}",
        )


async def main() -> None:
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("Set DASHSCOPE_API_KEY before running this demo.")

    embedding_model = DashScopeEmbeddingModel(
        credential=DashScopeCredential(api_key=api_key),
        model="text-embedding-v4",
        dimensions=1024,
    )
    parser = TextParser()
    chunker = ApproxTokenChunker(chunk_size=256, overlap=32)
    store = QdrantStore(location=":memory:")

    async with store:
        knowledge = KnowledgeBase(
            name="demo-kb",
            description="A toy corpus on cats and AgentScope.",
            embedding_model=embedding_model,
            vector_store=store,
            collection=COLLECTION,
        )

        print("Indexing demo corpus ...")
        await build_index(knowledge, parser, chunker)
        await search(knowledge, "When are cats most active?")
        await search(knowledge, "What framework lets me build multi-agent apps?")


if __name__ == "__main__":
    asyncio.run(main())
