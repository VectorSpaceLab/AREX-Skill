#!/usr/bin/env python3
"""No-download OmegaFold CLI smoke check and FASTA command planner."""

from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
from dataclasses import dataclass


DEFAULT_TIMEOUT_SECONDS = 15
EXPECTED_FLAGS = [
    "--num_cycle",
    "--subbatch_size",
    "--device",
    "--weights_file",
    "--weights",
    "--model",
    "--pseudo_msa_mask_rate",
    "--num_pseudo_msa",
    "--allow_tf32",
]


@dataclass(frozen=True)
class FastaRecord:
    header: str
    sequence: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate OmegaFold CLI availability without loading model weights "
            "or downloading checkpoints. Optionally inspect a FASTA and print "
            "the full inference command that would be run."
        )
    )
    parser.add_argument(
        "--fasta",
        type=pathlib.Path,
        help="Optional FASTA file to inspect for a dry-run command plan.",
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("omegafold_outputs"),
        help="Output directory to include in the planned command. Default: omegafold_outputs.",
    )
    parser.add_argument("--model", type=int, choices=(1, 2), default=1)
    parser.add_argument("--device", help="Optional planned device, such as cuda, cuda:0, mps, or cpu.")
    parser.add_argument("--weights-file", type=pathlib.Path, help="Optional local checkpoint path for the planned command.")
    parser.add_argument("--num-cycle", type=int, help="Optional planned --num_cycle value.")
    parser.add_argument("--subbatch-size", type=int, help="Optional planned --subbatch_size value.")
    parser.add_argument("--pseudo-msa-mask-rate", type=float, help="Optional planned --pseudo_msa_mask_rate value.")
    parser.add_argument("--num-pseudo-msa", type=int, help="Optional planned --num_pseudo_msa value.")
    parser.add_argument("--allow-tf32", choices=("True", "False"), help="Optional planned --allow_tf32 value.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Seconds to allow for `omegafold --help`. Default: {DEFAULT_TIMEOUT_SECONDS}.",
    )
    parser.add_argument(
        "--skip-help-check",
        action="store_true",
        help="Skip running `omegafold --help`; useful when only inspecting FASTA syntax.",
    )
    return parser.parse_args()


def shell_quote(value: object) -> str:
    try:
        text = os.fspath(value)
    except TypeError:
        text = str(value)
    if not text:
        return "''"
    safe = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_@%+=:,./-"
    if all(char in safe for char in text):
        return text
    return "'" + text.replace("'", "'\"'\"'") + "'"


def run_help_check(timeout: float) -> None:
    executable = shutil.which("omegafold")
    if executable is None:
        raise SystemExit(
            "ERROR: `omegafold` was not found on PATH. Activate the OmegaFold "
            "environment, reinstall the console script, or try `python -m omegafold --help`."
        )

    print(f"omegafold executable: {executable}")
    try:
        completed = subprocess.run(
            [executable, "--help"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"ERROR: `omegafold --help` timed out after {timeout} seconds.") from exc

    if completed.returncode != 0:
        print(completed.stdout.rstrip())
        raise SystemExit(f"ERROR: `omegafold --help` exited with status {completed.returncode}.")

    help_text = completed.stdout
    print("omegafold --help: OK")
    missing = [flag for flag in EXPECTED_FLAGS if flag not in help_text]
    if missing:
        print("warning: expected flags not found in help text: " + ", ".join(missing))
    else:
        print("recognized expected flags: " + ", ".join(EXPECTED_FLAGS))


def read_fasta(path: pathlib.Path) -> list[FastaRecord]:
    if not path.is_file():
        raise SystemExit(f"ERROR: FASTA file does not exist: {path}")

    records: list[FastaRecord] = []
    current_header: str | None = None
    current_parts: list[str] = []

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith((">", ":")):
            if current_header is not None:
                records.append(FastaRecord(current_header, "".join(current_parts).upper()))
            current_header = line[1:].strip()
            current_parts = []
            if not current_header:
                print(f"warning: empty FASTA header at line {line_number}")
        else:
            if current_header is None:
                raise SystemExit(f"ERROR: sequence data appears before the first FASTA header at line {line_number}.")
            current_parts.append(line)

    if current_header is not None:
        records.append(FastaRecord(current_header, "".join(current_parts).upper()))

    if not records:
        raise SystemExit(f"ERROR: no FASTA records found in {path}")
    empty = [record.header for record in records if not record.sequence]
    if empty:
        raise SystemExit("ERROR: FASTA records without sequence: " + ", ".join(empty))
    return records


def planned_pdb_name(header: str, index: int, output_dir: pathlib.Path) -> pathlib.Path:
    try:
        name_max = os.pathconf(os.fspath(output_dir), "PC_NAME_MAX") - 4
    except (AttributeError, OSError, ValueError):
        name_max = 32
    if len(header) < name_max:
        basename = header.replace(os.path.sep, "-")
    else:
        basename = f"{index}th chain"
    return output_dir / f"{basename}.pdb"


def print_fasta_plan(args: argparse.Namespace) -> None:
    records = read_fasta(args.fasta)
    sorted_records = sorted(records, key=lambda record: len(record.sequence))
    print(f"FASTA records: {len(records)}")
    for index, record in enumerate(sorted_records):
        output_path = planned_pdb_name(record.header, index, args.output_dir)
        print(
            f"  {index + 1}. header={record.header!r} length={len(record.sequence)} "
            f"planned_pdb={output_path}"
        )

    command: list[object] = ["omegafold", args.fasta, args.output_dir, "--model", args.model]
    if args.device:
        command.extend(["--device", args.device])
    if args.weights_file:
        command.extend(["--weights_file", args.weights_file])
        if not args.weights_file.is_file():
            print(f"warning: planned --weights_file does not exist: {args.weights_file}")
    if args.num_cycle is not None:
        command.extend(["--num_cycle", args.num_cycle])
    if args.subbatch_size is not None:
        command.extend(["--subbatch_size", args.subbatch_size])
    if args.pseudo_msa_mask_rate is not None:
        command.extend(["--pseudo_msa_mask_rate", args.pseudo_msa_mask_rate])
    if args.num_pseudo_msa is not None:
        command.extend(["--num_pseudo_msa", args.num_pseudo_msa])
    if args.allow_tf32 is not None:
        command.extend(["--allow_tf32", args.allow_tf32])

    print("planned command, not executed:")
    print("  " + " ".join(shell_quote(part) for part in command))
    print("note: full inference may download weights unless a valid local --weights_file/cache is present.")


def main() -> int:
    args = parse_args()
    if not args.skip_help_check:
        run_help_check(args.timeout)
    if args.fasta is not None:
        print_fasta_plan(args)
    elif args.skip_help_check:
        print("No checks requested; pass --fasta or omit --skip-help-check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
