#!/usr/bin/env python3
"""Safe local DocArray serialization/storage round-trip smoke helper."""

import argparse
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

np = None
BaseDoc = None
DocList = None
DocVec = None
NdArray = None
ScalarDoc = None
SmokeDoc = None


def require_docarray() -> None:
    """Import DocArray lazily so --help works even before dependencies are installed."""
    global np, BaseDoc, DocList, DocVec, NdArray, ScalarDoc, SmokeDoc
    if BaseDoc is not None:
        return

    import numpy as _np
    from docarray import BaseDoc as _BaseDoc
    from docarray import DocList as _DocList
    from docarray import DocVec as _DocVec
    from docarray.typing import NdArray as _NdArray

    class _ScalarDoc(_BaseDoc):
        text: str
        score: int

    class _SmokeDoc(_BaseDoc):
        text: str
        score: int
        embedding: _NdArray[3]

    # Make local dynamic classes discoverable for the trusted pickle smoke path.
    _ScalarDoc.__name__ = "ScalarDoc"
    _ScalarDoc.__qualname__ = "ScalarDoc"
    _ScalarDoc.__module__ = __name__
    _SmokeDoc.__name__ = "SmokeDoc"
    _SmokeDoc.__qualname__ = "SmokeDoc"
    _SmokeDoc.__module__ = __name__

    np = _np
    BaseDoc = _BaseDoc
    DocList = _DocList
    DocVec = _DocVec
    NdArray = _NdArray
    ScalarDoc = _ScalarDoc
    SmokeDoc = _SmokeDoc
    globals()["ScalarDoc"] = _ScalarDoc
    globals()["SmokeDoc"] = _SmokeDoc


def make_scalar_docs():
    return DocList[ScalarDoc](
        [ScalarDoc(text="alpha", score=1), ScalarDoc(text="beta", score=2)]
    )


def make_vector_docs():
    return DocList[SmokeDoc](
        [
            SmokeDoc(text="alpha", score=1, embedding=[1, 0, 0]),
            SmokeDoc(text="beta", score=2, embedding=[0, 1, 0]),
        ]
    )


def assert_scalar_docs_equal(actual, expected) -> None:
    assert len(actual) == len(expected), f"length mismatch: {len(actual)} != {len(expected)}"
    for idx, (got, want) in enumerate(zip(actual, expected)):
        assert got.text == want.text, f"text mismatch at {idx}: {got.text!r} != {want.text!r}"
        assert got.score == want.score, f"score mismatch at {idx}: {got.score!r} != {want.score!r}"


def assert_smoke_docs_equal(actual, expected) -> None:
    assert len(actual) == len(expected), f"length mismatch: {len(actual)} != {len(expected)}"
    for idx, (got, want) in enumerate(zip(actual, expected)):
        assert got.text == want.text, f"text mismatch at {idx}: {got.text!r} != {want.text!r}"
        assert got.score == want.score, f"score mismatch at {idx}: {got.score!r} != {want.score!r}"
        assert np.array_equal(np.asarray(got.embedding), np.asarray(want.embedding)), (
            f"embedding mismatch at {idx}: {got.embedding!r} != {want.embedding!r}"
        )


def assert_docvec_equal(actual, expected_len: int) -> None:
    assert len(actual) == expected_len, f"DocVec length mismatch: {len(actual)} != {expected_len}"
    assert actual.tensor_type == NdArray, f"unexpected tensor_type: {actual.tensor_type!r}"
    assert tuple(actual.embedding.shape) == (expected_len, 3), (
        f"unexpected embedding shape: {actual.embedding.shape!r}"
    )


@contextmanager
def make_workdir(tmp_dir: Optional[str]) -> Iterator[Path]:
    if tmp_dir:
        base = Path(tmp_dir).expanduser().resolve()
        base.mkdir(parents=True, exist_ok=True)
        run_dir = Path(tempfile.mkdtemp(prefix="docarray-roundtrip-", dir=str(base)))
        yield run_dir
    else:
        with tempfile.TemporaryDirectory(prefix="docarray-roundtrip-") as tmp:
            yield Path(tmp)


def roundtrip_json() -> None:
    doc = SmokeDoc(text="single", score=7, embedding=[1, 2, 3])
    doc_from_json = SmokeDoc.from_json(doc.to_json())
    assert doc_from_json.text == doc.text
    assert np.array_equal(np.asarray(doc_from_json.embedding), np.asarray(doc.embedding))

    docs = make_vector_docs()
    docs_from_json = DocList[SmokeDoc].from_json(docs.to_json())
    assert_smoke_docs_equal(docs_from_json, docs)

    vec = make_vector_docs().to_doc_vec(tensor_type=NdArray)
    vec_from_json = DocVec[SmokeDoc].from_json(vec.to_json(), tensor_type=NdArray)
    assert_docvec_equal(vec_from_json, expected_len=2)


def roundtrip_protobuf() -> None:
    doc = SmokeDoc(text="single", score=7, embedding=[1, 2, 3])
    doc_from_proto = SmokeDoc.from_protobuf(doc.to_protobuf())
    assert doc_from_proto.score == doc.score
    assert np.array_equal(np.asarray(doc_from_proto.embedding), np.asarray(doc.embedding))

    docs = make_vector_docs()
    docs_from_proto = DocList[SmokeDoc].from_protobuf(docs.to_protobuf())
    assert_smoke_docs_equal(docs_from_proto, docs)

    vec = make_vector_docs().to_doc_vec(tensor_type=NdArray)
    vec_from_proto = DocVec[SmokeDoc].from_protobuf(vec.to_protobuf(), tensor_type=NdArray)
    assert_docvec_equal(vec_from_proto, expected_len=2)


def roundtrip_bytes_base64_binary(workdir: Path, skip_protobuf: bool) -> None:
    doc_protocol = "pickle" if skip_protobuf else "protobuf"
    array_protocol = "json-array" if skip_protobuf else "protobuf-array"
    stream_protocol = "pickle" if skip_protobuf else "protobuf"

    doc = SmokeDoc(text="single", score=7, embedding=[1, 2, 3])
    doc_bytes = doc.to_bytes(protocol=doc_protocol, compress=None)
    doc_from_bytes = SmokeDoc.from_bytes(doc_bytes, protocol=doc_protocol, compress=None)
    assert doc_from_bytes.text == doc.text

    doc_base64 = doc.to_base64(protocol=doc_protocol, compress=None)
    doc_from_base64 = SmokeDoc.from_base64(doc_base64, protocol=doc_protocol, compress=None)
    assert doc_from_base64.score == doc.score

    docs = make_vector_docs()
    docs_bytes = docs.to_bytes(protocol=array_protocol, compress=None)
    docs_from_bytes = DocList[SmokeDoc].from_bytes(
        docs_bytes, protocol=array_protocol, compress=None
    )
    assert_smoke_docs_equal(docs_from_bytes, docs)

    docs_base64 = docs.to_base64(protocol=array_protocol, compress=None)
    docs_from_base64 = DocList[SmokeDoc].from_base64(
        docs_base64, protocol=array_protocol, compress=None
    )
    assert_smoke_docs_equal(docs_from_base64, docs)

    docs_path = workdir / "smoke-doclist.bin"
    docs.save_binary(docs_path, protocol=array_protocol, compress=None)
    docs_from_file = DocList[SmokeDoc].load_binary(
        docs_path, protocol=array_protocol, compress=None
    )
    assert_smoke_docs_equal(docs_from_file, docs)

    vec = make_vector_docs().to_doc_vec(tensor_type=NdArray)
    vec_bytes = vec.to_bytes(protocol=array_protocol, compress=None)
    vec_from_bytes = DocVec[SmokeDoc].from_bytes(
        vec_bytes, protocol=array_protocol, compress=None, tensor_type=NdArray
    )
    assert_docvec_equal(vec_from_bytes, expected_len=2)

    vec_base64 = vec.to_base64(protocol=array_protocol, compress=None)
    vec_from_base64 = DocVec[SmokeDoc].from_base64(
        vec_base64, protocol=array_protocol, compress=None, tensor_type=NdArray
    )
    assert_docvec_equal(vec_from_base64, expected_len=2)

    vec_path = workdir / "smoke-docvec.bin"
    vec.save_binary(vec_path, protocol=array_protocol, compress=None)
    vec_from_file = DocVec[SmokeDoc].load_binary(
        vec_path, protocol=array_protocol, compress=None, tensor_type=NdArray
    )
    assert_docvec_equal(vec_from_file, expected_len=2)

    scalar_docs = make_scalar_docs()
    stream_path = workdir / "smoke-stream.bin"
    scalar_docs.save_binary(stream_path, protocol=stream_protocol, compress=None)
    streamed = list(
        DocList[ScalarDoc].load_binary(
            stream_path, protocol=stream_protocol, compress=None, streaming=True
        )
    )
    assert_scalar_docs_equal(DocList[ScalarDoc](streamed), scalar_docs)


def roundtrip_csv(workdir: Path) -> None:
    docs = make_scalar_docs()
    csv_path = workdir / "scalar.csv"
    docs.to_csv(str(csv_path))
    loaded = DocList[ScalarDoc].from_csv(str(csv_path))
    assert_scalar_docs_equal(loaded, docs)


def roundtrip_dataframe() -> None:
    scalar_docs = make_scalar_docs()
    df = scalar_docs.to_dataframe()
    loaded = DocList[ScalarDoc].from_dataframe(df)
    assert_scalar_docs_equal(loaded, scalar_docs)

    vec = make_vector_docs().to_doc_vec(tensor_type=NdArray)
    vec_df = vec.to_dataframe()
    vec_loaded = DocVec[SmokeDoc].from_dataframe(vec_df, tensor_type=NdArray)
    assert_docvec_equal(vec_loaded, expected_len=2)


def roundtrip_file_store(workdir: Path) -> None:
    from docarray.store import FileDocStore

    namespace = workdir / "docstore"
    namespace.mkdir(parents=True, exist_ok=True)

    docs = make_scalar_docs()
    url = f"file://{namespace / 'sample'}"
    docs.push(url, show_progress=False)
    pulled = DocList[ScalarDoc].pull(url, show_progress=False, local_cache=False)
    assert_scalar_docs_equal(pulled, docs)

    stream_url = f"file://{namespace / 'streamed'}"
    DocList[ScalarDoc].push_stream(iter(make_scalar_docs()), stream_url, show_progress=False)
    pulled_stream = DocList[ScalarDoc](
        DocList[ScalarDoc].pull_stream(stream_url, show_progress=False, local_cache=False)
    )
    assert_scalar_docs_equal(pulled_stream, docs)

    names = set(FileDocStore.list(str(namespace), show_table=False))
    assert {"sample", "streamed"}.issubset(names), f"unexpected file store names: {names!r}"
    assert FileDocStore.delete(str(namespace / "sample"), missing_ok=False)
    assert FileDocStore.delete(str(namespace / "streamed"), missing_ok=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe local DocArray serialization, binary, CSV/DataFrame, and file-store "
            "round-trip assertions. No S3 or network service is used."
        )
    )
    parser.add_argument(
        "--skip-protobuf",
        action="store_true",
        help="Skip direct protobuf checks and use non-protobuf protocols for byte/binary smoke paths.",
    )
    parser.add_argument(
        "--skip-file-store",
        action="store_true",
        help="Skip local file:// DocList push/pull and streaming store checks.",
    )
    parser.add_argument(
        "--skip-dataframe",
        action="store_true",
        help="Skip pandas DataFrame round-trip checks.",
    )
    parser.add_argument(
        "--tmp-dir",
        default=None,
        help="Optional base directory for temporary smoke files. A unique subdirectory is created inside it.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_docarray()

    with make_workdir(args.tmp_dir) as workdir:
        roundtrip_json()
        print("OK: JSON round-trips")

        if args.skip_protobuf:
            print("SKIP: protobuf round-trips")
        else:
            roundtrip_protobuf()
            print("OK: protobuf round-trips")

        roundtrip_bytes_base64_binary(workdir, skip_protobuf=args.skip_protobuf)
        print("OK: bytes, base64, binary, and streaming binary round-trips")

        roundtrip_csv(workdir)
        print("OK: scalar CSV round-trip")

        if args.skip_dataframe:
            print("SKIP: DataFrame round-trips")
        else:
            roundtrip_dataframe()
            print("OK: DataFrame round-trips")

        if args.skip_file_store:
            print("SKIP: file:// store round-trips")
        else:
            roundtrip_file_store(workdir)
            print("OK: file:// store push/pull/list/delete round-trips")

    print("All requested DocArray serialization/storage smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
