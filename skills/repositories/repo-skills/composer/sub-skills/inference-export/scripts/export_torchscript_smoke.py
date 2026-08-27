#!/usr/bin/env python3
"""Safe TorchScript export smoke test for Composer inference export.

This script uses only synthetic data, writes to a temporary file by default,
and checks that the exported TorchScript artifact can be loaded back and run.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import torch
import torch.nn as nn

from composer.utils import export_for_inference


class TinyExportModel(nn.Module):
    """Small deterministic model used for a local export round-trip."""

    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, 3),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def run_smoke(output_path: Path) -> None:
    torch.manual_seed(7)
    model = TinyExportModel().eval()
    sample_input = torch.randn(2, 4)
    reference_output = model(sample_input)

    export_for_inference(
        model=model,
        save_format='torchscript',
        save_path=str(output_path),
    )

    if not output_path.exists():
        raise FileNotFoundError(f'expected exported file at {output_path}')

    exported = torch.jit.load(str(output_path))
    exported.eval()
    roundtrip_output = exported(sample_input)

    torch.testing.assert_close(reference_output, roundtrip_output, rtol=1e-5, atol=1e-6)
    print(f'TorchScript export smoke passed: {output_path}')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Export a tiny synthetic model to TorchScript and load it back.',
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Optional output path. Defaults to a temporary file that is removed automatically.',
    )
    args = parser.parse_args()

    if args.output is None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_smoke(Path(tmpdir) / 'tiny-export.pt')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        run_smoke(args.output)


if __name__ == '__main__':
    main()
