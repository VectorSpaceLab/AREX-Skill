#!/usr/bin/env python3
"""Build safe Pyserini fusion commands without executing them."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


METHODS = ("rrf", "interpolation", "average", "normalize")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def probability(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a float, got {value!r}") from exc
    if parsed < 0.0 or parsed > 1.0:
        raise argparse.ArgumentTypeError("expected a value between 0 and 1")
    return parsed


def existing_file(value: str) -> str:
    path = Path(value)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"run file does not exist: {value}")
    return value


def build_command(args: argparse.Namespace) -> list[str]:
    command = [
        "python",
        "-m",
        "pyserini.fusion",
        "--method",
        args.method,
        "--runs",
        *args.runs,
        "--output",
        args.output,
        "--runtag",
        args.runtag,
        "--k",
        str(args.k),
        "--depth",
        str(args.depth),
    ]
    if args.method == "rrf":
        command.extend(["--rrf.k", str(args.rrf_k)])
    if args.method == "interpolation":
        command.extend(["--alpha", str(args.alpha)])
    if args.resort:
        command.append("--resort")
    return command


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Pyserini fusion command after checking method-specific arguments.")
    parser.add_argument("--method", choices=METHODS, default="rrf", help="Fusion method to use.")
    parser.add_argument("--runs", nargs="+", type=existing_file, required=True, help="Input six-column TREC run files.")
    parser.add_argument("--output", required=True, help="Output path for the fused run.")
    parser.add_argument("--runtag", default="pyserini.fusion", help="Run tag to write in the fused output.")
    parser.add_argument("--k", type=positive_int, default=1000, help="Maximum output documents per topic.")
    parser.add_argument("--depth", type=positive_int, default=1000, help="Maximum input depth per topic per run.")
    parser.add_argument("--rrf-k", type=positive_int, default=60, help="RRF rank damping constant; distinct from output --k.")
    parser.add_argument("--alpha", type=probability, default=0.5, help="Interpolation weight for the first run; the second receives 1-alpha.")
    parser.add_argument("--resort", action="store_true", help="Ask Pyserini to sort each input run by score before fusion.")
    parser.add_argument("--shell", action="store_true", help="Print as a shell-escaped one-line command.")
    args = parser.parse_args(argv)

    if len(args.runs) < 2:
        parser.error("fusion requires at least two input runs")
    if args.method == "interpolation" and len(args.runs) != 2:
        parser.error("interpolation requires exactly two input runs")

    command = build_command(args)
    if args.shell:
        print(shlex.join(command))
    else:
        print(" ".join(shlex.quote(part) for part in command))

    print("\n# Recommended next checks:")
    for run in args.runs:
        print(f"#   python scripts/validate_trec_run.py {shlex.quote(run)} --summary")
    print(f"#   python scripts/validate_trec_run.py {shlex.quote(args.output)} --summary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
