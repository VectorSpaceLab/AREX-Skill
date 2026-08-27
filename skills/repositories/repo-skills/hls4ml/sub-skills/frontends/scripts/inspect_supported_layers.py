#!/usr/bin/env python3
"""Inspect the active hls4ml frontend registries and optional dependencies.

The script only imports a fixed list of known packages and never downloads data
or writes files. It is safe to run in read-only environments.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json

import hls4ml


OPTIONAL_MODULES = [
    'keras',
    'tensorflow',
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


def import_status(name: str) -> dict[str, str]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - inspection helper
        return {'status': 'missing', 'detail': exc.__class__.__name__}
    version = getattr(module, '__version__', None)
    return {'status': 'installed', 'version': str(version) if version is not None else 'unknown'}


def safe_sig(obj):
    try:
        return str(inspect.signature(obj))
    except Exception:
        return 'unavailable'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full', action='store_true', help='print full layer registries instead of just counts')
    args = parser.parse_args()

    from hls4ml import converters, utils
    from hls4ml.contrib.snntorch import SNNReadout

    data = {
        'hls4ml_version': hls4ml.__version__,
        'backends': sorted(hls4ml.backends.get_available_backends()),
        'layer_counts': {
            'keras': len(converters.get_supported_keras_layers()),
            'pytorch': len(converters.get_supported_pytorch_layers()),
            'onnx': len(converters.get_supported_onnx_layers()),
        },
        'live_signatures': {
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

    if args.full:
        data['supported_layers'] = {
            'keras': sorted(converters.get_supported_keras_layers()),
            'pytorch': sorted(converters.get_supported_pytorch_layers()),
            'onnx': sorted(converters.get_supported_onnx_layers()),
        }

    print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
