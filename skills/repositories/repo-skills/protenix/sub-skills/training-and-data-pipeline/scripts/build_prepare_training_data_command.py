#!/usr/bin/env python3
"""Build a safe no-run Protenix training-data preprocessing command."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a no-run Protenix training-data preprocessing command.")
    parser.add_argument("--input", required=True, help="Input CIF directory or text file listing CIF paths.")
    parser.add_argument("--output-csv", required=True, help="Output index CSV path.")
    parser.add_argument("--bioassembly-dir", required=True, help="Output directory for preprocessed .pkl.gz bioassembly files.")
    parser.add_argument("--cluster-txt", help="Optional protein clustering file.")
    parser.add_argument("--num-cpu", type=int, default=8, help="CPU workers to request.")
    parser.add_argument("--disable-filters", action="store_true", help="Add -d for model-generated CIFs where WeightedPDB filters should be disabled.")
    parser.add_argument("--check-inputs", action="store_true", help="Warn if provided input paths do not exist.")
    parser.add_argument("--print-warnings", action="store_true", help="Print planning warnings after the command.")
    args = parser.parse_args()

    command = [
        "python",
        "-m",
        "scripts.prepare_training_data",
        "-i",
        args.input,
        "-o",
        args.output_csv,
        "-b",
        args.bioassembly_dir,
        "-n",
        str(args.num_cpu),
    ]
    if args.cluster_txt:
        command.extend(["-c", args.cluster_txt])
    if args.disable_filters:
        command.append("-d")

    warnings = [
        "This helper only prints a command; it does not preprocess CIF files.",
        "Preprocessing can consume substantial CPU, memory, and disk, especially for large mmCIF collections.",
    ]
    if not args.cluster_txt:
        warnings.append("No cluster file was provided; confirm whether chain/interface cluster IDs are required for your training plan.")
    if args.disable_filters:
        warnings.append("-d disables the full WeightedPDB filters and is intended for model-generated CIFs or custom cases where those filters are undesired.")
    else:
        warnings.append("Without -d, the script applies the documented WeightedPDB-style filtering rules for RCSB-style CIF inputs.")
    if args.check_inputs:
        for label, value in [("input", args.input), ("cluster file", args.cluster_txt)]:
            if value and not Path(value).exists():
                warnings.append(f"{label} path does not exist: {value}")

    print(shell_join(command))
    if args.print_warnings:
        for warning in warnings:
            print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
