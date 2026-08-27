try:
    from adalflow.components.data_process.text_splitter import TextSplitter
    from adalflow.core.types import Document
except ModuleNotFoundError as exc:
    raise SystemExit(
        f"A required dependency is missing while importing AdalFlow: {exc.name}. Install the package and its base dependencies in the active Python environment before running this smoke script."
    ) from exc


def main() -> None:
    splitter = TextSplitter(split_by="word", chunk_size=3, chunk_overlap=1)
    document = Document(
        text="one two three four",
        meta_data={"source": "smoke"},
        id="doc-1",
    )

    chunks = splitter.call([document])
    chunk_texts = [chunk.text for chunk in chunks]
    expected = ["one two three ", "three four"]

    assert chunk_texts == expected, f"unexpected chunks: {chunk_texts!r}"
    assert [chunk.parent_doc_id for chunk in chunks] == ["doc-1", "doc-1"]
    assert [chunk.order for chunk in chunks] == [0, 1]

    print("text_splitter_smoke ok:", chunk_texts)


if __name__ == "__main__":
    main()
