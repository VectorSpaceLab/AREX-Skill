#!/usr/bin/env python3
"""Attach `RAGMiddleware` to an Agent and exercise static and agentic modes.

Prerequisites:
    - AgentScope installed with the RAG-related extras used by the script.
    - `DASHSCOPE_API_KEY` set for both the chat and embedding models.
"""
from __future__ import annotations

import asyncio
import os

from agentscope.agent import Agent
from agentscope.credential import DashScopeCredential
from agentscope.embedding import DashScopeEmbeddingModel
from agentscope.message import UserMsg
from agentscope.middleware import RAGMiddleware
from agentscope.model import DashScopeChatModel
from agentscope.rag import (
    ApproxTokenChunker,
    KnowledgeBase,
    QdrantStore,
    TextParser,
)
from agentscope.tool import Toolkit


COLLECTION = "demo-kb"

KNOWLEDGE: dict[str, bytes] = {
    "company-policy.md": (
        b"# Acme Remote Work Policy\n\n"
        b"Employees may work remotely up to three days per week. "
        b"Wednesdays are mandatory in-office days for the whole "
        b"engineering org so cross-team syncs land on a predictable "
        b"day.\n\n"
        b"Equipment stipend: each new hire receives a USD 1,500 "
        b"one-off stipend for a home-office setup. Receipts must be "
        b"submitted within 90 days of the start date.\n"
    ),
    "release-notes.md": (
        b"# AgentScope release notes\n\n"
        b"- New `agentscope.rag` module: pluggable parser, chunker, "
        b"embedding, and vector-store backends.\n"
        b"- `RAGMiddleware` ships in two modes -- `static` for "
        b"automatic injection, `agentic` for tool-driven search.\n"
    ),
}


async def index_corpus(knowledge: KnowledgeBase) -> None:
    parser = TextParser()
    chunker = ApproxTokenChunker(chunk_size=256, overlap=32)
    for filename, file_bytes in KNOWLEDGE.items():
        sections = await parser.parse(file=file_bytes, filename=filename)
        chunks = await chunker.chunk(sections)
        await knowledge.insert_document(
            chunks,
            document_metadata={"filename": filename},
        )


async def ask(agent: Agent, question: str) -> None:
    print(f"\n[{agent.name}] user: {question}")
    reply = await agent.reply(UserMsg(name="user", content=question))
    print(f"[{agent.name}] assistant: {reply.get_text_content()}")


async def main() -> None:
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("Set DASHSCOPE_API_KEY before running this demo.")

    credential = DashScopeCredential(api_key=api_key)
    chat_model = DashScopeChatModel(
        credential=credential,
        model="qwen-plus",
        stream=False,
    )
    embedding_model = DashScopeEmbeddingModel(
        credential=credential,
        model="text-embedding-v4",
        dimensions=1024,
    )

    store = QdrantStore(location=":memory:")
    async with store:
        knowledge = KnowledgeBase(
            name="acme-handbook",
            description="Acme HR policies and release notes.",
            embedding_model=embedding_model,
            vector_store=store,
            collection=COLLECTION,
        )
        await index_corpus(knowledge)

        static_mw = RAGMiddleware(
            knowledge_bases=[knowledge],
            parameters=RAGMiddleware.Parameters(
                mode="static",
                top_k=3,
                emit_hint_event=False,
            ),
        )
        static_agent = Agent(
            name="rag-static-agent",
            system_prompt=(
                "You are a concise assistant. Use matched context when available."
            ),
            model=chat_model,
            toolkit=Toolkit(),
            middlewares=[static_mw],
        )
        await ask(static_agent, "How many remote days per week does Acme allow?")

        agentic_mw = RAGMiddleware(
            knowledge_bases=[knowledge],
            parameters=RAGMiddleware.Parameters(mode="agentic", top_k=3),
        )
        agentic_agent = Agent(
            name="rag-agentic-agent",
            system_prompt=(
                "You are a concise assistant. Use the search_knowledge tool when needed."
            ),
            model=chat_model,
            toolkit=Toolkit(),
            middlewares=[agentic_mw],
        )
        await ask(agentic_agent, "Summarise what's new in the release notes.")


if __name__ == "__main__":
    asyncio.run(main())
