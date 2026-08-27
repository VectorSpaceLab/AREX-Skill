#!/usr/bin/env python3
"""Convert JSONL with {"text": ...} rows into an RWKV .bin/.idx pair.

This is a safe, explicit-path adaptation of RWKV-LM's make_data.py. It never
modifies the source JSONL and never writes outside the requested output prefix.
"""
from __future__ import annotations

import argparse
import json
import random
import struct
from pathlib import Path

import numpy as np

DTYPE_CODES = {np.uint8: 1, np.int8: 2, np.int16: 3, np.int32: 4, np.int64: 5, float: 6, np.double: 7, np.uint16: 8}


class Trie:
    def __init__(self):
        self.to = [None for _ in range(256)]
        self.values = set()

    def add(self, key: bytes, idx: int, value: tuple[bytes, int]) -> None:
        if idx == len(key):
            self.values.add(value)
            return
        ch = key[idx]
        if self.to[ch] is None:
            self.to[ch] = Trie()
        self.to[ch].add(key, idx + 1, value)

    def find_longest(self, key: bytes, idx: int) -> tuple[int, tuple[bytes, int]]:
        node = self
        ret = None
        pos = idx
        while pos < len(key) and node.to[key[pos]] is not None:
            node = node.to[key[pos]]
            pos += 1
            if node.values:
                ret = (pos, next(iter(node.values)))
        if ret is None:
            raise ValueError(f"no tokenizer entry matches byte 0x{key[idx]:02x} at offset {idx}")
        return ret


class TrieTokenizer:
    def __init__(self, vocab_file: Path):
        self.idx2token: dict[int, bytes] = {}
        self.token2idx: dict[bytes, int] = {}
        for line in vocab_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            idx = int(line[: line.index(" ")])
            token_expr = line[line.index(" ") : line.rindex(" ")]
            token = eval(token_expr)  # RWKV vocab file uses Python bytes/string literals.
            token = token.encode("utf-8") if isinstance(token, str) else token
            if not isinstance(token, bytes):
                raise ValueError(f"bad token literal at index {idx}")
            self.idx2token[idx] = token
            self.token2idx[token] = idx
        self.root = Trie()
        for token, idx in self.token2idx.items():
            self.root.add(token, 0, (token, idx))

    def encode(self, text: str) -> list[int]:
        src = text.encode("utf-8")
        out: list[int] = []
        idx = 0
        while idx < len(src):
            idx, (_, token_id) = self.root.find_longest(src, idx)
            out.append(token_id)
        return out

    def decode(self, tokens: list[int]) -> str:
        return b"".join(self.idx2token[t] for t in tokens).decode("utf-8")


class MMapIndexedDatasetBuilder:
    def __init__(self, data_file: Path, dtype=np.uint16):
        self.data_file = data_file.open("wb")
        self.dtype = dtype
        self.sizes: list[int] = []
        self.doc_idx: list[int] = [0]
        self.count = 0

    def add_item(self, values: list[int]) -> None:
        arr = np.asarray(values, dtype=self.dtype)
        self.data_file.write(arr.tobytes(order="C"))
        self.sizes.append(arr.size)
        self.count += arr.size

    def end_document(self) -> None:
        self.doc_idx.append(len(self.sizes))

    def finalize(self, index_file: Path) -> None:
        self.data_file.close()
        dtype_size = self.dtype().itemsize
        pointers = []
        address = 0
        for size in self.sizes:
            pointers.append(address)
            address += size * dtype_size
        with index_file.open("wb") as f:
            f.write(b"MMIDIDX\x00\x00")
            f.write(struct.pack("<Q", 1))
            f.write(struct.pack("<B", DTYPE_CODES[self.dtype]))
            f.write(struct.pack("<Q", len(self.sizes)))
            f.write(struct.pack("<Q", len(self.doc_idx)))
            f.write(np.asarray(self.sizes, dtype=np.int32).tobytes(order="C"))
            f.write(np.asarray(pointers, dtype=np.int64).tobytes(order="C"))
            f.write(np.asarray(self.doc_idx, dtype=np.int64).tobytes(order="C"))


def default_vocab_file() -> Path | None:
    try:
        import rwkv  # type: ignore
        path = Path(rwkv.__file__).resolve().parent / "rwkv_vocab_v20230424.txt"
        return path if path.exists() else None
    except Exception:
        return None


def read_text_rows(path: Path) -> list[str]:
    rows = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {lineno}: invalid JSON: {exc}") from exc
        text = obj.get("text")
        if not isinstance(text, str):
            raise ValueError(f"line {lineno}: expected a string field named 'text'")
        rows.append(text)
    if not rows:
        raise ValueError("no non-empty JSONL rows with text fields found")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input JSONL file with a string text field")
    parser.add_argument("--output-prefix", required=True, type=Path, help="Output prefix without .bin/.idx")
    parser.add_argument("--repeat", type=int, default=1, help="Shuffle/write the corpus this many times")
    parser.add_argument("--ctx-len", type=int, default=0, help="Optional context length for final magic-prime hint")
    parser.add_argument("--seed", type=int, default=1234, help="Shuffle seed")
    parser.add_argument("--vocab-file", type=Path, default=None, help="RWKV rwkv_vocab_v20230424.txt path")
    args = parser.parse_args()

    if args.repeat <= 0:
        raise SystemExit("--repeat must be positive")
    vocab = args.vocab_file or default_vocab_file()
    if vocab is None or not vocab.exists():
        raise SystemExit("Provide --vocab-file or install the rwkv package with rwkv_vocab_v20230424.txt")
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    out_bin = Path(str(args.output_prefix) + ".bin")
    out_idx = Path(str(args.output_prefix) + ".idx")
    if out_bin.exists() or out_idx.exists():
        raise SystemExit(f"refusing to overwrite existing {out_bin} or {out_idx}")

    tokenizer = TrieTokenizer(vocab)
    rows = read_text_rows(args.input)
    rng = random.Random(args.seed)
    builder = MMapIndexedDatasetBuilder(out_bin)
    for rep in range(args.repeat):
        shuffled = list(rows)
        rng.shuffle(shuffled)
        for text in shuffled:
            tokens = tokenizer.encode(text)
            if tokenizer.decode(tokens) != text:
                raise ValueError("tokenizer roundtrip failed for one JSONL row")
            builder.add_item(tokens + [0])
            builder.end_document()
    builder.finalize(out_idx)
    print(f"wrote {out_bin}")
    print(f"wrote {out_idx}")
    print(f"documents={len(builder.sizes)} tokens={builder.count} dtype=uint16")
    if args.ctx_len > 0:
        from math import floor
        start = builder.count // args.ctx_len - 1
        print(f"ctx_len={args.ctx_len} candidate_search_start={start}")
        print("Run compute_magic_prime.py on this prefix for the exact --magic_prime value.")


if __name__ == "__main__":
    main()
