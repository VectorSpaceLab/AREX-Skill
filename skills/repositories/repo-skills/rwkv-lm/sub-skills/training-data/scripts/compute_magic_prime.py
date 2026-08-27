#!/usr/bin/env python3
"""Compute the RWKV binidx training magic prime.

The RWKV-LM training scripts use a prime p where p % 3 == 2 and
p < token_count // ctx_len. This helper can read the token count from a RWKV
MMapIndexedDataset prefix or accept an explicit token count.
"""
from __future__ import annotations

import argparse
import mmap
import os
import struct
from pathlib import Path

DTYPE_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 8, 7: 8, 8: 2}
MAGIC = b"MMIDIDX\x00\x00"


def is_prime(n: int) -> bool:
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def read_dtype_size(prefix: Path) -> int:
    idx_path = prefix.with_suffix(prefix.suffix + ".idx") if prefix.suffix else Path(str(prefix) + ".idx")
    with idx_path.open("rb") as f:
        header = f.read(9)
        if header != MAGIC:
            raise ValueError(f"{idx_path} does not look like an RWKV MMIDIDX index")
        version = struct.unpack("<Q", f.read(8))[0]
        if version != 1:
            raise ValueError(f"unsupported MMIDIDX version {version}")
        dtype_code = struct.unpack("<B", f.read(1))[0]
    try:
        return DTYPE_SIZES[dtype_code]
    except KeyError as exc:
        raise ValueError(f"unknown MMIDIDX dtype code {dtype_code}") from exc


def token_count_from_prefix(prefix: Path) -> int:
    bin_path = prefix.with_suffix(prefix.suffix + ".bin") if prefix.suffix else Path(str(prefix) + ".bin")
    dtype_size = read_dtype_size(prefix)
    size = bin_path.stat().st_size
    if size % dtype_size != 0:
        raise ValueError(f"{bin_path} size {size} is not divisible by dtype width {dtype_size}")
    return size // dtype_size


def compute_magic_prime(token_count: int, ctx_len: int) -> int:
    if ctx_len <= 0:
        raise ValueError("ctx_len must be positive")
    start = token_count // ctx_len - 1
    for candidate in range(start, 1, -1):
        if candidate % 3 == 2 and is_prime(candidate):
            return candidate
    raise ValueError("no valid magic prime found; dataset may be too small for this ctx_len")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--data-prefix", type=Path, help="RWKV binidx prefix without .bin/.idx suffix")
    group.add_argument("--token-count", type=int, help="Explicit flat token count")
    parser.add_argument("--ctx-len", type=int, required=True, help="Training context length")
    args = parser.parse_args()

    token_count = args.token_count if args.token_count is not None else token_count_from_prefix(args.data_prefix)
    magic = compute_magic_prime(token_count, args.ctx_len)
    print(f"token_count={token_count}")
    print(f"ctx_len={args.ctx_len}")
    print(f"magic_prime={magic}")
    print(f"--my_exit_tokens {token_count} --magic_prime {magic} --ctx_len {args.ctx_len}")


if __name__ == "__main__":
    main()
