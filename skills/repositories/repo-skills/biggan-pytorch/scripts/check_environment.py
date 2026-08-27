#!/usr/bin/env python3
"""Read-only BigGAN-PyTorch environment and import diagnostic.

Usage: python check_environment.py --repo-root /path/to/checkout
The script does not download data, change files, or launch training.
"""
from __future__ import annotations
import argparse
import importlib
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', type=Path, default=None)
    parser.add_argument('--skip-model', action='store_true')
    args = parser.parse_args()
    if args.repo_root:
        sys.path.insert(0, str(args.repo_root.resolve()))
    try:
        import torch
        import torchvision
        print(f'torch={torch.__version__}')
        print(f'torchvision={torchvision.__version__}')
        print(f'cuda_available={torch.cuda.is_available()}')
        if not torch.cuda.is_available():
            print('BACKEND_BLOCKED: CUDA is required by core train/sample/metric paths')
            return 2
        free, total = torch.cuda.mem_get_info()
        print(f'cuda_memory_free={free} total={total}')
        probe = torch.zeros(1, device='cuda')
        print(f'cuda_probe={probe.device}')
    except Exception as exc:
        print(f'BACKEND_BLOCKED: {type(exc).__name__}: {exc}')
        return 2
    modules = ['animal_hash', 'utils', 'losses', 'datasets', 'inception_utils',
               'train', 'sample', 'make_hdf5', 'calculate_inception_moments']
    if not args.skip_model:
        modules += ['BigGAN', 'BigGANdeep']
    failed = 0
    for name in modules:
        try:
            mod = importlib.import_module(name)
            print(f'import_ok={name}:{getattr(mod, "__file__", "built-in")}')
        except Exception as exc:
            failed += 1
            print(f'import_failed={name}:{type(exc).__name__}:{exc}')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
