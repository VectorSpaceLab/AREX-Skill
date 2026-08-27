#!/usr/bin/env python3
"""Quick hls4ml installation and optional dependency check.

This helper is safe and read-only. It reports the installed hls4ml version,
backend registry, and the presence of common optional frontend packages.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from typing import Any

OPTIONAL_MODULES = [
    'tensorflow',
    'keras',
    'torch',
    'onnx',
    'qonnx',
    'qkeras',
    'HGQ',
    'hgq2',
    'da4ml',
    'snntorch',
    'brevitas',
    'pquant',
    'sparsepixels',
]


def safe_sig(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception:
        return 'unavailable'


def import_status(name: str) -> dict[str, str]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - read-only probe
        return {'status': 'missing', 'detail': exc.__class__.__name__}
    version = getattr(module, '__version__', None)
    return {'status': 'installed', 'version': str(version) if version is not None else 'unknown'}


def build_report() -> dict[str, Any]:
    import hls4ml
    from hls4ml import converters, utils
    from hls4ml.contrib.snntorch import SNNReadout

    return {
        'hls4ml_version': hls4ml.__version__,
        'backends': sorted(hls4ml.backends.get_available_backends()),
        'layer_counts': {
            'keras': len(converters.get_supported_keras_layers()),
            'pytorch': len(converters.get_supported_pytorch_layers()),
            'onnx': len(converters.get_supported_onnx_layers()),
        },
        'signatures': {
            'config_from_keras_model': safe_sig(utils.config_from_keras_model),
            'config_from_pytorch_model': safe_sig(utils.config_from_pytorch_model),
            'config_from_onnx_model': safe_sig(utils.config_from_onnx_model),
            'convert_from_keras_model': safe_sig(converters.convert_from_keras_model),
            'convert_from_pytorch_model': safe_sig(converters.convert_from_pytorch_model),
            'convert_from_onnx_model': safe_sig(converters.convert_from_onnx_model),
            'convert_from_config': safe_sig(converters.convert_from_config),
            'fetch_example_model': safe_sig(utils.fetch_example_model),
            'fetch_example_list': safe_sig(utils.fetch_example_list),
            'plot_model': safe_sig(utils.plot_model),
            'SNNReadout': safe_sig(SNNReadout),
        },
        'optional_modules': {name: import_status(name) for name in OPTIONAL_MODULES},
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"hls4ml version: {report['hls4ml_version']}")
    print('backends: ' + ', '.join(report['backends']))
    print('layer counts: ' + ', '.join(f"{k}={v}" for k, v in report['layer_counts'].items()))
    print('optional modules:')
    for name, status in report['optional_modules'].items():
        if status['status'] == 'installed':
            print(f"  - {name}: installed ({status['version']})")
        else:
            print(f"  - {name}: missing ({status['detail']})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='emit JSON instead of text')
    parser.add_argument('--strict', action='store_true', help='exit non-zero if hls4ml cannot be imported')
    args = parser.parse_args()

    try:
        report = build_report()
    except Exception as exc:  # pragma: no cover - import failure should be explicit
        print(f'Unable to import hls4ml: {exc}', file=sys.stderr)
        return 2 if args.strict else 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
