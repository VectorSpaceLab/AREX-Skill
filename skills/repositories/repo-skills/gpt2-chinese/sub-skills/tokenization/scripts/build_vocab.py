#!/usr/bin/env python3
"""Build a vocabulary from a JSON list of Chinese texts.

This is a safe replacement for the legacy keras-based cache/make_vocab.py.
It expects a GPT2-Chinese checkout so it can reuse the repo's optional thulac
user dictionary when available, but it can also run without that dictionary.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path
from typing import Iterable, List

SPECIAL_TOKENS = ["[SEP]", "[CLS]", "[MASK]", "[PAD]", "[UNK]"]


def resolve(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def to_tokens(segmented: object) -> List[str]:
    if isinstance(segmented, str):
        return [token for token in segmented.split() if token]
    tokens: List[str] = []
    for item in segmented:  # type: ignore[assignment]
        if isinstance(item, (list, tuple)) and item:
            token = str(item[0]).strip()
        else:
            token = str(item).strip()
        if token:
            tokens.append(token)
    return tokens


def iter_lines(raw_data_path: Path) -> Iterable[str]:
    with raw_data_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("raw data must be a JSON list of strings")
    for item in data:
        if isinstance(item, str):
            yield item


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a GPT2-Chinese vocabulary from a JSON corpus")
    parser.add_argument("--repo-root", required=True, help="Path to the GPT2-Chinese checkout")
    parser.add_argument("--raw-data-path", required=True, help="JSON list of source strings")
    parser.add_argument("--vocab-file", required=True, help="Output vocabulary file")
    parser.add_argument("--vocab-size", type=int, default=50000, help="Maximum vocabulary size including special tokens")
    parser.add_argument("--user-dict", default="tokenizations/thulac_dict/seg", help="Optional thulac user dictionary relative to repo root")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    raw_data_path = resolve(repo_root, args.raw_data_path)
    vocab_file = resolve(repo_root, args.vocab_file)
    user_dict = resolve(repo_root, args.user_dict)

    if not raw_data_path.exists():
        print(f"missing raw data file: {raw_data_path}", file=sys.stderr)
        return 2

    try:
        import thulac
    except Exception as exc:  # pragma: no cover - direct failure path
        print(f"thulac import failed: {exc}", file=sys.stderr)
        return 1

    if user_dict.exists():
        lac = thulac.thulac(user_dict=str(user_dict), seg_only=True)
    else:
        print(f"warning: user dictionary not found at {user_dict}; falling back to default segmentation", file=sys.stderr)
        lac = thulac.thulac(seg_only=True)

    counter = collections.Counter()
    total = 0
    for line in iter_lines(raw_data_path):
        total += 1
        text = line.replace("\n", " [SEP] ")
        segmented = lac.cut(text, text=True)
        counter.update(to_tokens(segmented))

    vocab_tokens = []
    seen = set()
    for token in SPECIAL_TOKENS:
        if token not in seen:
            vocab_tokens.append(token)
            seen.add(token)

    for token, _count in counter.most_common():
        if token in seen:
            continue
        vocab_tokens.append(token)
        seen.add(token)
        if len(vocab_tokens) >= args.vocab_size:
            break

    vocab_file.parent.mkdir(parents=True, exist_ok=True)
    with vocab_file.open("w", encoding="utf-8") as handle:
        for token in vocab_tokens[: args.vocab_size]:
            handle.write(token + "\n")

    print(f"wrote {len(vocab_tokens[: args.vocab_size])} tokens to {vocab_file}")
    print(f"processed {total} documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
