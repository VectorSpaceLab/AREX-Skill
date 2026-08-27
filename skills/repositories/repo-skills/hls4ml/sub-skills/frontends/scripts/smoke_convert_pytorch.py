#!/usr/bin/env python3
"""Build, convert, compile, and predict through a tiny PyTorch model.

The script is intentionally safe by default:
- it uses a temporary output directory unless you pass `--output-dir`
- it does not synthesize hardware
- it does not download anything
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import numpy as np
import torch
import hls4ml


class TinyLinear(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = torch.nn.Linear(2, 1, bias=False)
        with torch.no_grad():
            self.fc.weight[:] = torch.tensor([[0.5, 0.5]])

    def forward(self, x):
        return self.fc(x)


def make_workdir(path: str | None, overwrite: bool):
    if path is None:
        return tempfile.TemporaryDirectory(prefix='hls4ml_frontend_torch_'), None

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

    model = TinyLinear().eval()
    config = hls4ml.utils.config_from_pytorch_model(
        model,
        input_shape=(2,),
        granularity='name',
        backend=args.backend,
        channels_last_conversion='full',
        transpose_outputs=False,
    )

    tmp = None
    output_dir = args.output_dir
    if output_dir is None:
        tmp, out_path = make_workdir(None, False)
        output_dir = str(Path(tmp.name) / 'pytorch_smoke')
    else:
        _, out_path = make_workdir(output_dir, args.overwrite)
        output_dir = str(out_path)

    x = np.asarray([[1.0, 1.0]], dtype=np.float32)
    expected = np.asarray([[1.0]], dtype=np.float32)

    try:
        hls_model = hls4ml.converters.convert_from_pytorch_model(
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
