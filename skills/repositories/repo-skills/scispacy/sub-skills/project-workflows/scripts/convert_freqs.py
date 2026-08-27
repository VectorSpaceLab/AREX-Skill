#!/usr/bin/env python3
"""Convert token frequency counts into spaCy vocab JSONL.

This is a small, safe helper for scispaCy project workflows. It accepts the
project's tab-separated frequency format and emits the JSONL vocabulary format
used by the spaCy configs.

Example:
    python scripts/convert_freqs.py --input_path /tmp/freqs.tsv --output_path /tmp/vocab.jsonl --min_word_frequency 1000
"""

from __future__ import annotations

import argparse
import json
import math
from ast import literal_eval
from pathlib import Path

from preshed.counter import PreshCounter
from tqdm import tqdm

from scispacy.file_cache import cached_path


def read_freqs(freqs_loc: Path, max_length: int = 100, min_doc_freq: int = 5, min_freq: int = 50):
    """Read the repo frequency format and convert it to log probabilities."""
    print("Counting frequencies...")
    counts = PreshCounter()
    total = 0
    with freqs_loc.open() as f:
        for i, line in tqdm(enumerate(f), desc="pass 1"):
            freq, doc_freq, _ = line.rstrip().split("\t", 2)
            freq = int(freq)
            counts.inc(i + 1, freq)
            total += freq
    counts.smooth()
    log_total = math.log(total) if total else 0.0

    probs = {}
    with freqs_loc.open() as f:
        for line in tqdm(f, desc="pass 2"):
            freq, doc_freq, key = line.rstrip().split("\t", 2)
            doc_freq = int(doc_freq)
            freq = int(freq)
            if doc_freq >= min_doc_freq and freq >= min_freq and len(key) < max_length:
                try:
                    word = literal_eval(key)
                except SyntaxError:
                    word = literal_eval(f"'{key}'")
                smooth_count = counts.smoother(int(freq))
                probs[word] = math.log(smooth_count) - log_total

    oov_prob = math.log(counts.smoother(0)) - log_total if total else -20.0
    return probs, oov_prob


def main(input_path: str | None, output_path: str, min_word_frequency: int) -> None:
    if input_path is not None:
        input_path = cached_path(input_path)
        freq_path = Path(input_path)
    else:
        freq_path = None

    probs, oov_prob = (
        read_freqs(freq_path, min_freq=min_word_frequency)
        if freq_path is not None
        else ({}, -20.0)
    )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"lang": "en", "settings": {"oov_prob": oov_prob}}))
        f.write("\n")
        for word, prob in probs.items():
            f.write(json.dumps({"orth": word, "prob": prob}))
            f.write("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input_path", type=str, default=None, help="Path to the frequency TSV file.")
    parser.add_argument("--output_path", type=str, required=True, help="Output path for the JSONL vocabulary file.")
    parser.add_argument("--min_word_frequency", type=int, default=50, help="Minimum frequency for inclusion.")
    args = parser.parse_args()
    main(args.input_path, args.output_path, args.min_word_frequency)
