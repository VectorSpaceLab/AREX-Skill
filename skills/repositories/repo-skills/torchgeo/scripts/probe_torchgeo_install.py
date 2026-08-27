#!/usr/bin/env python3
"""Probe an installed TorchGeo environment without downloading data."""

from __future__ import annotations

import importlib
import importlib.metadata
import json
import sys

MODULES = [
    'torch',
    'torchvision',
    'torchgeo',
    'rasterio',
    'geopandas',
    'pyproj',
    'shapely',
    'lightning',
    'kornia',
    'timm',
    'segmentation_models_pytorch',
]


def probe_module(name: str) -> dict[str, str | bool]:
    """Return import status and version metadata for one module."""
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report all import failures
        return {'module': name, 'ok': False, 'error': f'{type(exc).__name__}: {exc}'}

    version = getattr(module, '__version__', None)
    if version is None:
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            version = 'unknown'
    return {'module': name, 'ok': True, 'version': str(version)}


def main() -> int:
    """Print a JSON probe report and return nonzero on missing core imports."""
    report = {'python': sys.version, 'modules': [probe_module(name) for name in MODULES]}

    try:
        from torchgeo.models import list_models

        report['torchgeo_models'] = list_models()
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report all failures
        report['torchgeo_models_error'] = f'{type(exc).__name__}: {exc}'

    print(json.dumps(report, indent=2, sort_keys=True))
    core = {'torch', 'torchvision', 'torchgeo', 'rasterio', 'geopandas', 'pyproj', 'shapely'}
    failed = [m['module'] for m in report['modules'] if m['module'] in core and not m['ok']]
    if failed:
        print(f'FAILED core imports: {failed}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
