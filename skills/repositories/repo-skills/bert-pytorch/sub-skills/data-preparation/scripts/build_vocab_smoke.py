#!/usr/bin/env python3
"""Build, reload, and inspect a tiny BERT-pytorch vocabulary."""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
import tempfile
from pathlib import Path

from bert_pytorch.dataset import BERTDataset, WordVocab

SKILL_ROOT = Path(__file__).resolve().parents[3]
TINY_CORPUS_HELPER = SKILL_ROOT / "scripts" / "make_tiny_corpus.py"


def make_corpus(path: Path) -> Path:
    subprocess.run([sys.executable, str(TINY_CORPUS_HELPER), "--output", str(path), "--overwrite"], check=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and validate a tiny BERT-pytorch vocab from a small corpus.")
    parser.add_argument("--workdir", type=Path, default=None, help="Directory for generated smoke files.")
    parser.add_argument("--corpus", type=Path, default=None, help="Use an existing corpus instead of generating one.")
    parser.add_argument("--output", type=Path, default=None, help="Vocabulary output path; defaults inside workdir.")
    parser.add_argument("--seq-len", type=int, default=8, help="Sequence length for the dataset check.")
    parser.add_argument("--min-freq", type=int, default=1, help="Minimum token frequency for the vocab.")
    parser.add_argument("--skip-dataset-check", action="store_true", help="Only build and reload the vocab.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing vocab output file.")
    args = parser.parse_args()

    workdir = args.workdir or Path(tempfile.mkdtemp(prefix="bert-pytorch-data-smoke-"))
    workdir.mkdir(parents=True, exist_ok=True)

    corpus_path = args.corpus or workdir / "tiny_corpus.txt"
    if args.corpus is None:
        make_corpus(corpus_path)
    elif not corpus_path.exists():
        raise SystemExit(f"corpus does not exist: {corpus_path}")

    vocab_path = args.output or workdir / "tiny_vocab.pkl"
    if vocab_path.exists() and not args.overwrite:
        raise SystemExit(f"vocab output already exists: {vocab_path}; pass --overwrite to replace it")
    vocab_path.parent.mkdir(parents=True, exist_ok=True)

    with corpus_path.open("r", encoding="utf-8") as handle:
        vocab = WordVocab(handle, min_freq=args.min_freq)
    vocab.save_vocab(str(vocab_path))

    loaded = WordVocab.load_vocab(str(vocab_path))
    if len(loaded) != len(vocab):
        raise SystemExit(f"vocab reload mismatch: {len(vocab)} != {len(loaded)}")

    print(f"corpus={corpus_path}")
    print(f"vocab={vocab_path}")
    print(f"vocab_size={len(vocab)}")
    print("reload=ok")

    if not args.skip_dataset_check:
        random.seed(0)
        dataset = BERTDataset(str(corpus_path), loaded, seq_len=args.seq_len)
        sample = dataset[0]
        print(f"dataset_len={len(dataset)}")
        print(f"sample_keys={sorted(sample.keys())}")
        print(f"bert_input_shape={tuple(sample['bert_input'].shape)}")
        print(f"bert_label_shape={tuple(sample['bert_label'].shape)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
