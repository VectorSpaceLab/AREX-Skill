#!/usr/bin/env python3
"""Build a scispaCy linker ANN index from a local knowledge base.

This is a safe wrapper around `create_tfidf_ann_index` for small or custom KBs.
It does not depend on the source checkout and can be run from any directory.

Example:
    python scripts/build_linker_index.py --kb-path /path/to/kb.jsonl --output-path /tmp/linker-index
"""

from __future__ import annotations

import argparse
from pathlib import Path

from scispacy.candidate_generation import create_tfidf_ann_index
from scispacy.linking_utils import KnowledgeBase


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kb-path",
        required=True,
        help="Path to a JSON or JSONL knowledge-base file.",
    )
    parser.add_argument(
        "--output-path",
        required=True,
        help="Directory where the ANN index, vectorizer, vectors, and alias map will be written.",
    )
    parser.add_argument(
        "--ef-search",
        type=int,
        default=200,
        help="nmslib query-time efSearch value used when loading or building the index.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    kb_path = Path(args.kb_path)
    output_path = Path(args.output_path)
    if not kb_path.exists():
        raise SystemExit(f"KB path does not exist: {kb_path}")
    output_path.mkdir(parents=True, exist_ok=True)

    kb = KnowledgeBase(kb_path)
    concept_aliases, _, _ = create_tfidf_ann_index(str(output_path), kb, ef_search=args.ef_search)
    print(f"Built linker index in {output_path} with {len(concept_aliases)} aliases")


if __name__ == "__main__":
    main()
