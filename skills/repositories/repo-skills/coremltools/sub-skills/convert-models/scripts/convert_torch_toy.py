#!/usr/bin/env python3
"""Convert a tiny PyTorch module to a Core ML ML Program package.

This script is intentionally small and safe: it imports optional dependencies
lazily, traces a deterministic torch.nn.Module, converts with an explicit
TensorType name/shape, and saves only to the user-provided .mlpackage path.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def _import_dependencies():
    try:
        import torch  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user's environment
        print(
            "Missing or unusable PyTorch. Install a coremltools-compatible torch "
            "package before running this converter smoke script.\n"
            f"Import error: {exc}",
            file=sys.stderr,
        )
        return None, None

    try:
        import coremltools as ct  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user's environment
        print(
            "Missing or unusable coremltools. Install coremltools in the same "
            "environment as PyTorch before running this script.\n"
            f"Import error: {exc}",
            file=sys.stderr,
        )
        return None, None

    return torch, ct


def _target_from_name(ct, name: str):
    try:
        return getattr(ct.target, name)
    except AttributeError as exc:
        choices = [n for n in dir(ct.target) if not n.startswith("_")]
        raise ValueError(
            f"Unknown deployment target {name!r}. Try one of: {', '.join(sorted(choices))}"
        ) from exc


def _prepare_output(path: Path, overwrite: bool) -> None:
    if path.suffix != ".mlpackage":
        raise ValueError("--output must end with .mlpackage for the default ML Program conversion")
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing output: {path}")
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Trace a tiny torch.nn.Module, convert it with coremltools using an "
            "explicit TensorType name/shape, and save a .mlpackage."
        )
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Destination Core ML package path. Must end with .mlpackage.",
    )
    parser.add_argument(
        "--input-name",
        default="input",
        help="Core ML input feature name to use in ct.TensorType. Default: input.",
    )
    parser.add_argument(
        "--batch-size",
        default=1,
        type=_positive_int,
        help="Batch dimension for the toy tensor. Default: 1.",
    )
    parser.add_argument(
        "--features",
        default=3,
        type=_positive_int,
        help="Feature dimension for the toy tensor. Default: 3.",
    )
    parser.add_argument(
        "--minimum-deployment-target",
        default="iOS15",
        help="coremltools target enum name, such as iOS15, iOS16, or macOS12. Default: iOS15.",
    )
    parser.add_argument(
        "--compute-precision",
        choices=("default", "float16", "float32"),
        default="float32",
        help="ML Program compute precision. Default: float32 for stable toy output.",
    )
    parser.add_argument(
        "--load-model",
        action="store_true",
        help=(
            "Allow coremltools to compile/load the model after conversion. By default "
            "the script uses skip_model_load=True for host safety."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the output package if it already exists.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    output = args.output.expanduser()

    try:
        _prepare_output(output, args.overwrite)
    except Exception as exc:
        print(f"Output path error: {exc}", file=sys.stderr)
        return 2

    torch, ct = _import_dependencies()
    if torch is None or ct is None:
        return 1

    class TinyModule(torch.nn.Module):
        def forward(self, x):
            return torch.relu(x * 2.0 + 1.0)

    try:
        torch.manual_seed(0)
        module = TinyModule().eval()
        example = torch.arange(
            args.batch_size * args.features,
            dtype=torch.float32,
        ).reshape(args.batch_size, args.features)
        traced = torch.jit.trace(module, example)

        target = _target_from_name(ct, args.minimum_deployment_target)
        precision = None
        if args.compute_precision == "float16":
            precision = ct.precision.FLOAT16
        elif args.compute_precision == "float32":
            precision = ct.precision.FLOAT32

        mlmodel = ct.convert(
            traced,
            source="pytorch",
            inputs=[ct.TensorType(name=args.input_name, shape=tuple(example.shape))],
            minimum_deployment_target=target,
            convert_to="mlprogram",
            compute_precision=precision,
            compute_units=ct.ComputeUnit.CPU_ONLY,
            skip_model_load=not args.load_model,
        )
        mlmodel.save(str(output))
    except Exception as exc:
        print(f"Conversion failed: {exc}", file=sys.stderr)
        return 1

    print(f"Saved Core ML package: {output}")
    print(f"Input feature: {args.input_name}, shape: ({args.batch_size}, {args.features})")
    if not args.load_model:
        print("Used skip_model_load=True; run prediction only on a supported Core ML runtime.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
