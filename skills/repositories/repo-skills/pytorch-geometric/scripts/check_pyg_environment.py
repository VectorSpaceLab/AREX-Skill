#!/usr/bin/env python3
"""Safe PyTorch Geometric environment diagnostic.

This script imports packages, reports backend facts, and optionally requires
PyTorch, PyG, or a neighbor-sampling extension. It does not download data,
allocate GPUs by default, start services, or write files.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from typing import Any


def import_status(name: str) -> dict[str, Any]:
    item: dict[str, Any] = {'name': name, 'ok': False}
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic surface
        item['error'] = f'{type(exc).__name__}: {exc}'
        return item
    item['ok'] = True
    item['version'] = getattr(module, '__version__', None)
    return item


def distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Print JSON output.')
    parser.add_argument('--require-torch', action='store_true', help='Fail if torch cannot import.')
    parser.add_argument('--require-pyg', action='store_true', help='Fail if torch_geometric cannot import.')
    parser.add_argument('--require-neighbor-backend', action='store_true', help='Fail if neither pyg_lib nor torch_sparse imports.')
    parser.add_argument('--check-cuda', action='store_true', help='Report CUDA availability without allocating tensors.')
    args = parser.parse_args()

    modules = {
        'torch': import_status('torch'),
        'torch_geometric': import_status('torch_geometric'),
        'pyg_lib': import_status('pyg_lib'),
        'torch_sparse': import_status('torch_sparse'),
        'torch_scatter': import_status('torch_scatter'),
    }

    result: dict[str, Any] = {
        'ok': True,
        'python': sys.version.split()[0],
        'modules': modules,
        'distributions': {
            'torch': distribution_version('torch'),
            'torch-geometric': distribution_version('torch-geometric'),
            'pyg-lib': distribution_version('pyg-lib'),
            'torch-sparse': distribution_version('torch-sparse'),
            'torch-scatter': distribution_version('torch-scatter'),
        },
        'checks': [],
    }

    torch_module = sys.modules.get('torch') if modules['torch']['ok'] else None
    if torch_module is not None:
        result['torch_backend'] = {
            'cuda_version': getattr(getattr(torch_module, 'version', None), 'cuda', None),
            'cuda_available': bool(torch_module.cuda.is_available()) if args.check_cuda or hasattr(torch_module, 'cuda') else None,
        }

    def fail(message: str) -> None:
        result['ok'] = False
        result['checks'].append({'ok': False, 'message': message})

    if args.require_torch and not modules['torch']['ok']:
        fail('torch is required but could not be imported')
    if args.require_pyg and not modules['torch_geometric']['ok']:
        fail('torch_geometric is required but could not be imported')
    if args.require_neighbor_backend and not (modules['pyg_lib']['ok'] or modules['torch_sparse']['ok']):
        fail('neighbor sampling backend required: install pyg-lib or torch-sparse matching the active torch build')

    if result['ok']:
        result['checks'].append({'ok': True, 'message': 'requested environment checks passed'})

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print('PyG environment:', 'ok' if result['ok'] else 'not ok')
        for name, status in modules.items():
            detail = status.get('version') or status.get('error') or 'unknown'
            print(f'- {name}: {"ok" if status["ok"] else "missing"} ({detail})')
        for check in result['checks']:
            print(f'- check: {check["message"]}')
    return 0 if result['ok'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
