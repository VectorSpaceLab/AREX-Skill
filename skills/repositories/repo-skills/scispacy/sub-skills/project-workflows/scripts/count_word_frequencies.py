#!/usr/bin/env python3
"""Count word and document frequencies from a raw text corpus.

This helper uses scispaCy's biomedical tokenizer to count token frequencies for
one text file per input document. It is a safer replacement for the source repo
script because it does not depend on the source checkout being on sys.path.

Example:
    python scripts/count_word_frequencies.py --raw-dir /path/to/raw --output-path /tmp/freqs.tsv
"""

from __future__ import annotations

import argparse
import io
from collections import Counter
from multiprocessing import Pool
from pathlib import Path
from typing import Iterable, List, Tuple

import spacy
from spacy.language import Language

from scispacy.custom_tokenizer import combined_rule_tokenizer


def count_frequencies(language_class: Language, input_path: Path) -> Tuple[Counter, Counter]:
    print(f"Processing {input_path}.")
    tokenizer = combined_rule_tokenizer(language_class())
    counts = Counter()
    doc_counts = Counter()
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            words = [t.text for t in tokenizer(line)]
            counts.update(words)
            doc_counts.update(set(words))
    return counts, doc_counts


def parallelize(tasks: Iterable[Tuple[Language, Path]], jobs: int) -> List[Tuple[Counter, Counter]]:
    with Pool(processes=jobs) as pool:
        return pool.starmap(count_frequencies, tasks)


def merge_counts(frequencies: List[Tuple[Counter, Counter]], output_path: Path) -> None:
    counts = Counter()
    doc_counts = Counter()
    for word_count, doc_count in frequencies:
        counts.update(word_count)
        doc_counts.update(doc_count)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(output_path, "w", encoding="utf-8") as file_:
        for word, count in counts.most_common():
            if not word.isspace():
                file_.write(f"{count}\t{doc_counts[word]}\t{repr(word)}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True, help="Directory containing raw text files.")
    parser.add_argument("--output-path", type=Path, required=True, help="Output TSV path for the merged counts.")
    parser.add_argument("--jobs", type=int, default=2, help="Number of worker processes.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    language_class = spacy.util.get_lang_class("en")
    raw_files = [path for path in sorted(args.raw_dir.iterdir()) if path.is_file()]
    tasks = [(language_class, path) for path in raw_files]
    if not tasks:
        raise SystemExit(f"No input files found in {args.raw_dir}")
    frequencies = parallelize(tasks, args.jobs) if args.jobs > 1 else [count_frequencies(*task) for task in tasks]
    merge_counts(frequencies, args.output_path)
    print(f"Wrote {args.output_path}")


if __name__ == "__main__":
    main()
