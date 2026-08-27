from pathlib import Path
from tempfile import TemporaryDirectory

try:
    from adalflow.components.data_process.text_splitter import TextSplitter
    from adalflow.core.db import LocalDB
    from adalflow.core.types import Document
except ModuleNotFoundError as exc:
    raise SystemExit(
        f"A required dependency is missing while importing AdalFlow: {exc.name}. Install the package and its base dependencies in the active Python environment before running this smoke script."
    ) from exc


def main() -> None:
    db = LocalDB(name="retrieval-rag-smoke")
    documents = [
        Document(
            text="alpha beta gamma delta",
            meta_data={"topic": "one"},
            id="doc-1",
        )
    ]

    db.load(documents)
    splitter = TextSplitter(split_by="word", chunk_size=3, chunk_overlap=1)
    db.register_transformer(transformer=splitter, key="split")
    db.transform(key="split")

    transformed = db.get_transformed_data(key="split")
    transformed_texts = [doc.text for doc in transformed]
    expected = ["alpha beta gamma ", "gamma delta"]
    assert transformed_texts == expected, f"unexpected transformed docs: {transformed_texts!r}"

    with TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "localdb.pkl"
        db.save_state(str(save_path))
        restored = LocalDB.load_state(str(save_path))

        assert restored is not None, "expected LocalDB.load_state to restore a value"
        assert restored.index_path == str(save_path)
        assert [doc.text for doc in restored.items] == [doc.text for doc in documents]
        assert restored.get_transformer_keys() == ["split"]
        assert [doc.text for doc in restored.get_transformed_data(key="split")] == expected

    print("localdb_smoke ok:", len(db.items), len(transformed_texts))


if __name__ == "__main__":
    main()
