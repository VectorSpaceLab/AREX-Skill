#!/usr/bin/env python3
"""Build and convert a minimal coremltools MIL program.

The parent process avoids importing coremltools by default. Conversion runs in a
child process so native import/conversion crashes are reported cleanly.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import signal
import subprocess
import sys
import textwrap
import traceback
from typing import Iterable, Optional


NATIVE_ERROR_TOKENS = (
    "BlobWriter",
    "BlobReader",
    "libmilstoragepython",
    "libcoremlpython",
    "libmodelpackage",
    "coremlpython",
    "milstorage",
    "native",
    "segmentation fault",
    "SIGSEGV",
)


def _default_output(convert_to: str) -> pathlib.Path:
    suffix = ".mlpackage" if convert_to == "mlprogram" else ".mlmodel"
    return pathlib.Path(f"mil_smoke{suffix}")


def _normalize_output(path_text: Optional[str], convert_to: str) -> pathlib.Path:
    if path_text is None:
        return _default_output(convert_to)

    path = pathlib.Path(path_text)
    if path.suffix:
        return path

    suffix = ".mlpackage" if convert_to == "mlprogram" else ".mlmodel"
    return path.with_suffix(suffix)


def _looks_like_native_issue(text: str) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in NATIVE_ERROR_TOKENS)


def _native_hint(convert_to: str) -> str:
    backend = "ML Program" if convert_to == "mlprogram" else "neural network"
    if convert_to == "mlprogram":
        first_check = "Retry with --convert-to neuralnetwork to separate MIL construction from ML Program packaging."
    else:
        first_check = "Check whether a plain coremltools import succeeds with this Python/platform combination."

    return textwrap.dedent(
        f"""
        Native/runtime diagnostic:
          The failure looks related to coremltools native components while using the {backend} backend.
          For ML Programs this often appears as a missing BlobWriter/libmilstorage component,
          an incompatible coremltools wheel for the current Python/platform, or an unavailable
          Core ML runtime for save/prediction/debug output retrieval.

        Suggested next checks:
          1. {first_check}
          2. Use a coremltools build compatible with this Python version and platform.
          3. Run prediction/intermediate-output debugging only on a compatible macOS or configured remote runtime.
        """
    ).strip()


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a tiny MIL Builder program, convert it to Core ML, and save the result.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              python mil_smoke.py --convert-to neuralnetwork --output mil_smoke.mlmodel
              python mil_smoke.py --convert-to mlprogram --compute-precision float32 --output mil_smoke.mlpackage
              python mil_smoke.py --convert-to mlprogram --pass-pipeline empty --print-program
            """
        ),
    )
    parser.add_argument(
        "--convert-to",
        choices=("mlprogram", "neuralnetwork"),
        default="mlprogram",
        help="Core ML backend to exercise.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output model path. If omitted, uses mil_smoke.mlpackage or mil_smoke.mlmodel.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Remove an existing output file/package before saving.",
    )
    parser.add_argument(
        "--input-dtype",
        choices=("fp32", "fp16"),
        default="fp32",
        help="MIL input dtype for the smoke program.",
    )
    parser.add_argument(
        "--compute-precision",
        choices=("default", "float16", "float32"),
        default="default",
        help="ML Program compute precision. Ignored for neuralnetwork.",
    )
    parser.add_argument(
        "--pass-pipeline",
        choices=("default", "empty", "cleanup"),
        default="default",
        help="Pass pipeline override for pass-related triage.",
    )
    parser.add_argument(
        "--minimum-deployment-target",
        choices=("iOS15", "iOS16", "iOS17", "iOS18"),
        default=None,
        help="Optional minimum deployment target.",
    )
    parser.add_argument(
        "--print-program",
        action="store_true",
        help="Print the constructed MIL program before conversion.",
    )
    parser.add_argument(
        "--predict",
        action="store_true",
        help="Try a prediction after saving. This usually requires macOS/Core ML runtime support.",
    )
    parser.add_argument(
        "--in-process",
        action="store_true",
        help="Import coremltools and run conversion in this process instead of the default child process.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print Python tracebacks for caught exceptions.",
    )
    parser.add_argument(
        "--_worker",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def _remove_existing(path: pathlib.Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _prepare_output(path: pathlib.Path, overwrite: bool) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(
                f"Output already exists: {path}. Use --overwrite or choose another --output."
            )
        _remove_existing(path)
    path.parent.mkdir(parents=True, exist_ok=True)


def _build_program(mb, mil_types, np, input_dtype: str):
    mil_dtype = mil_types.fp16 if input_dtype == "fp16" else mil_types.fp32
    np_dtype = np.float16 if input_dtype == "fp16" else np.float32

    @mb.program(input_specs=[mb.TensorSpec(shape=(1, 4), dtype=mil_dtype)])
    def prog(x):
        scale = mb.const(val=np.array([1.0, 2.0, 3.0, 4.0], dtype=np_dtype), name="scale")
        shifted = mb.add(x=x, y=scale, name="shifted")
        activated = mb.relu(x=shifted, name="relu")
        mean = mb.reduce_mean(x=activated, axes=[1], keep_dims=False, name="mean")
        return mean

    return prog, np_dtype


def _worker(args: argparse.Namespace) -> int:
    output = _normalize_output(args.output, args.convert_to)
    stage = "importing coremltools"

    try:
        import numpy as np
        import coremltools as ct
        from coremltools.converters.mil import Builder as mb
        from coremltools.converters.mil.mil import types as mil_types

        stage = "building MIL program"
        prog, np_dtype = _build_program(mb, mil_types, np, args.input_dtype)
        if args.print_program:
            print("=== MIL program ===")
            print(prog)

        convert_kwargs = {"convert_to": args.convert_to}

        if args.pass_pipeline == "empty":
            convert_kwargs["pass_pipeline"] = ct.PassPipeline.EMPTY
        elif args.pass_pipeline == "cleanup":
            convert_kwargs["pass_pipeline"] = ct.PassPipeline.CLEANUP

        if args.minimum_deployment_target is not None:
            convert_kwargs["minimum_deployment_target"] = getattr(
                ct.target, args.minimum_deployment_target
            )

        if args.convert_to == "mlprogram" and args.compute_precision != "default":
            if args.compute_precision == "float32":
                convert_kwargs["compute_precision"] = ct.precision.FLOAT32
            elif args.compute_precision == "float16":
                convert_kwargs["compute_precision"] = ct.precision.FLOAT16

        print(f"coremltools version: {getattr(ct, '__version__', 'unknown')}")
        print(f"Converting MIL program with arguments: {convert_kwargs}")

        stage = "converting MIL program"
        mlmodel = ct.convert(prog, **convert_kwargs)
        spec = mlmodel.get_spec()
        print(
            "Converted spec:",
            f"type={spec.WhichOneof('Type')}",
            f"specificationVersion={spec.specificationVersion}",
        )

        stage = "preparing output path"
        _prepare_output(output, args.overwrite)

        stage = "saving model"
        mlmodel.save(str(output))
        print(f"Saved model: {output}")

        if args.predict:
            stage = "running prediction"
            x = np.arange(4, dtype=np_dtype).reshape(1, 4)
            try:
                prediction = mlmodel.predict({"x": x})
                print("Prediction succeeded. Outputs:")
                for name, value in prediction.items():
                    print(f"  {name}: shape={getattr(value, 'shape', None)} dtype={getattr(value, 'dtype', None)}")
            except Exception as exc:  # noqa: BLE001 - report runtime failures clearly.
                print(
                    "Prediction failed. Conversion/save may still be valid; prediction usually requires "
                    "a compatible Core ML runtime such as macOS.",
                    file=sys.stderr,
                )
                print(f"Prediction error: {type(exc).__name__}: {exc}", file=sys.stderr)
                if args.verbose:
                    traceback.print_exc()
                return 5

        return 0

    except Exception as exc:  # noqa: BLE001 - smoke tool should classify broad failures.
        message = f"ERROR during {stage}: {type(exc).__name__}: {exc}"
        print(message, file=sys.stderr)
        if _looks_like_native_issue(message):
            print(_native_hint(args.convert_to), file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2


def _run_child(argv: Iterable[str], convert_to: str) -> int:
    child_argv = [arg for arg in argv if arg != "--in-process"] + ["--_worker"]
    cmd = [sys.executable, str(pathlib.Path(__file__).resolve()), *child_argv]
    completed = subprocess.run(cmd, text=True, capture_output=True)

    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)

    if completed.returncode < 0:
        signum = -completed.returncode
        signame = signal.Signals(signum).name if signum in {s.value for s in signal.Signals} else f"SIG{signum}"
        print(
            f"ERROR: child conversion process terminated by {signame}. "
            "This usually indicates a native dependency/runtime crash rather than a MIL syntax error.",
            file=sys.stderr,
        )
        print(_native_hint(convert_to), file=sys.stderr)
        return 128 + signum

    combined = f"{completed.stdout}\n{completed.stderr}"
    if completed.returncode != 0 and _looks_like_native_issue(combined):
        print(_native_hint(convert_to), file=sys.stderr)

    return completed.returncode


def main(argv: Optional[Iterable[str]] = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = _parse_args(raw_argv)

    if args._worker or args.in_process:
        return _worker(args)

    return _run_child(raw_argv, args.convert_to)


if __name__ == "__main__":
    raise SystemExit(main())
