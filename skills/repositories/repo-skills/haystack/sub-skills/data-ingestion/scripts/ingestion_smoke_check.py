#!/usr/bin/env python3
"""Smoke-check public Haystack ingestion APIs without network or source-checkout dependencies."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

try:
    from haystack import Document, Pipeline
    from haystack.components.converters import TextFileToDocument
    from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
    from haystack.components.routers import DocumentLengthRouter, DocumentTypeRouter, FileTypeRouter, MetadataRouter
    from haystack.dataclasses import ByteStream, ChatMessage, FileContent
except ModuleNotFoundError as error:
    missing = error.name or "required dependency"
    raise SystemExit(
        "Haystack ingestion smoke check requires an environment with `haystack-ai` and its runtime dependencies "
        f"installed. Missing import: {missing}"
    ) from error


def check_data_classes() -> None:
    document = Document(content="Hello   ingestion", meta={"source": "inline", "language": "en"})
    assert document.id
    assert document.to_dict(flatten=False)["meta"]["source"] == "inline"

    stream = ByteStream.from_string(
        "Stream text",
        mime_type="text/plain",
        meta={"file_path": "stream.txt", "language": "en"},
    )
    assert stream.to_string() == "Stream text"
    assert stream.mime_type == "text/plain"

    message = ChatMessage.from_user("Summarize this text")
    assert message.text == "Summarize this text"


def check_file_content(tmp_path: Path) -> None:
    file_path = tmp_path / "attachment.txt"
    file_path.write_text("attachment", encoding="utf-8")
    content = FileContent.from_file_path(file_path)
    assert content.base64_data
    assert content.filename == "attachment.txt"
    assert content.mime_type == "text/plain"


def check_conversion_and_preprocessing(tmp_path: Path) -> list[Document]:
    source = tmp_path / "note.txt"
    source.write_text("Title\n\nOne   two three four five six seven.", encoding="utf-8")

    converted = TextFileToDocument().run(sources=[source], meta={"batch": "smoke"})["documents"]
    assert len(converted) == 1
    assert converted[0].meta["batch"] == "smoke"
    assert converted[0].meta["file_path"] == "note.txt"

    cleaned = DocumentCleaner(strip_whitespaces=True).run(documents=converted)["documents"]
    assert len(cleaned) == 1
    assert "  " not in cleaned[0].content

    chunks = DocumentSplitter(split_by="word", split_length=4, split_overlap=1).run(documents=cleaned)["documents"]
    assert len(chunks) >= 2
    assert all(chunk.meta.get("source_id") == cleaned[0].id for chunk in chunks)
    return chunks


def check_routers(tmp_path: Path, chunks: list[Document]) -> None:
    source = tmp_path / "note.txt"
    routed_files = FileTypeRouter(mime_types=["text/plain", "application/pdf"]).run(sources=[source])
    assert routed_files["text/plain"] == [source]

    typed_docs = DocumentTypeRouter(
        mime_types=["text/plain"],
        file_path_meta_field="file_path",
    ).run(documents=[Document(content="typed", meta={"file_path": "typed.txt"})])
    assert len(typed_docs["text/plain"]) == 1

    metadata_docs = MetadataRouter(
        rules={"smoke": {"field": "meta.batch", "operator": "==", "value": "smoke"}}
    ).run(documents=chunks)
    assert len(metadata_docs["smoke"]) == len(chunks)
    assert metadata_docs["unmatched"] == []

    length_docs = DocumentLengthRouter(threshold=8).run(documents=chunks)
    assert set(length_docs) == {"short_documents", "long_documents"}
    assert len(length_docs["short_documents"]) + len(length_docs["long_documents"]) == len(chunks)


def check_pipeline(tmp_path: Path) -> None:
    source = tmp_path / "pipeline.txt"
    source.write_text("alpha beta gamma delta epsilon", encoding="utf-8")

    pipeline = Pipeline()
    pipeline.add_component("converter", TextFileToDocument())
    pipeline.add_component("cleaner", DocumentCleaner(strip_whitespaces=True))
    pipeline.add_component("splitter", DocumentSplitter(split_by="word", split_length=3, split_overlap=0))
    pipeline.connect("converter.documents", "cleaner.documents")
    pipeline.connect("cleaner.documents", "splitter.documents")

    result = pipeline.run({"converter": {"sources": [source], "meta": {"batch": "pipeline"}}})
    documents = result["splitter"]["documents"]
    assert documents
    assert all(doc.meta["batch"] == "pipeline" for doc in documents)


def main() -> None:
    with TemporaryDirectory() as directory:
        tmp_path = Path(directory)
        check_data_classes()
        check_file_content(tmp_path)
        chunks = check_conversion_and_preprocessing(tmp_path)
        check_routers(tmp_path, chunks)
        check_pipeline(tmp_path)
    print("ingestion smoke check passed")


if __name__ == "__main__":
    main()
