#!/usr/bin/env python3
"""Check an SDV runtime without depending on the original source checkout.

Examples:
  python scripts/check_import.py
  python scripts/check_import.py --require-dot
  python scripts/check_import.py --check-cuda
  python scripts/check_import.py --require-cuda --json
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import shutil
import sys
from importlib import metadata


MODULES = [
    'sdv',
    'sdv.metadata',
    'sdv.datasets',
    'sdv.io.local',
    'sdv.constraints',
    'sdv.cag',
    'sdv.single_table',
    'sdv.multi_table',
    'sdv.sequential',
    'sdv.evaluation',
    'sdv.utils',
]


def check_imports() -> dict:
    results = {}
    for module_name in MODULES:
        try:
            importlib.import_module(module_name)
            results[module_name] = {'status': 'pass'}
        except Exception as exc:  # pragma: no cover - diagnostic script
            results[module_name] = {'status': 'fail', 'error': f'{type(exc).__name__}: {exc}'}
    return results


def check_graphviz(require_dot: bool) -> dict:
    result = {'requested': require_dot, 'python_package': None, 'dot_available': False}
    try:
        import graphviz

        result['python_package'] = getattr(graphviz, '__version__', 'unknown')
        try:
            result['graphviz_version'] = list(graphviz.version())
        except Exception as exc:  # pragma: no cover - depends on host binary
            result['graphviz_error'] = f'{type(exc).__name__}: {exc}'
    except Exception as exc:  # pragma: no cover - depends on environment
        result['python_package_error'] = f'{type(exc).__name__}: {exc}'

    result['dot_available'] = shutil.which('dot') is not None
    if require_dot and not result['dot_available']:
        result['status'] = 'fail'
        result['error'] = 'Graphviz dot executable is required but was not found on PATH.'
    else:
        result['status'] = 'pass' if result['dot_available'] or not require_dot else 'warn'
    return result


def check_cuda(check_cuda: bool, require_cuda: bool) -> dict:
    result = {'requested': check_cuda or require_cuda, 'required': require_cuda}
    if not (check_cuda or require_cuda):
        result['status'] = 'not-requested'
        return result

    try:
        import torch

        result['torch_version'] = getattr(torch, '__version__', 'unknown')
        result['torch_cuda_version'] = getattr(torch.version, 'cuda', None)
        result['cuda_available'] = bool(torch.cuda.is_available())
        result['cuda_device_count'] = int(torch.cuda.device_count())
        if result['cuda_available']:
            result['device_name'] = torch.cuda.get_device_name(0)
            result['device_capability'] = list(torch.cuda.get_device_capability(0))
            tensor = torch.empty((1,), device='cuda')
            result['tiny_tensor_device'] = str(tensor.device)
    except Exception as exc:  # pragma: no cover - depends on optional backend
        result['status'] = 'fail' if require_cuda else 'warn'
        result['error'] = f'{type(exc).__name__}: {exc}'
        return result

    if require_cuda and not result.get('cuda_available'):
        result['status'] = 'fail'
        result['error'] = 'CUDA was required but torch.cuda.is_available() is false.'
    else:
        result['status'] = 'pass' if result.get('cuda_available') else 'warn'
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description='Check SDV import, Graphviz, and optional CUDA readiness.')
    parser.add_argument('--require-dot', action='store_true', help='Fail if Graphviz dot is unavailable.')
    parser.add_argument('--check-cuda', action='store_true', help='Probe torch CUDA and warn if unavailable.')
    parser.add_argument('--require-cuda', action='store_true', help='Fail if torch CUDA is unavailable.')
    parser.add_argument('--json', action='store_true', help='Emit JSON only.')
    args = parser.parse_args()

    report = {
        'python': platform.python_version(),
        'platform': platform.platform(),
        'sdv_distribution_version': None,
        'imports': check_imports(),
        'graphviz': check_graphviz(args.require_dot),
        'cuda': check_cuda(args.check_cuda, args.require_cuda),
    }
    try:
        report['sdv_distribution_version'] = metadata.version('sdv')
    except metadata.PackageNotFoundError:
        report['sdv_distribution_version'] = None

    import_failed = any(item['status'] == 'fail' for item in report['imports'].values())
    hard_failed = (
        import_failed
        or report['graphviz']['status'] == 'fail'
        or report['cuda']['status'] == 'fail'
        or report['sdv_distribution_version'] is None
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print(f"SDV distribution: {report['sdv_distribution_version']}")
        for module_name, result in report['imports'].items():
            print(f"import {module_name}: {result['status']}")
            if result.get('error'):
                print(f"  {result['error']}")
        print(f"Graphviz dot: {'available' if report['graphviz']['dot_available'] else 'not found'}")
        if report['cuda']['status'] != 'not-requested':
            print(f"CUDA status: {report['cuda']['status']}")
            print(f"CUDA available: {report['cuda'].get('cuda_available')}")
            if report['cuda'].get('device_name'):
                print(f"CUDA device 0: {report['cuda']['device_name']}")

    return 1 if hard_failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
