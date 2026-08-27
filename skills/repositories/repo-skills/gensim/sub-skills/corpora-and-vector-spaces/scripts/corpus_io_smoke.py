#!/usr/bin/env python3
"""Tiny corpus/vector-space smoke test for Gensim.

No network is used. The script builds a Dictionary, serializes/reloads Matrix
Market data, and exercises TextDirectoryCorpus on temporary text files.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


def run_smoke() -> dict:
    from gensim import corpora
    from gensim.utils import simple_preprocess

    docs = ["Human computer interface", "Graph minors trees", "Human system computer"]
    texts = [simple_preprocess(doc) for doc in docs]
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        mm_path = tmpdir / "tiny.mm"
        corpora.MmCorpus.serialize(str(mm_path), corpus, id2word=dictionary)
        loaded = list(corpora.MmCorpus(str(mm_path)))

        text_root = tmpdir / "texts"
        text_root.mkdir()
        (text_root / "a.txt").write_text("Human computer\nGraph trees\n", encoding="utf-8")
        (text_root / "b.txt").write_text("System interface\n", encoding="utf-8")
        text_corpus = corpora.TextDirectoryCorpus(
            str(text_root),
            dictionary=dictionary,
            lines_are_documents=True,
            pattern=r".*\.txt",
        )
        text_vectors = list(text_corpus)

    assert len(dictionary) >= 6
    assert loaded == corpus
    assert len(text_vectors) == 3
    return {"dictionary_size": len(dictionary), "documents": len(corpus), "text_directory_vectors": len(text_vectors)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()
    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("corpus IO smoke passed", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
