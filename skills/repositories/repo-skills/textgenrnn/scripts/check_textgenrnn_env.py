#!/usr/bin/env python3
"""Check a textgenrnn runtime and optionally run a short generation smoke.

This helper is safe by default: it imports packages and reports versions. Use
--generate when you also want to instantiate a model and generate a short sample.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import platform
import sys
from pathlib import Path
from typing import List, Optional


COMPAT_HINT = (
    "Use a pre-Keras-3 TensorFlow stack such as TensorFlow/Keras 2.15.x and "
    "ensure pkg_resources is available, for example through setuptools<81."
)


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected integer, got {value!r}") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def parse_temperature(value: str) -> List[float]:
    parts = [part.strip() for part in value.split(",")]
    if not parts or any(part == "" for part in parts):
        raise argparse.ArgumentTypeError("temperature must be a float or comma-list")
    try:
        return [float(part) for part in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"temperature must contain only floats, got {value!r}"
        ) from exc


def optional_existing_path(path_text: Optional[str], label: str) -> Optional[str]:
    if path_text is None:
        return None
    path = Path(path_text).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check textgenrnn imports, TensorFlow compatibility, and optional generation."
    )
    parser.add_argument("--generate", action="store_true", help="Instantiate a model and generate a short sample.")
    parser.add_argument("--weights-path", help="Optional HDF5 weights file for --generate.")
    parser.add_argument("--vocab-path", help="Optional vocabulary JSON file for --generate.")
    parser.add_argument("--config-path", help="Optional config JSON file for --generate.")
    parser.add_argument("--name", default="textgenrnn", help="Model name metadata for --generate.")
    parser.add_argument("--n", type=positive_int, default=1, help="Number of samples for --generate.")
    parser.add_argument("--prefix", default=None, help="Optional generation prefix for --generate.")
    parser.add_argument(
        "--temperature",
        type=parse_temperature,
        default=parse_temperature("0.5"),
        help="Sampling temperature or comma-list for --generate.",
    )
    parser.add_argument(
        "--max-gen-length",
        type=positive_int,
        default=40,
        help="Maximum generated token length for --generate.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress generated sample text.")
    return parser


def print_header(title: str) -> None:
    print(f"\n== {title} ==")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    print_header("Python")
    print(f"executable: {sys.executable}")
    print(f"version: {sys.version.split()[0]}")
    print(f"platform: {platform.platform()}")

    print_header("pkg_resources")
    try:
        import pkg_resources  # type: ignore

        print("available: true")
        print(f"module: {getattr(pkg_resources, '__file__', 'unknown')}")
    except Exception as exc:
        print("available: false")
        print(f"error: {exc}")
        print(f"hint: {COMPAT_HINT}")

    print_header("TensorFlow")
    tf = None
    try:
        import tensorflow as tf_import  # type: ignore

        tf = tf_import
        print(f"version: {tf.__version__}")
        try:
            import tensorflow.compat.v1.keras.backend as compat_backend  # type: ignore

            print(f"compat_v1_keras_backend: true")
            print(f"has_set_session: {hasattr(compat_backend, 'set_session')}")
        except Exception as exc:
            print("compat_v1_keras_backend: false")
            print(f"error: {exc}")
            print(f"hint: {COMPAT_HINT}")
        try:
            gpus = tf.config.list_physical_devices("GPU")
            print(f"gpu_devices: {len(gpus)}")
            for gpu in gpus:
                print(f"- {gpu}")
        except Exception as exc:
            print(f"gpu_query_error: {exc}")
    except Exception as exc:
        print(f"error: could not import tensorflow: {exc}")
        print(f"hint: {COMPAT_HINT}")

    print_header("textgenrnn")
    try:
        from importlib.metadata import version

        try:
            print(f"distribution_version: {version('textgenrnn')}")
        except Exception as exc:
            print(f"distribution_version_error: {exc}")
        from textgenrnn import textgenrnn

        print("import: ok")
    except Exception as exc:
        print(f"import: failed: {exc}")
        print(f"hint: {COMPAT_HINT}")
        return 2

    if not args.generate:
        print("\nGeneration smoke skipped. Add --generate to instantiate a model.")
        return 0

    print_header("Generation smoke")
    try:
        weights_path = optional_existing_path(args.weights_path, "--weights-path")
        vocab_path = optional_existing_path(args.vocab_path, "--vocab-path")
        config_path = optional_existing_path(args.config_path, "--config-path")
    except Exception as exc:
        print(f"model_file_error: {exc}")
        return 2

    if tf is not None:
        try:
            tf.random.set_seed(42)
        except Exception:
            pass
    try:
        import numpy as np

        np.random.seed(42)
    except Exception:
        pass

    try:
        kwargs = {
            "weights_path": weights_path,
            "vocab_path": vocab_path,
            "config_path": config_path,
            "name": args.name,
        }
        if args.quiet:
            with contextlib.redirect_stdout(io.StringIO()):
                model = textgenrnn(**kwargs)
                samples = model.generate(
                    n=args.n,
                    return_as_list=True,
                    prefix=args.prefix,
                    temperature=args.temperature,
                    max_gen_length=args.max_gen_length,
                    progress=False,
                )
        else:
            model = textgenrnn(**kwargs)
            samples = model.generate(
                n=args.n,
                return_as_list=True,
                prefix=args.prefix,
                temperature=args.temperature,
                max_gen_length=args.max_gen_length,
                progress=False,
            )
        print(f"generated_count: {len(samples)}")
        if not args.quiet:
            for idx, sample in enumerate(samples, 1):
                print(f"[{idx}] {sample}")
    except Exception as exc:
        print(f"generation: failed: {exc}")
        print(f"hint: {COMPAT_HINT}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
