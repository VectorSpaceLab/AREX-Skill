#!/usr/bin/env python3
'''
Static dependency probe for the GeoAI QGIS plugin.

This script is read-only by design. It does not install packages, start QGIS,
contact the network, or write into user directories.
It reports the managed dependency plan, optional platform-specific packages,
and the recommended CUDA wheel family when enough local hints are provided.
'''

from __future__ import annotations

import argparse
import importlib
import json
import os
import platform as _platform
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class PackageSpec:
    dist_name: str
    module_name: str
    specifier: str
    purpose: str
    optional_install: bool = False
    optional_verify: bool = False


BASE_PACKAGES: tuple[PackageSpec, ...] = (
    PackageSpec('torch', 'torch', '>=2.0.0', 'PyTorch runtime'),
    PackageSpec('torchvision', 'torchvision', '>=0.15.0', 'TorchVision runtime'),
    PackageSpec('geoai-py', 'geoai', '>=0.39.0', 'GeoAI base package'),
    PackageSpec('segment-geospatial', 'samgeo', '', 'GeoAI segmentation helper'),
    PackageSpec('sam3', 'sam3', '', 'SAM3 / SamGeo3 backend'),
    PackageSpec('deepforest', 'deepforest', '', 'Tree segmentation backend'),
    PackageSpec('omniwatermask', 'omniwatermask', '', 'Water segmentation backend'),
    PackageSpec('transformers', 'transformers', '>=4.56.2', 'Transformers runtime'),
)

CUDA_DRIVER_REQUIREMENTS = {
    'cu128': 570,
    'cu126': 560,
    'cu124': 550,
}


def _platform_name(raw: str) -> str:
    if raw != 'auto':
        return raw
    if sys.platform.startswith('win'):
        return 'win32'
    if sys.platform == 'darwin':
        return 'darwin'
    return 'linux'


def _default_python_version() -> str:
    return f'{sys.version_info.major}.{sys.version_info.minor}'


def _default_cache_dir() -> str:
    return (
        os.environ.get('GEOAI_CACHE_DIR')
        or os.environ.get('GEOAI_VENV_DIR')
        or str(Path.home() / '.qgis_geoai')
    )


def build_package_plan(platform_name: str) -> list[PackageSpec]:
    plan = list(BASE_PACKAGES)
    if platform_name == 'win32':
        insertion = 4
        plan.insert(
            insertion,
            PackageSpec(
                'triton-windows',
                'triton',
                '',
                'Windows triton shim for SAM3',
                optional_install=True,
                optional_verify=True,
            ),
        )
        plan = [
            PackageSpec(
                p.dist_name,
                p.module_name,
                p.specifier,
                p.purpose,
                p.optional_install,
                p.optional_verify or p.dist_name == 'sam3',
            )
            for p in plan
        ]
    if platform_name == 'darwin':
        plan = [
            PackageSpec(
                p.dist_name,
                p.module_name,
                p.specifier,
                p.purpose,
                p.optional_install or p.dist_name == 'sam3',
                p.optional_verify or p.dist_name == 'sam3',
            )
            for p in plan
        ]
    return plan


def select_cuda_index(
    platform_name: str,
    compute_capability: float | None,
    gpu_name: str | None,
    driver_major: int | None,
) -> tuple[str | None, str]:
    if compute_capability is not None:
        needs_cu128 = compute_capability >= 12.0
    else:
        needs_cu128 = bool(gpu_name and 'RTX 50' in gpu_name.upper())

    if needs_cu128:
        index = 'cu128'
    elif platform_name == 'win32' and driver_major is not None and driver_major >= 560:
        index = 'cu126'
    else:
        index = 'cu124'

    required_driver = CUDA_DRIVER_REQUIREMENTS.get(index, 0)
    if driver_major is not None and driver_major < required_driver:
        return None, (
            f'NVIDIA driver {driver_major} is too old for {index} '
            f'(needs >= {required_driver}); use CPU or Pixi instead.'
        )

    return index, f'Recommended PyTorch CUDA wheel family: {index}'


def _safe_metadata_version(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def _safe_import(module_name: str) -> tuple[bool, str | None]:
    try:
        importlib.import_module(module_name)
        return True, None
    except Exception as exc:
        return False, f'{type(exc).__name__}: {exc}'


def probe_packages(
    plan: Iterable[PackageSpec],
    check_installed: bool,
    probe_imports: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in plan:
        row: dict[str, Any] = {
            'dist_name': spec.dist_name,
            'module_name': spec.module_name,
            'specifier': spec.specifier,
            'purpose': spec.purpose,
            'optional_install': spec.optional_install,
            'optional_verify': spec.optional_verify,
        }
        if check_installed:
            row['installed_version'] = _safe_metadata_version(spec.dist_name)
            row['installed'] = row['installed_version'] is not None
        if probe_imports:
            ok, err = _safe_import(spec.module_name)
            row['import_ok'] = ok
            row['import_error'] = err
        rows.append(row)
    return rows


def render_text(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append('GeoAI QGIS dependency probe')
    lines.append(f"Platform: {report['platform']}")
    lines.append(f"Python version target: {report['python_version']}")
    lines.append(f"Managed cache dir: {report['cache_dir']}")
    lines.append(f"CUDA recommendation: {report['cuda_message']}")
    if report.get('cuda_reason'):
        lines.append(f"CUDA note: {report['cuda_reason']}")
    lines.append('')
    lines.append('Packages:')
    for row in report['packages']:
        flags: list[str] = []
        if row.get('optional_install'):
            flags.append('optional-install')
        if row.get('optional_verify'):
            flags.append('optional-verify')
        flag_text = f" ({', '.join(flags)})" if flags else ''
        version = row.get('installed_version') or 'not checked'
        lines.append(
            f"- {row['dist_name']}{row['specifier']} -> {row['module_name']} "
            f"[{version}]{flag_text}"
        )
        if row.get('import_error'):
            lines.append(f"  import error: {row['import_error']}")
    if report.get('warnings'):
        lines.append('')
        lines.append('Warnings:')
        for warning in report['warnings']:
            lines.append(f'- {warning}')
    return '\n'.join(lines).rstrip() + '\n'


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    platform_name = _platform_name(args.platform)
    plan = build_package_plan(platform_name)
    if args.check_installed:
        packages = probe_packages(plan, check_installed=True, probe_imports=args.probe_imports)
    else:
        packages = probe_packages(plan, check_installed=False, probe_imports=args.probe_imports)

    cuda_index, cuda_message = select_cuda_index(
        platform_name=platform_name,
        compute_capability=args.compute_capability,
        gpu_name=args.gpu_name,
        driver_major=args.driver_major,
    )

    warnings: list[str] = []
    if cuda_index is None:
        warnings.append('CUDA driver is too old for the requested wheel family.')
    if platform_name == 'win32':
        warnings.append('Windows may need a pinned QGIS version and the triton-windows shim.')
    if platform_name == 'darwin':
        warnings.append('macOS may use MPS at runtime; sam3 is treated as optional on this platform.')

    return {
        'platform': platform_name,
        'python_version': args.python_version,
        'cache_dir': args.cache_dir,
        'cuda_index': cuda_index,
        'cuda_message': cuda_message,
        'cuda_reason': None if cuda_index is not None else 'Use Pixi or CPU mode for this environment.',
        'packages': packages,
        'warnings': warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Static dependency probe for the GeoAI QGIS plugin.'
    )
    parser.add_argument('--platform', default='auto', choices=['auto', 'win32', 'darwin', 'linux'])
    parser.add_argument('--python-version', default=_default_python_version())
    parser.add_argument('--cache-dir', default=_default_cache_dir())
    parser.add_argument('--compute-capability', type=float, default=None)
    parser.add_argument('--gpu-name', default=None)
    parser.add_argument('--driver-major', type=int, default=None)
    parser.add_argument('--check-installed', action='store_true', help='Check installed package metadata in the current interpreter.')
    parser.add_argument('--probe-imports', action='store_true', help='Attempt import probes for the package modules.')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    args = parser.parse_args(argv)

    report = build_report(args)
    if args.format == 'json':
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report), end='')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
