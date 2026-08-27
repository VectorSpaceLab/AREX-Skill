#!/usr/bin/env python3
"""Build a tiny MIL Core ML model and optionally apply Core ML weight compression.

The parent process intentionally does not import coremltools. Conversion and
optimization run in a child process so --help remains safe even when optional
framework dependencies in the current Python environment are broken.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


WORKER_CODE = r'''
from __future__ import annotations

import argparse
from pathlib import Path


def _build_tiny_mlprogram():
    import numpy as np
    import coremltools as ct
    from coremltools.converters.mil import Builder as mb

    @mb.program(input_specs=[mb.TensorSpec(shape=(1, 4))], opset_version=ct.target.iOS16)
    def prog(x):
        weight = np.array(
            [
                [0.25, -0.50, 0.75, 1.00],
                [1.25, 0.50, -0.75, 0.00],
                [-1.00, 1.50, 0.25, -0.25],
                [0.10, 0.20, 0.30, 0.40],
            ],
            dtype=np.float32,
        )
        bias = np.array([0.05, -0.05, 0.10, -0.10], dtype=np.float32)
        y = mb.linear(x=x, weight=weight, bias=bias, name="tiny_linear")
        return mb.relu(x=y, name="tiny_relu")

    return ct.convert(
        prog,
        convert_to="mlprogram",
        compute_precision=ct.precision.FLOAT32,
        skip_model_load=True,
    )


def _compress(mlmodel, compression: str):
    if compression == "none":
        return mlmodel, "conversion-only"

    import coremltools.optimize.coreml as cto

    if compression == "linear":
        config = cto.OptimizationConfig(
            global_config=cto.OpLinearQuantizerConfig(
                mode="linear_symmetric",
                dtype="int8",
                granularity="per_tensor",
                weight_threshold=0,
            )
        )
        return cto.linear_quantize_weights(mlmodel, config), "linear int8 weight quantization"

    if compression == "palettize":
        config = cto.OptimizationConfig(
            global_config=cto.OpPalettizerConfig(
                mode="uniform",
                nbits=2,
                granularity="per_tensor",
                weight_threshold=0,
            )
        )
        return cto.palettize_weights(mlmodel, config), "2-bit uniform weight palettization"

    if compression == "prune":
        config = cto.OptimizationConfig(
            global_config=cto.OpThresholdPrunerConfig(
                threshold=0.15,
                minimum_sparsity_percentile=0.0,
                weight_threshold=0,
            )
        )
        return cto.prune_weights(mlmodel, config), "threshold weight pruning"

    raise ValueError(f"Unsupported compression mode: {compression}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--compression", choices=["none", "linear", "palettize", "prune"], required=True)
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    mlmodel = _build_tiny_mlprogram()
    mlmodel, label = _compress(mlmodel, args.compression)
    mlmodel.save(str(output))

    spec = mlmodel.get_spec()
    spec_type = spec.WhichOneof("Type")
    print(f"created={output}")
    print(f"spec_type={spec_type}")
    print(f"compression={label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _remove_existing(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _describe_returncode(code: int) -> str:
    if code < 0:
        return f"terminated by signal {-code}"
    return f"exited with code {code}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a tiny MIL mlprogram and optionally apply safe "
            "coremltools.optimize.coreml weight compression."
        )
    )
    parser.add_argument(
        "--output",
        default="coremltools_optimize_smoke.mlpackage",
        help="Output .mlpackage path to create. Default: %(default)s",
    )
    parser.add_argument(
        "--compression",
        choices=["none", "linear", "palettize", "prune"],
        default="linear",
        help="Optional Core ML weight compression to apply. Default: %(default)s",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing output file or .mlpackage directory.",
    )
    args = parser.parse_args(argv)

    output = Path(args.output)
    if output.exists():
        if not args.force:
            print(
                f"Refusing to overwrite existing output: {output}\n"
                "Pass --force or choose a new --output path.",
                file=sys.stderr,
            )
            return 2
        _remove_existing(output)

    cmd = [
        sys.executable,
        "-c",
        WORKER_CODE,
        "--output",
        os.fspath(output),
        "--compression",
        args.compression,
    ]

    completed = subprocess.run(cmd, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)

    if completed.returncode != 0:
        if args.compression == "none":
            hint = (
                "Conversion-only smoke also failed; fix the coremltools "
                "import/conversion environment before debugging optimization."
            )
        else:
            hint = "Retry with --compression none to isolate conversion from optimization."
        print(
            "Smoke failed: child process "
            f"{_describe_returncode(completed.returncode)}. "
            "This usually indicates a coremltools import/conversion/optimization "
            f"environment problem rather than a large-model issue. {hint}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
