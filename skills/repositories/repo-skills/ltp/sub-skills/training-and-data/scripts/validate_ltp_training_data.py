#!/usr/bin/env python3
"""Lightweight LTP training data layout validator.

This script checks split-file presence and simple row structure. It does not
load datasets, tokenize, train, or evaluate models.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

SPECS = {
    "bio": {"files": ["train.bio", "dev.bio", "test.bio"], "vocabs": ["bio.txt"]},
    "ner": {"files": ["train.bio", "dev.bio", "test.bio"], "vocabs": ["bio.txt"]},
    "conllu": {"files": ["train.conllu", "dev.conllu", "test.conllu"], "vocabs": ["word.txt", "word_char.txt", "upos.txt", "xpos.txt", "deprel.txt"]},
    "dep": {"files": ["train.conllu", "dev.conllu", "test.conllu"], "vocabs": ["word.txt", "word_char.txt", "upos.txt", "xpos.txt", "deprel.txt"]},
    "sdp": {"files": ["train.conllu", "dev.conllu", "test.conllu"], "vocabs": ["word.txt", "word_char.txt", "upos.txt", "xpos.txt", "deprel.txt"]},
    "srl": {"files": ["train.txt", "dev.txt", "test.txt"], "vocabs": ["arguments.txt", "predicate.txt"]},
    "cws": {"files": ["train.txt", "dev.txt", "test.txt"], "vocabs": []},
    "pos": {"files": ["train.txt", "dev.txt", "test.txt"], "vocabs": []},
}


def check_nonempty(path: Path, errors: List[str]) -> None:
    if not path.is_file():
        errors.append(f"missing file: {path}")
        return
    if path.stat().st_size == 0:
        errors.append(f"empty file: {path}")


def check_bio(path: Path, errors: List[str]) -> None:
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if len(line.split()) < 2:
            errors.append(f"{path}:{lineno}: BIO row should have token and label columns")
            break


def check_conllu(path: Path, errors: List[str]) -> None:
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.startswith("#"):
            continue
        if len(line.split("\t")) < 8:
            errors.append(f"{path}:{lineno}: CoNLL-U row should have at least 8 tab-separated fields")
            break


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LTP training data split files and basic formats.")
    parser.add_argument("--task", required=True, choices=sorted(SPECS))
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--strict-vocabs", action="store_true", help="fail when expected vocab files are missing")
    args = parser.parse_args()

    root = Path(args.data_dir)
    errors: List[str] = []
    if not root.is_dir():
        errors.append(f"data directory not found: {root}")
    else:
        spec = SPECS[args.task]
        for filename in spec["files"]:
            path = root / filename
            check_nonempty(path, errors)
            if path.is_file() and args.task in {"bio", "ner"}:
                check_bio(path, errors)
            if path.is_file() and args.task in {"conllu", "dep", "sdp"}:
                check_conllu(path, errors)
        vocab_root = root / "vocabs"
        for vocab in spec["vocabs"]:
            vpath = vocab_root / vocab
            if not vpath.is_file():
                msg = f"missing expected vocab file: {vpath}"
                if args.strict_vocabs:
                    errors.append(msg)
                else:
                    print(f"warning: {msg}")

    if errors:
        print("LTP training data validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print(f"LTP training data validation passed for task={args.task} data_dir={root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
