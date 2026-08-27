#!/usr/bin/env python3
"""Validate mixtral-offloading 2/3/4-bit packing round trips on CPU."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch


class PackedTensor(torch.Tensor):
    pass


def local_pack_4bit(W_q: torch.Tensor) -> torch.Tensor:
    W_q = W_q.to(torch.uint8)
    assert W_q.size(0) % 2 == 0
    return ((W_q[::2] << 4) | W_q[1::2]).to(torch.uint8)


def local_unpack_4bit(W_q: torch.Tensor) -> torch.Tensor:
    W_q = W_q.to(torch.uint8)
    out = torch.empty((2 * W_q.size(0), *W_q.shape[1:]), dtype=torch.uint8)
    out[::2] = W_q >> 4
    out[1::2] = W_q & 0xF
    return out


def local_pack_2bit(W_q: torch.Tensor) -> torch.Tensor:
    W_q = W_q.to(torch.uint8)
    assert W_q.size(0) % 4 == 0
    return ((W_q[::4] << 6) | (W_q[1::4] << 4) | (W_q[2::4] << 2) | W_q[3::4]).to(torch.uint8)


def local_unpack_2bit(W_q: torch.Tensor) -> torch.Tensor:
    W_q = W_q.to(torch.uint8)
    out = torch.empty((4 * W_q.size(0), *W_q.shape[1:]), dtype=torch.uint8)
    out[::4] = (W_q >> 6) & 0b11
    out[1::4] = (W_q >> 4) & 0b11
    out[2::4] = (W_q >> 2) & 0b11
    out[3::4] = W_q & 0b11
    return out


def local_pack_3bit(W_q: torch.Tensor) -> torch.Tensor:
    W_q = W_q.to(torch.uint8)
    height = W_q.size(0)
    rem = height % 10 or 10
    new_height = (height + 9) // 10
    packed = torch.zeros((new_height, *W_q.shape[1:]), dtype=torch.int32)
    for i in range(10):
        values = W_q[i::10].to(torch.int32) << (3 * (9 - i))
        if i < rem:
            packed |= values
        else:
            packed[: new_height - 1] |= values
    return packed


def local_unpack_3bit(W_q: torch.Tensor) -> torch.Tensor:
    assert W_q.dtype == torch.int32
    out = torch.empty((10 * W_q.size(0), *W_q.shape[1:]), dtype=torch.uint8)
    for i in range(10):
        out[i::10] = ((W_q >> (3 * (9 - i))) & 0b111).to(torch.uint8)
    return out


def maybe_repo_funcs(repo_root: str | None):
    if not repo_root:
        return None
    sys.path.insert(0, str(Path(repo_root).resolve()))
    from src import packing  # type: ignore
    return packing


def check(label: str, original: torch.Tensor, packed: torch.Tensor, unpacked: torch.Tensor) -> None:
    if not torch.equal(unpacked[: original.size(0)], original):
        raise AssertionError(f'{label} round trip failed')
    print(f'PASS {label}: original={tuple(original.shape)} packed={tuple(packed.shape)}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', help='Optional user checkout root; when provided, also test src.packing functions.')
    args = parser.parse_args()

    modules = [('bundled', None)]
    repo = maybe_repo_funcs(args.repo_root)
    if repo is not None:
        modules.append(('repo', repo))

    for name, mod in modules:
        p4 = mod.pack_4bit_u8_common if mod else local_pack_4bit
        u4 = mod.unpack_4bit_u8_common if mod else local_unpack_4bit
        p2 = mod.pack_2bit_u8_common if mod else local_pack_2bit
        u2 = mod.unpack_2bit_u8_common if mod else local_unpack_2bit
        p3 = mod.pack_3bit_i32_common if mod else local_pack_3bit
        u3 = mod.unpack_3bit_i32_common if mod else local_unpack_3bit
        w4 = (torch.arange(16, dtype=torch.uint8).reshape(4, 4) % 16)
        w2 = (torch.arange(16, dtype=torch.uint8).reshape(4, 4) % 4)
        w3 = (torch.arange(40, dtype=torch.uint8).reshape(10, 4) % 8)
        check(f'{name} 4bit', w4, p4(w4), u4(p4(w4)))
        check(f'{name} 2bit', w2, p2(w2), u2(p2(w2)))
        check(f'{name} 3bit', w3, p3(w3), u3(p3(w3)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
