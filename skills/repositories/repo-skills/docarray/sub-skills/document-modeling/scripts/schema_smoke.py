#!/usr/bin/env python3
"""Safe DocArray document-modeling smoke checks.

The script uses only public DocArray APIs and in-memory NumPy data. It can be
run from any working directory as long as DocArray is importable in the active
Python environment.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from typing import Optional


def _import_runtime():
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise SystemExit(
            "ImportError: schema_smoke.py requires NumPy because the verified "
            "DocArray modeling path uses docarray.typing.NdArray. Install NumPy "
            "or run in a DocArray environment with base dependencies."
        ) from exc

    try:
        import docarray
        from docarray import BaseDoc, DocList, DocVec
        from docarray.documents import ImageDoc, TextDoc
        from docarray.documents.helper import create_doc, create_doc_from_dict
        from docarray.typing import NdArray
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise SystemExit(
            "ImportError: DocArray is not importable in this Python environment. "
            "Install docarray with the selected extras for your workflow before "
            "running this smoke helper. Original error: " + str(exc)
        ) from exc

    return {
        "np": np,
        "docarray": docarray,
        "BaseDoc": BaseDoc,
        "DocList": DocList,
        "DocVec": DocVec,
        "ImageDoc": ImageDoc,
        "TextDoc": TextDoc,
        "create_doc": create_doc,
        "create_doc_from_dict": create_doc_from_dict,
        "NdArray": NdArray,
    }


def run_smoke(skip_docvec: bool = False, verbose: bool = True) -> None:
    rt = _import_runtime()
    np = rt["np"]
    docarray = rt["docarray"]
    BaseDoc = rt["BaseDoc"]
    DocList = rt["DocList"]
    DocVec = rt["DocVec"]
    ImageDoc = rt["ImageDoc"]
    TextDoc = rt["TextDoc"]
    create_doc = rt["create_doc"]
    create_doc_from_dict = rt["create_doc_from_dict"]
    NdArray = rt["NdArray"]

    class ThumbnailDoc(BaseDoc):
        tensor: NdArray[3, 8, 8]

    class ArticleDoc(BaseDoc):
        title: str
        text: TextDoc
        thumbnail: Optional[ThumbnailDoc] = None
        embedding: NdArray[4]

    article = ArticleDoc(
        title="hello",
        text=TextDoc("DocArray smoke"),
        thumbnail=ThumbnailDoc(tensor=np.zeros((3, 8, 8))),
        embedding=np.arange(4),
    )
    assert article.id is not None
    assert article.text.text == "DocArray smoke"
    assert article.thumbnail is not None
    assert article.thumbnail.tensor.shape == (3, 8, 8)
    assert article.embedding.shape == (4,)

    # Shape validation should reject an impossible shape. DocArray warns before
    # attempting a reshape, so keep the expected warning out of smoke output.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            ThumbnailDoc(tensor=np.zeros((2, 8, 8)))
        except Exception:
            pass
        else:  # pragma: no cover - would indicate a validation regression
            raise AssertionError("NdArray[3, 8, 8] accepted a tensor with shape (2, 8, 8)")

    MultiModalDoc = create_doc(
        "SmokeMultiModalDoc",
        image=(ImageDoc, ...),
        text=(TextDoc, ...),
        score=(float, 0.0),
    )
    dynamic_doc = MultiModalDoc(
        image=ImageDoc(tensor=np.zeros((3, 8, 8))),
        text=TextDoc(text="dynamic"),
    )
    assert isinstance(dynamic_doc, BaseDoc)
    assert dynamic_doc.text.text == "dynamic"
    assert dynamic_doc.score == 0.0

    InferredDoc = create_doc_from_dict(
        "SmokeInferredDoc",
        {"text": TextDoc("sample"), "image": ImageDoc(), "rank": 1},
    )
    inferred = InferredDoc(text=TextDoc("sample"), image=ImageDoc(), rank=2)
    assert isinstance(inferred, BaseDoc)
    assert inferred.rank == 2

    rows = DocList[ArticleDoc](
        [
            ArticleDoc(
                title=f"doc-{i}",
                text=TextDoc(text=f"text-{i}"),
                thumbnail=ThumbnailDoc(tensor=np.ones((3, 8, 8)) * i),
                embedding=np.ones(4) * i,
            )
            for i in range(3)
        ]
    )
    assert len(rows) == 3
    assert rows.title == ["doc-0", "doc-1", "doc-2"]
    assert rows.text.text == ["text-0", "text-1", "text-2"]
    assert rows.thumbnail[0].tensor.shape == (3, 8, 8)

    rows_with_missing = DocList[ArticleDoc](
        [
            ArticleDoc(title="present", text=TextDoc("a"), thumbnail=ThumbnailDoc(tensor=np.zeros((3, 8, 8))), embedding=np.zeros(4)),
            ArticleDoc(title="missing", text=TextDoc("b"), thumbnail=None, embedding=np.ones(4)),
        ]
    )
    assert rows_with_missing.thumbnail[1] is None
    assert isinstance(rows_with_missing.thumbnail, list)

    if not skip_docvec:
        try:
            vec = rows.to_doc_vec()
            assert isinstance(vec, DocVec)
            assert vec.embedding.shape == (3, 4)
            assert vec.thumbnail.tensor.shape == (3, 3, 8, 8)
            assert vec[0].is_view()
            vec.embedding = np.zeros((3, 4))
            assert np.asarray(vec[0].embedding).shape == (4,)

            none_rows = DocList[ArticleDoc](
                [
                    ArticleDoc(title=f"none-{i}", text=TextDoc("none"), thumbnail=None, embedding=np.zeros(4))
                    for i in range(2)
                ]
            )
            none_vec = none_rows.to_doc_vec()
            assert none_vec.thumbnail is None
        except Exception as exc:
            raise SystemExit(
                "DocVec smoke failed. If NumPy 2.x is installed, try a current "
                "verified NumPy 1.x environment or rerun with --skip-docvec. "
                "Original error: " + repr(exc)
            ) from exc

    if verbose:
        print("DocArray document-modeling smoke passed")
        print(f"docarray={getattr(docarray, '__version__', 'unknown')}")
        print(f"numpy={np.__version__}")
        if skip_docvec:
            print("DocVec checks skipped by request")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run safe in-memory DocArray document-modeling smoke checks.",
    )
    parser.add_argument(
        "--skip-docvec",
        action="store_true",
        help="Skip DocVec columnar batch checks; useful when diagnosing NumPy/backend compatibility.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress success details and print only errors.",
    )
    args = parser.parse_args(argv)

    run_smoke(skip_docvec=args.skip_docvec, verbose=not args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
