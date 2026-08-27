#!/usr/bin/env python
"""Quick MMGeneration install and backend smoke check.

This script is intentionally conservative:
- Default mode verifies imports and package versions only.
- `--check-cuda` adds a tiny CUDA allocation smoke test when a GPU is available.
- `--check-mmcv-ops` verifies the compiled MMCV ops import.

It does not train, download checkpoints, or touch repo state.
"""

from __future__ import annotations

import argparse
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Check MMGeneration install')
    parser.add_argument(
        '--check-cuda',
        action='store_true',
        help='run a tiny CUDA tensor smoke test when CUDA is available')
    parser.add_argument(
        '--check-mmcv-ops',
        action='store_true',
        help='import mmcv.ops to confirm compiled MMCV ops are usable')
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='print only failures and a short summary')
    return parser.parse_args()


def show(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(msg)


def fail(msg: str, code: int = 1) -> int:
    print(f'ERROR: {msg}', file=sys.stderr)
    return code


def import_and_report(names: Iterable[str], quiet: bool = False) -> int:
    for name in names:
        try:
            import_module(name)
        except Exception as exc:  # pragma: no cover - explicit smoke path
            return fail(f'could not import {name}: {exc}')
        show(f'import ok: {name}', quiet)
    return 0


def report_versions(quiet: bool = False) -> None:
    for dist_name in ['mmgen', 'mmcv-full', 'mmcls', 'torch', 'torchvision']:
        try:
            show(f'{dist_name}: {version(dist_name)}', quiet)
        except PackageNotFoundError:
            show(f'{dist_name}: not installed', quiet)


def check_cuda(quiet: bool = False) -> int:
    try:
        import torch
    except Exception as exc:
        return fail(f'could not import torch for CUDA check: {exc}')

    if not torch.cuda.is_available():
        return fail('CUDA is not available in this environment', code=2)

    try:
        device_count = torch.cuda.device_count()
        device_name = torch.cuda.get_device_name(0)
        capability = torch.cuda.get_device_capability(0)
        tensor = torch.empty((1,), device='cuda')
    except Exception as exc:  # pragma: no cover - explicit smoke path
        return fail(f'CUDA smoke failed: {exc}')

    show(f'cuda devices: {device_count}', quiet)
    show(f'cuda device 0: {device_name}', quiet)
    show(f'cuda capability 0: {capability}', quiet)
    show(f'cuda tensor device: {tensor.device}', quiet)
    return 0


def main() -> int:
    args = parse_args()
    show('MMGeneration install check', args.quiet)

    report_versions(args.quiet)

    rc = import_and_report([
        'mmgen',
        'mmgen.apis',
        'mmcv',
        'torch',
        'torchvision',
        'mmcls',
    ], args.quiet)
    if rc != 0:
        return rc

    if args.check_mmcv_ops:
        try:
            import_module('mmcv.ops')
        except Exception as exc:
            return fail(f'could not import mmcv.ops: {exc}')
        show('import ok: mmcv.ops', args.quiet)

    if args.check_cuda:
        rc = check_cuda(args.quiet)
        if rc != 0:
            return rc

    show('install check passed', args.quiet)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
