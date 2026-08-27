#!/usr/bin/env python3
"""Check MMDeploy backend readiness and custom-op availability.

Purpose:
    Provide a safe, read-only environment check for MMDeploy backend packages,
    converter tools, and backend-manager custom-op paths.

Prerequisites:
    - A Python environment where MMDeploy is importable, either from the
      installed package set or via --repo-root.
    - Optional backend packages/toolkits only for the backends you want to
      inspect.

Examples:
    python scripts/check_env.py
    python scripts/check_env.py --backend tensorrt --with-custom-ops
    python scripts/check_env.py --repo-root <checkout-root> --backend onnxruntime --json
"""
from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import platform
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

BACKEND_ALIASES = {
    'ort': 'onnxruntime',
    'trt': 'tensorrt',
    'torch_jit': 'torchscript',
    'torchjit': 'torchscript',
    'libtorch': 'torchscript',
    'ppl': 'pplnn',
    'ppl.nn': 'pplnn',
}
KNOWN_BACKENDS = [
    'onnxruntime',
    'tensorrt',
    'ncnn',
    'openvino',
    'pplnn',
    'torchscript',
    'rknn',
    'ascend',
    'coreml',
    'tvm',
    'vacc',
    'snpe',
    'sdk',
]


def add_repo_root(repo_root: Optional[str]) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def safe_version(package: str) -> str:
    try:
        return metadata.version(package)
    except Exception:
        return 'NotInstalled'


def collect_env() -> Dict[str, Any]:
    """Collect a compact environment summary without side effects."""
    env: Dict[str, Any] = {
        'Python': sys.version.split()[0],
        'Platform': platform.platform(),
        'MMDeploy': safe_version('mmdeploy'),
        'MMEngine': safe_version('mmengine'),
        'MMCV': safe_version('mmcv'),
        'Torch': safe_version('torch'),
        'TorchVision': safe_version('torchvision'),
        'ONNX': safe_version('onnx'),
    }
    try:
        import mmdeploy  # type: ignore

        env['MMDeployPackageVersion'] = getattr(mmdeploy, '__version__', 'Unknown')
        try:
            from mmengine.utils import get_git_hash

            env['MMDeployGitHash'] = get_git_hash()[:7]
        except Exception:
            pass
    except Exception as exc:
        env['MMDeployImport'] = f'Failed: {exc.__class__.__name__}'
    return env


def get_backend_names(selected: Optional[List[str]]) -> List[str]:
    if not selected or selected == ['all']:
        return list(KNOWN_BACKENDS)

    names: List[str] = []
    for raw in selected:
        for item in raw.split(','):
            item = item.strip().lower()
            if not item:
                continue
            names.append(BACKEND_ALIASES.get(item, item))
    seen = set()
    deduped: List[str] = []
    for name in names:
        if name not in seen:
            seen.add(name)
            deduped.append(name)
    return deduped


def safe_call(func, *args, **kwargs):
    try:
        return True, func(*args, **kwargs)
    except Exception as exc:
        return False, f'{exc.__class__.__name__}: {exc}'


def inspect_backend(name: str, with_custom_ops: bool = False) -> Dict[str, Any]:
    try:
        from mmdeploy.backend.base import get_backend_manager
    except Exception as exc:
        return {
            'backend': name,
            'manager': None,
            'available': False,
            'version': 'None',
            'custom_ops_available': None,
            'availability_error': f'Failed to import backend manager: {exc.__class__.__name__}: {exc}',
            'version_error': None,
        }

    manager = get_backend_manager(name)
    report: Dict[str, Any] = {
        'backend': name,
        'manager': None if manager is None else manager.__name__,
        'available': False,
        'version': 'None',
        'custom_ops_available': None,
        'availability_error': None,
        'version_error': None,
    }

    if manager is None:
        report['availability_error'] = 'Backend manager not registered'
        return report

    ok, available = safe_call(manager.is_available)
    if ok:
        report['available'] = bool(available)
    else:
        report['availability_error'] = available

    if report['available']:
        ok, version = safe_call(manager.get_version)
        if ok:
            report['version'] = str(version)
        else:
            report['version_error'] = version
    else:
        report['version'] = 'None'

    if with_custom_ops:
        ok, custom_ops = safe_call(manager.is_available, True)
        if ok:
            report['custom_ops_available'] = bool(custom_ops)
        else:
            report['custom_ops_available'] = f'Error: {custom_ops}'

    return report


def collect_codebase_versions() -> Dict[str, Any]:
    try:
        from mmdeploy.utils import get_codebase_version

        return get_codebase_version()
    except Exception as exc:
        return {'error': f'{exc.__class__.__name__}: {exc}'}


def build_report(backends: Iterable[str], with_custom_ops: bool) -> Dict[str, Any]:
    env = collect_env()
    backend_reports = [inspect_backend(name, with_custom_ops=with_custom_ops)
                        for name in backends]
    codebase_versions = collect_codebase_versions()
    return {
        'environment': env,
        'backends': backend_reports,
        'codebases': codebase_versions,
    }


def print_human_report(report: Dict[str, Any], with_custom_ops: bool) -> None:
    print('********** Environment information **********')
    for key, value in report['environment'].items():
        print(f'{key}: {value}')

    print('\n********** Backend information **********')
    for item in report['backends']:
        print(f"{item['backend']}:\t{item['version']}")
        if item.get('availability_error'):
            print(f"{item['backend']} availability error:\t{item['availability_error']}")
        if with_custom_ops:
            custom_ops = item.get('custom_ops_available')
            if custom_ops is not None:
                state = 'Available' if custom_ops is True else 'NotAvailable'
                print(f"{item['backend']} custom ops:\t{state}")
            elif item.get('availability_error'):
                print(f"{item['backend']} custom ops:\tCheckFailed")

    print('\n********** Codebase information **********')
    codebases = report.get('codebases', {})
    if isinstance(codebases, dict):
        for key, value in codebases.items():
            print(f'{key}:\t{value}')
    else:
        print(codebases)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Check MMDeploy backend package, tool, and custom-op readiness.'
    )
    parser.add_argument(
        '--repo-root',
        help='Optional repository root to add to sys.path before imports.')
    parser.add_argument(
        '--backend',
        action='append',
        help=('Backend name to inspect. Repeat the flag or pass comma-separated '
              'names. Default: all registered backends except default/pytorch.'),
    )
    parser.add_argument(
        '--with-custom-ops',
        action='store_true',
        help='Also check the backend custom-op build or plugin path when supported.',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Print a JSON report instead of the human-readable summary.',
    )
    parser.add_argument(
        '--fail-on-missing',
        action='store_true',
        help='Exit with status 1 when any requested backend or custom-op check is unavailable.',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    add_repo_root(args.repo_root)

    try:
        backends = get_backend_names(args.backend)
    except Exception as exc:
        print(f'Failed to resolve backend names: {exc}', file=sys.stderr)
        return 2

    try:
        report = build_report(backends, with_custom_ops=args.with_custom_ops)
    except Exception as exc:
        print(f'Failed to build report: {exc.__class__.__name__}: {exc}', file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print_human_report(report, with_custom_ops=args.with_custom_ops)

    if args.fail_on_missing:
        missing = []
        for item in report['backends']:
            if not item.get('available'):
                missing.append(item['backend'])
                continue
            if args.with_custom_ops and item.get('custom_ops_available') is not True:
                missing.append(f"{item['backend']}[custom-ops]")
        if missing:
            print(
                'Unavailable backends or custom-op paths: ' + ', '.join(missing),
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
