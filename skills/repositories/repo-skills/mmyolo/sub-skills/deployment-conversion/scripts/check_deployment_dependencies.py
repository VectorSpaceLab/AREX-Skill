#!/usr/bin/env python3
"""Probe deployment-oriented optional dependencies and backend readiness.

This script only inspects imports, binaries, and light runtime facts. It does not
export models, build engines, download artifacts, or run vendor tooling.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import platform
import shutil
import sys
import warnings
from dataclasses import dataclass, asdict
from typing import Dict, List, Sequence

warnings.filterwarnings('ignore', category=FutureWarning)

BACKEND_CHOICES = ['all', 'onnxruntime', 'tensorrt', 'rknn', 'mmdeploy', 'deepstream']


@dataclass
class CheckResult:
    name: str
    available: bool
    detail: str


@dataclass
class ProfileResult:
    name: str
    checks: List[CheckResult]

    @property
    def missing(self) -> List[CheckResult]:
        return [check for check in self.checks if not check.available]

    @property
    def ok(self) -> bool:
        return not self.missing


def probe_module(module_name: str) -> CheckResult:
    """Check whether a Python module can be imported."""
    try:
        spec = importlib.util.find_spec(module_name)
    except Exception as exc:  # pragma: no cover - import machinery failure path
        return CheckResult(module_name, False, f'spec lookup failed: {exc}')

    if spec is None:
        return CheckResult(module_name, False, 'not installed')

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return CheckResult(module_name, False, f'import failed: {exc}')

    version = getattr(module, '__version__', None)
    detail = f'present{f" ({version})" if version else ""}'
    return CheckResult(module_name, True, detail)


def probe_any_module(label: str, candidates: Sequence[str]) -> CheckResult:
    """Return the first available module among a candidate list."""
    details: List[str] = []
    for candidate in candidates:
        result = probe_module(candidate)
        if result.available:
            return CheckResult(label, True, f'{candidate}: {result.detail}')
        details.append(f'{candidate}: {result.detail}')
    return CheckResult(label, False, '; '.join(details))


def probe_binary(binary_name: str) -> CheckResult:
    path = shutil.which(binary_name)
    if path is None:
        return CheckResult(binary_name, False, 'not found on PATH')
    return CheckResult(binary_name, True, path)


def probe_torch_cuda() -> List[CheckResult]:
    result = probe_module('torch')
    checks = [result]
    if not result.available:
        checks.append(CheckResult('torch.cuda', False, 'torch is unavailable'))
        return checks

    try:
        import torch
    except Exception as exc:  # pragma: no cover - import failure after probe
        checks.append(CheckResult('torch.cuda', False, f'import failed: {exc}'))
        return checks

    cuda_available = torch.cuda.is_available()
    version = getattr(torch.version, 'cuda', None)
    detail = f'available={cuda_available}'
    if version:
        detail += f', torch.version.cuda={version}'
    checks.append(CheckResult('torch.cuda', cuda_available, detail))
    return checks


PROFILE_CHECKS: Dict[str, Dict[str, Sequence[str]]] = {
    'onnxruntime': {
        'modules': ('torch', 'onnx', 'onnxruntime', 'onnxsim', 'mmengine',
                    'mmcv', 'mmdet', 'mmyolo'),
        'binaries': (),
    },
    'tensorrt': {
        'modules': ('torch', 'onnx', 'tensorrt'),
        'binaries': ('nvidia-smi', 'trtexec'),
    },
    'rknn': {
        'modules': ('torch', 'onnx'),
        'module_groups': ('rknn.api', 'rknn_toolkit2'),
        'binaries': (),
    },
    'mmdeploy': {
        'modules': ('torch', 'onnx', 'mmdeploy', 'mmdeploy_runtime', 'onnxruntime', 'mmyolo'),
        'binaries': (),
    },
    'deepstream': {
        'modules': ('torch', 'onnx', 'tensorrt'),
        'binaries': ('nvidia-smi', 'deepstream-app', 'cmake', 'make'),
    },
}


def build_profile(name: str) -> ProfileResult:
    spec = PROFILE_CHECKS[name]
    checks: List[CheckResult] = []

    if name in ('tensorrt', 'deepstream'):
        checks.extend(probe_torch_cuda())

    for module_name in spec.get('modules', ()):
        checks.append(probe_module(module_name))

    if name == 'rknn':
        checks.append(probe_any_module('rknn', ['rknn.api', 'rknn_toolkit2']))

    for binary_name in spec.get('binaries', ()):
        checks.append(probe_binary(binary_name))

    # Deduplicate repeated torch checks when a profile already adds it explicitly.
    unique: Dict[str, CheckResult] = {}
    ordered: List[CheckResult] = []
    for check in checks:
        if check.name in unique:
            continue
        unique[check.name] = check
        ordered.append(check)
    return ProfileResult(name=name, checks=ordered)


def selected_profiles(requested: Sequence[str]) -> List[str]:
    if 'all' in requested:
        return [name for name in PROFILE_CHECKS]
    seen = []
    for item in requested:
        if item not in seen:
            seen.append(item)
    return seen


def render_text(profiles: Sequence[ProfileResult]) -> str:
    lines: List[str] = []
    lines.append(f'Platform: {platform.platform()}')
    lines.append(f'Python: {sys.version.split()[0]}')
    lines.append('')
    for profile in profiles:
        lines.append(f'[{"ok" if profile.ok else "missing"}] {profile.name}')
        for check in profile.checks:
            status = 'ok' if check.available else 'missing'
            lines.append(f'  - [{status}] {check.name}: {check.detail}')
        if profile.missing:
            lines.append('  recovery: add the missing package, binary, or vendor stack before running this backend path')
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def render_json(profiles: Sequence[ProfileResult]) -> str:
    payload = {
        'platform': platform.platform(),
        'python': sys.version.split()[0],
        'profiles': [
            {
                'name': profile.name,
                'ok': profile.ok,
                'checks': [asdict(check) for check in profile.checks],
                'missing': [asdict(check) for check in profile.missing],
            } for profile in profiles
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Probe deployment dependency and backend readiness without building artifacts.')
    parser.add_argument(
        '--backend',
        nargs='+',
        choices=BACKEND_CHOICES,
        default=['all'],
        help='Backend profile(s) to probe. Default: all.')
    parser.add_argument(
        '--json',
        action='store_true',
        help='Emit JSON instead of human-readable text.')
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit with status 1 when any selected profile has missing checks.')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile_names = selected_profiles(args.backend)
    profiles = [build_profile(name) for name in profile_names]

    output = render_json(profiles) if args.json else render_text(profiles)
    print(output, end='')

    if args.strict and any(not profile.ok for profile in profiles):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
