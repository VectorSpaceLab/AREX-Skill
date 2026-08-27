#!/usr/bin/env python3
"""Create a tiny local DeepPavlov TF-IDF retrieval config.

The script itself uses only the Python standard library and never downloads
models, datasets, credentials, or source-checkout files. The generated config is
intended for a prepared DeepPavlov environment and mirrors the safe parts of the
DeepPavlov doc-retrieval test configs: odqa_reader -> sqlite_iterator ->
hashing_tfidf_vectorizer -> tfidf_ranker.

By default the config uses stream_spacy_tokenizer because the TF-IDF vectorizer
expects the tokenizer to expose ngram_range when saving the index. The script
sets the model name in metadata but does not install or download that model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any

SAMPLE_DOCS = {
    "deep_pavlov.txt": (
        "DeepPavlov is an open-source framework for natural language processing, "
        "dialog systems, retrieval, and question answering."
    ),
    "ivan_pavlov.txt": (
        "Ivan Pavlov studied conditioned reflexes and classical conditioning in physiology."
    ),
}

SAMPLE_QUERIES = [
    "What is DeepPavlov?",
    "Who studied conditioned reflexes?",
]


def build_config(root: Path, spacy_model: str, top_n: int) -> Dict[str, Any]:
    """Return a minimal local retrieval config with no download entries."""
    return {
        "dataset_reader": {
            "class_name": "odqa_reader",
            "data_path": "{ROOT_PATH}/docs",
            "save_path": "{ROOT_PATH}/tiny_docs.db",
            "dataset_format": "txt",
        },
        "dataset_iterator": {
            "class_name": "sqlite_iterator",
            "shuffle": False,
            "load_path": "{ROOT_PATH}/tiny_docs.db",
        },
        "chainer": {
            "in": ["docs"],
            "in_y": ["doc_ids", "doc_nums"],
            "out": ["tfidf_doc_ids", "tfidf_doc_scores"],
            "pipe": [
                {
                    "class_name": "hashing_tfidf_vectorizer",
                    "id": "vectorizer",
                    "fit_on": ["docs", "doc_ids", "doc_nums"],
                    "save_path": "{ROOT_PATH}/tiny_tfidf.npz",
                    "load_path": "{ROOT_PATH}/tiny_tfidf.npz",
                    "tokenizer": {
                        "class_name": "stream_spacy_tokenizer",
                        "spacy_model": "{SPACY_MODEL}",
                        "lemmas": False,
                        "lowercase": True,
                        "filter_stopwords": False,
                        "alphas_only": False,
                        "ngram_range": [1, 2],
                    },
                },
                {
                    "class_name": "tfidf_ranker",
                    "top_n": top_n,
                    "in": ["docs"],
                    "out": ["tfidf_doc_ids", "tfidf_doc_scores"],
                    "vectorizer": "#vectorizer",
                },
            ],
        },
        "train": {
            "batch_size": 2,
            "evaluation_targets": [],
            "class_name": "fit_trainer",
        },
        "metadata": {
            "variables": {
                "ROOT_PATH": str(root),
                "SPACY_MODEL": spacy_model,
            },
            "download": [],
        },
    }


def write_text(path: Path, text: str, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Write sample docs, sample queries, and a tiny local DeepPavlov "
            "TF-IDF retrieval config. No downloads are performed."
        )
    )
    parser.add_argument(
        "--output-dir",
        default="./tiny-retrieval-smoke",
        help="Directory that will receive docs/, sample_queries.txt, and tiny_retrieval_config.json.",
    )
    parser.add_argument(
        "--spacy-model",
        default="en_core_web_sm",
        help="Already-installed spaCy model name to place in the generated config.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=2,
        help="Number of document IDs/scores the generated ranker should return.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing sample docs, query file, and config if present.",
    )
    args = parser.parse_args()

    if args.top_n < 1:
        parser.error("--top-n must be at least 1")

    root = Path(args.output_dir).expanduser().resolve()
    docs_dir = root / "docs"
    config_path = root / "tiny_retrieval_config.json"
    query_path = root / "sample_queries.txt"

    docs_dir.mkdir(parents=True, exist_ok=True)
    wrote = []
    skipped = []

    for name, text in SAMPLE_DOCS.items():
        target = docs_dir / name
        if write_text(target, text + "\n", args.overwrite):
            wrote.append(target)
        else:
            skipped.append(target)

    if write_text(query_path, "\n".join(SAMPLE_QUERIES) + "\n", args.overwrite):
        wrote.append(query_path)
    else:
        skipped.append(query_path)

    config = build_config(root, args.spacy_model, args.top_n)
    config_text = json.dumps(config, indent=2, ensure_ascii=False) + "\n"
    if write_text(config_path, config_text, args.overwrite):
        wrote.append(config_path)
    else:
        skipped.append(config_path)

    print("Tiny retrieval workspace:", root)
    if wrote:
        print("Wrote:")
        for path in wrote:
            print("  -", path)
    if skipped:
        print("Skipped existing files (use --overwrite to replace):")
        for path in skipped:
            print("  -", path)
    print("\nNo downloads were performed.")
    print("After DeepPavlov and the spaCy model are already installed, try:")
    print(f"  python -m deeppavlov train {config_path}")
    print(f"  python -m deeppavlov predict {config_path} -f {query_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
