#!/usr/bin/env python3
"""Run a tiny CUDA/Triton smoke for mixtral-offloading kernel environments."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', help='Optional user checkout root containing src/triton_kernels.py.')
    parser.add_argument('--skip-if-no-cuda', action='store_true', help='Exit 0 instead of 2 when CUDA is unavailable.')
    args = parser.parse_args()

    import torch
    import triton  # noqa: F401

    if not torch.cuda.is_available():
        msg = 'CUDA is not available; Triton wrapper behavior is not verified.'
        print(msg)
        return 0 if args.skip_if_no_cuda else 2

    device = torch.device('cuda:0')
    x = torch.ones((1, 32), device=device, dtype=torch.float16).contiguous()
    (x + 1).sum().item()
    print('PASS torch CUDA tiny tensor')

    if not args.repo_root:
        print('PASS Triton import; pass --repo-root to exercise src.triton_kernels wrapper')
        return 0

    sys.path.insert(0, str(Path(args.repo_root).resolve()))
    from src.triton_kernels import triton_matmul4_transpose  # type: ignore

    # K=32 and N=32 match the retained Triton autotune block sizes. groupsize=1
    # uses scales/zeros shaped as (N, K). Zero-packed qweight should produce a
    # zero output when zeros=0 and scales=1.
    qweight = torch.zeros((16, 32), device=device, dtype=torch.int32)
    scales = torch.ones((32, 32), device=device, dtype=torch.float16)
    zeros = torch.zeros((32, 32), device=device, dtype=torch.float16)
    out = triton_matmul4_transpose(1, x, qweight, scales, zeros)
    torch.cuda.synchronize()
    if out.shape != (1, 32):
        raise AssertionError(f'unexpected output shape {tuple(out.shape)}')
    if not torch.isfinite(out).all():
        raise AssertionError('non-finite Triton output')
    print('PASS repo triton_matmul4_transpose tiny smoke', tuple(out.shape))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
