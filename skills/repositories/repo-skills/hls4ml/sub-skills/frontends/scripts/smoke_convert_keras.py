#!/usr/bin/env python3
"""Build, convert, compile, and predict through a tiny Keras model.

The script is intentionally safe by default:
- it uses a temporary output directory unless you pass `--output-dir`
- it does not synthesize hardware
- it does not download anything
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')

import numpy as np
import hls4ml
import keras


def build_model():
    model = keras.Sequential(
        [
            keras.layers.Input(shape=(2,), name='input_data'),
            keras.layers.Dense(2, activation='relu', use_bias=False, name='dense'),
        ]
    )
    model.build((None, 2))
    model.layers[-1].set_weights([np.eye(2, dtype=np.float32)])
    return model


def make_workdir(path: str | None, overwrite: bool):
    if path is None:
        return tempfile.TemporaryDirectory(prefix='hls4ml_frontend_keras_'), None

    out = Path(path)
    if out.exists() and any(out.iterdir()) and not overwrite:
        raise SystemExit(f'output directory is not empty: {out} (use --overwrite to replace it)')
    out.mkdir(parents=True, exist_ok=True)
    return None, out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', default='Vitis', help='hls4ml backend to use (default: Vitis)')
    parser.add_argument('--io-type', default='io_parallel', choices=['io_parallel', 'io_stream'])
    parser.add_argument('--output-dir', help='keep generated files in this directory instead of a temp directory')
    parser.add_argument('--overwrite', action='store_true', help='allow reusing a non-empty output directory')
    args = parser.parse_args()

    model = build_model()
    config = hls4ml.utils.config_from_keras_model(model, granularity='name', backend=args.backend)

    tmp = None
    output_dir = args.output_dir
    if output_dir is None:
        tmp, out_path = make_workdir(None, False)
        output_dir = str(Path(tmp.name) / 'keras_smoke')
    else:
        _, out_path = make_workdir(output_dir, args.overwrite)
        output_dir = str(out_path)

    x = np.asarray([[1.0, 2.0]], dtype=np.float32)
    expected = np.asarray([[1.0, 2.0]], dtype=np.float32)

    try:
        hls_model = hls4ml.converters.convert_from_keras_model(
            model,
            backend=args.backend,
            hls_config=config,
            output_dir=output_dir,
            io_type=args.io_type,
        )
        hls_model.compile()
        pred = np.asarray(hls_model.predict(x), dtype=np.float32).reshape(expected.shape)
        np.testing.assert_allclose(pred, expected, atol=1e-6, rtol=0)
        summary = {
            'status': 'ok',
            'backend': args.backend,
            'io_type': args.io_type,
            'output_dir': output_dir,
            'prediction': pred.tolist(),
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    finally:
        if tmp is not None:
            tmp.cleanup()


if __name__ == '__main__':
    raise SystemExit(main())
