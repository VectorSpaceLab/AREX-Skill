#!/usr/bin/env python3
"""Convert word2vec-format vectors to TensorBoard Projector TSV files."""

from __future__ import annotations

import argparse
from pathlib import Path


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to word2vec-format vector file")
    parser.add_argument("--output-prefix", required=True, help="Prefix for *_tensor.tsv and *_metadata.tsv")
    parser.add_argument("--binary", action="store_true", help="Read binary word2vec format")
    parser.add_argument("--verify", action="store_true", help="Check generated tensor/metadata row counts match")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_prefix = Path(args.output_prefix)
    if not input_path.is_file():
        parser.error(f"input file does not exist: {input_path}")
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    from gensim.scripts.word2vec2tensor import word2vec2tensor

    word2vec2tensor(str(input_path), str(output_prefix), binary=args.binary)
    tensor = Path(str(output_prefix) + "_tensor.tsv")
    metadata = Path(str(output_prefix) + "_metadata.tsv")
    if args.verify:
        if not tensor.is_file() or not metadata.is_file():
            raise SystemExit("expected tensor and metadata files were not created")
        tensor_rows = count_lines(tensor)
        metadata_rows = count_lines(metadata)
        if tensor_rows != metadata_rows:
            raise SystemExit(f"row mismatch: tensor={tensor_rows}, metadata={metadata_rows}")
    print(f"wrote {tensor} and {metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
