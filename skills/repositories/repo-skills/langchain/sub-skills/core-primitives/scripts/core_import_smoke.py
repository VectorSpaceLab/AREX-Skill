#!/usr/bin/env python3
"""Non-mutating smoke check for core LangChain primitives."""

from __future__ import annotations

import asyncio
import json
from typing import Any


def main() -> None:
    from langchain_core.documents import Document
    from langchain_core.embeddings import Embeddings
    from langchain_core.messages import (
        AIMessage,
        HumanMessage,
        message_to_dict,
        messages_from_dict,
        messages_to_dict,
    )
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnableConfig, RunnableLambda
    from langchain_core.tools import tool
    from langchain_core.vectorstores import InMemoryVectorStore

    class ToyEmbeddings(Embeddings):
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [[float(len(text)), float(sum(map(ord, text)) % 17)] for text in texts]

        def embed_query(self, text: str) -> list[float]:
            return [float(len(text)), float(sum(map(ord, text)) % 17)]

    runnable = RunnableLambda(lambda value: {"text": value["text"].upper()})
    config: RunnableConfig = {"tags": ["core-smoke"], "metadata": {"scope": "core"}}
    runnable_result = runnable.invoke({"text": "ok"}, config=config)
    async_result = asyncio.run(runnable.ainvoke({"text": "async"}, config=config))
    batch_result = runnable.batch([{"text": "a"}, {"text": "bb"}], config=config)

    prompt = ChatPromptTemplate.from_messages([("human", "Say {topic}")])
    parser_chain = prompt | RunnableLambda(lambda _prompt_value: "parsed") | StrOutputParser()
    parser_result = parser_chain.invoke({"topic": "hello"}, config=config)

    messages = [HumanMessage(content="hello"), AIMessage(content="world")]
    serialized_messages = messages_to_dict(messages)
    restored_messages = messages_from_dict(serialized_messages)
    single_message_type = message_to_dict(messages[0])["type"]

    @tool
    def echo_tool(text: str) -> str:
        """Echo text for smoke checking."""
        return text

    tool_result = echo_tool.invoke({"text": "tool"}, config=config)
    tool_schema = echo_tool.args_schema.model_json_schema() if echo_tool.args_schema else {}

    vector_store = InMemoryVectorStore(ToyEmbeddings())
    ids = vector_store.add_documents(
        [Document(page_content="alpha", metadata={"kind": "letter"})],
        ids=["doc-1"],
    )
    search_result = vector_store.similarity_search("alpha", k=1)

    summary: dict[str, Any] = {
        "runnable": runnable_result,
        "async": async_result,
        "batch": batch_result,
        "parser": parser_result,
        "message_count": len(restored_messages),
        "single_message_type": single_message_type,
        "tool": tool_result,
        "tool_schema_fields": sorted(tool_schema.get("properties", {})),
        "vector_ids": ids,
        "vector_hit": search_result[0].page_content if search_result else None,
    }
    print("OK core_import_smoke")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
