#!/usr/bin/env python3
"""Convert a GloVe-style text vector file to word2vec text format.

This is a safe wrapper around Gensim's conversion helper with optional load
verification.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to GloVe text file")
    parser.add_argument("--output", required=True, help="Path to write word2vec text file")
    parser.add_argument("--verify-load", action="store_true", help="Load the output with KeyedVectors after conversion")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.is_file():
        parser.error(f"input file does not exist: {input_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    from gensim.scripts.glove2word2vec import glove2word2vec

    vector_count, vector_size = glove2word2vec(str(input_path), str(output_path))
    if args.verify_load:
        from gensim.models import KeyedVectors
        kv = KeyedVectors.load_word2vec_format(str(output_path), binary=False)
        if len(kv) != vector_count or kv.vector_size != vector_size:
            raise SystemExit(
                f"verification mismatch: expected {vector_count}x{vector_size}, got {len(kv)}x{kv.vector_size}"
            )
    print(f"wrote {output_path} ({vector_count} vectors, {vector_size} dimensions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
