#!/usr/bin/env python3
"""Check a Raster Vision installation without running training or cloud jobs.

This helper is safe to run from any working directory. It imports the selected
Raster Vision packages, inspects distribution metadata, checks CLI help, and
optionally reports torch CUDA visibility. It does not submit AWS jobs, download
example data, or train a model.
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

DISTS = [
    'rastervision',
    'rastervision_pipeline',
    'rastervision_core',
    'rastervision_pytorch_learner',
    'rastervision_pytorch_backend',
    'rastervision_aws_s3',
    'rastervision_aws_batch',
]

OPTIONAL_DISTS = [
    'rastervision_aws_sagemaker',
    'rastervision_gdal_vsi',
]

MODULES = [
    'rastervision.pipeline',
    'rastervision.core',
    'rastervision.pytorch_learner',
    'rastervision.pytorch_backend',
    'rastervision.aws_s3',
    'rastervision.aws_batch',
]

OPTIONAL_MODULES = [
    'rastervision.aws_sagemaker',
    'rastervision.gdal_vsi',
]


def dist_versions(names: list[str]) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name in names:
        try:
            out[name] = version(name)
        except PackageNotFoundError:
            out[name] = None
    return out


def import_modules(names: list[str]) -> dict[str, dict[str, str | bool | None]]:
    out: dict[str, dict[str, str | bool | None]] = {}
    for name in names:
        try:
            mod = importlib.import_module(name)
            out[name] = {
                'ok': True,
                'file': getattr(mod, '__file__', None),
                'error': None,
            }
        except Exception as exc:  # pragma: no cover - diagnostic surface
            out[name] = {'ok': False, 'file': None, 'error': repr(exc)}
    return out


def cli_help(timeout: int) -> dict[str, Any]:
    cmd = [sys.executable, '-m', 'rastervision.pipeline.cli', '--help']
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - diagnostic surface
        return {'ok': False, 'command': cmd, 'error': repr(exc)}
    return {
        'ok': proc.returncode == 0,
        'command': cmd,
        'returncode': proc.returncode,
        'stdout_first_lines': proc.stdout.splitlines()[:20],
        'stderr_first_lines': proc.stderr.splitlines()[:20],
    }


def torch_status() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - optional diagnostic
        return {'installed': False, 'error': repr(exc)}

    status: dict[str, Any] = {
        'installed': True,
        'version': getattr(torch, '__version__', None),
        'cuda_version': getattr(torch.version, 'cuda', None),
        'cuda_available': bool(torch.cuda.is_available()),
        'cuda_device_count': int(torch.cuda.device_count()),
    }
    if torch.cuda.is_available():
        try:
            status['first_device'] = torch.cuda.get_device_name(0)
            status['first_device_capability'] = torch.cuda.get_device_capability(0)
        except Exception as exc:  # pragma: no cover - diagnostic only
            status['device_error'] = repr(exc)
    return status


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Check a Raster Vision installation without running training or cloud jobs.'
    )
    parser.add_argument('--json', action='store_true', help='Emit JSON only.')
    parser.add_argument('--timeout', type=int, default=30, help='CLI help timeout in seconds.')
    args = parser.parse_args()

    report = {
        'python': sys.executable,
        'python_version': sys.version,
        'distributions': dist_versions(DISTS),
        'optional_distributions': dist_versions(OPTIONAL_DISTS),
        'imports': import_modules(MODULES),
        'optional_imports': import_modules(OPTIONAL_MODULES),
        'cli_help': cli_help(args.timeout),
        'torch': torch_status(),
    }

    required_ok = all(v is not None for v in report['distributions'].values())
    required_ok = required_ok and all(v['ok'] for v in report['imports'].values())
    required_ok = required_ok and report['cli_help']['ok']
    report['required_ok'] = required_ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print('Raster Vision installation check')
        print(f'Python: {report["python"]}')
        print(f'Required distributions: {report["distributions"]}')
        print(f'Optional distributions: {report["optional_distributions"]}')
        for name, item in report['imports'].items():
            print(f'Import {name}: {"OK" if item["ok"] else "FAIL"}')
            if item['error']:
                print(f'  {item["error"]}')
        for name, item in report['optional_imports'].items():
            state = 'OK' if item['ok'] else 'missing or failed'
            print(f'Optional import {name}: {state}')
        print(f'CLI help: {"OK" if report["cli_help"]["ok"] else "FAIL"}')
        print(f'Torch: {report["torch"]}')
        print(f'Required check: {"OK" if required_ok else "FAIL"}')
    return 0 if required_ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
