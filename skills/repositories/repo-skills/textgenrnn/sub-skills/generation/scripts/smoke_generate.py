#!/usr/bin/env python3
"""Short, safe textgenrnn generation smoke helper.

The script imports textgenrnn, loads default or user-provided model files,
generates a small number of samples, and optionally writes them to a UTF-8 file.
It performs no training and is safe to run from arbitrary current directories.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional


COMPAT_HINT = (
    "Compatibility hint: textgenrnn==2.0.0 needs a pre-Keras-3 TensorFlow "
    "stack such as TensorFlow/Keras 2.15.x and an environment where "
    "pkg_resources is available. For custom scratch-trained models, provide "
    "matching weights, vocab, and config files."
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


def existing_path(path_text: Optional[str], label: str) -> Optional[str]:
    if path_text is None:
        return None
    path = Path(path_text).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test textgenrnn generation with default or custom model files."
    )
    parser.add_argument("--weights-path", help="Optional HDF5 weights file.")
    parser.add_argument("--vocab-path", help="Optional vocabulary JSON file.")
    parser.add_argument("--config-path", help="Optional config JSON file.")
    parser.add_argument("--name", default="textgenrnn", help="Model name metadata.")
    parser.add_argument("--n", type=positive_int, default=1, help="Number of samples.")
    parser.add_argument("--prefix", default=None, help="Optional generation prefix.")
    parser.add_argument(
        "--temperature",
        type=parse_temperature,
        default=parse_temperature("0.5"),
        help="Sampling temperature as a float or comma-list, e.g. 0.2,1.0.",
    )
    parser.add_argument(
        "--max-gen-length",
        type=positive_int,
        default=80,
        help="Maximum generated token length for each sample.",
    )
    parser.add_argument(
        "--output-file",
        help="Optional destination file. Parent directories are created if needed.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress generated sample printing; still reports errors.",
    )
    return parser


def print_lines(lines: Iterable[str]) -> None:
    for line in lines:
        print(line)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.quiet:
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

    try:
        weights_path = existing_path(args.weights_path, "--weights-path")
        vocab_path = existing_path(args.vocab_path, "--vocab-path")
        config_path = existing_path(args.config_path, "--config-path")
    except Exception as exc:  # path validation should be concise for agents
        print(f"ERROR: {exc}", file=sys.stderr)
        print(COMPAT_HINT, file=sys.stderr)
        return 2

    try:
        import numpy as np
        import tensorflow as tf
        from textgenrnn import textgenrnn
    except Exception as exc:
        print(f"ERROR: could not import textgenrnn runtime: {exc}", file=sys.stderr)
        print(COMPAT_HINT, file=sys.stderr)
        return 2

    # Make the helper deterministic by default even though textgenrnn sampling is
    # stochastic in normal library use.
    np.random.seed(42)
    try:
        tf.random.set_seed(42)
    except Exception:
        pass

    init_kwargs = {
        "weights_path": weights_path,
        "vocab_path": vocab_path,
        "config_path": config_path,
        "name": args.name,
    }

    try:
        if args.quiet:
            with contextlib.redirect_stdout(io.StringIO()):
                textgen = textgenrnn(**init_kwargs)
                texts = textgen.generate(
                    n=args.n,
                    return_as_list=True,
                    prefix=args.prefix,
                    temperature=args.temperature,
                    max_gen_length=args.max_gen_length,
                    progress=False,
                )
        else:
            textgen = textgenrnn(**init_kwargs)
            texts = textgen.generate(
                n=args.n,
                return_as_list=True,
                prefix=args.prefix,
                temperature=args.temperature,
                max_gen_length=args.max_gen_length,
                progress=False,
            )
    except Exception as exc:
        print(f"ERROR: model load or generation failed: {exc}", file=sys.stderr)
        print(COMPAT_HINT, file=sys.stderr)
        print(
            "Check that custom weights/vocab/config files are a matching triplet "
            "and that --max-gen-length is positive.",
            file=sys.stderr,
        )
        return 1

    if args.output_file:
        try:
            output_path = Path(args.output_file).expanduser()
            if output_path.parent != Path(""):
                output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("\n".join(texts) + "\n", encoding="utf-8")
        except Exception as exc:
            print(f"ERROR: could not write --output-file: {exc}", file=sys.stderr)
            return 1

    if not args.quiet:
        print_lines(f"[{idx}] {text}" for idx, text in enumerate(texts, 1))
        if args.output_file:
            print(f"Wrote {len(texts)} sample(s) to {Path(args.output_file).expanduser()}")
    elif not args.output_file:
        print(
            f"Generated {len(texts)} sample(s); rerun without --quiet to print them.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
