#!/usr/bin/env python3
"""Check a mixtral-offloading runtime without downloading model weights."""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', help='Optional user checkout root to test src.* imports.')
    parser.add_argument('--require-cuda', action='store_true', help='Fail if torch CUDA is unavailable.')
    args = parser.parse_args()

    if args.repo_root:
        sys.path.insert(0, str(Path(args.repo_root).resolve()))

    modules = ['torch', 'transformers', 'hqq', 'triton', 'safetensors', 'numpy', 'tqdm']
    if args.repo_root:
        modules += ['src.build_model', 'src.packing', 'src.triton_kernels', 'src.expert_cache', 'src.expert_wrapper', 'src.custom_layers', 'src.utils']

    for name in modules:
        importlib.import_module(name)
        print(f'PASS import {name}')

    import torch
    print(f'torch={torch.__version__} cuda_build={torch.version.cuda}')
    cuda_ok = torch.cuda.is_available()
    print(f'cuda_available={cuda_ok} device_count={torch.cuda.device_count()}')
    if cuda_ok:
        x = torch.ones((1,), device='cuda')
        y = (x + 1).item()
        print(f'PASS cuda tensor value={y} device={torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)}')
    elif args.require_cuda:
        print('FAIL CUDA is required for offloaded inference/Triton kernel verification', file=sys.stderr)
        return 2

    if args.repo_root:
        from src.build_model import OffloadConfig
        cfg = OffloadConfig(main_size=4, offload_size=4, buffer_size=1, offload_per_layer=1)
        print(f'PASS source OffloadConfig {cfg}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
