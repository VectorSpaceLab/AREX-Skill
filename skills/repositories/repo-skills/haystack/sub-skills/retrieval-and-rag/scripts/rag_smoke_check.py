"""Portable local retrieval/RAG smoke check for Haystack.

This script intentionally avoids network calls and provider credentials. It verifies
that a process can import Haystack, write documents, retrieve with BM25, apply a
metadata filter, and pass retrieved documents through a minimal component in a
Pipeline.
"""

from __future__ import annotations

from haystack import Document, Pipeline, component
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.components.writers import DocumentWriter
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.document_stores.types import DuplicatePolicy


@component
class ContextAnswerer:
    """Small deterministic answer component used only for local smoke checks."""

    @component.output_types(reply=str)
    def run(self, query: str, documents: list[Document]) -> dict[str, str]:
        context = " | ".join(doc.content or "" for doc in documents)
        return {"reply": f"query={query}; context={context}"}


def main() -> None:
    store = InMemoryDocumentStore(index="disco-retrieval-rag-smoke")
    writer = DocumentWriter(document_store=store, policy=DuplicatePolicy.OVERWRITE)
    documents = [
        Document(id="paris", content="Jean lives in Paris and likes retrieval.", meta={"city": "Paris", "lang": "en"}),
        Document(id="berlin", content="Mark lives in Berlin and likes pipelines.", meta={"city": "Berlin", "lang": "en"}),
        Document(id="rome", content="Giorgio lives in Rome and likes components.", meta={"city": "Rome", "lang": "en"}),
    ]
    write_result = writer.run(documents=documents)
    assert write_result["documents_written"] == len(documents), write_result
    assert store.count_documents() == len(documents)

    retriever = InMemoryBM25Retriever(document_store=store, top_k=2)
    retrieval_result = retriever.run(query="Who lives in Paris?")
    retrieved = retrieval_result["documents"]
    assert retrieved, "BM25 retrieval returned no documents"
    assert retrieved[0].id == "paris", [doc.id for doc in retrieved]

    filters = {"field": "meta.city", "operator": "==", "value": "Berlin"}
    filtered = retriever.run(query="Who likes pipelines?", filters=filters, top_k=1)["documents"]
    assert len(filtered) == 1, filtered
    assert filtered[0].id == "berlin", [doc.id for doc in filtered]

    rag = Pipeline()
    rag.add_component("retriever", InMemoryBM25Retriever(document_store=store, top_k=1))
    rag.add_component("answerer", ContextAnswerer())
    rag.connect("retriever.documents", "answerer.documents")

    question = "Who lives in Paris?"
    rag_result = rag.run({"retriever": {"query": question}, "answerer": {"query": question}})
    reply = rag_result["answerer"]["reply"]
    assert "Jean lives in Paris" in reply, reply
    print("retrieval-and-rag smoke check passed")


if __name__ == "__main__":
    main()
