#!/usr/bin/env python3
"""Validate DMS mutation CSVs and build ESM variant prediction commands.

The helper mirrors the command-line contract of the ESM variant prediction
example while staying safe by default: it validates mutation notation and offset
consistency, then prints a shell-quoted command instead of launching inference.
"""

from __future__ import annotations

import argparse
import csv
import re
import shlex
import string
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

MUTATION_RE = re.compile(r"^([A-Z])(\d+)([A-Z])$")
STANDARD_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")
MSA_INSERTION_DELETE = str.maketrans({character: None for character in string.ascii_lowercase + ".*"})


@dataclass(frozen=True)
class MutationCheck:
    row_number: int
    mutation: str
    sequence_index: int
    warning: str | None = None


class ValidationError(Exception):
    """Raised when command construction would produce an invalid prediction run."""


def remove_insertions(sequence: str) -> str:
    """Remove A3M lowercase insertions plus '.' and '*' characters."""

    return sequence.translate(MSA_INSERTION_DELETE)


def read_first_msa_sequence(msa_path: Path) -> str | None:
    """Read and clean the first FASTA/A3M sequence without requiring Biopython."""

    sequence_parts: list[str] = []
    seen_header = False
    with msa_path.open("r", encoding="utf-8") as msa_handle:
        for raw_line in msa_handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if seen_header and sequence_parts:
                    break
                seen_header = True
                continue
            if seen_header:
                sequence_parts.append(line)
    if not sequence_parts:
        return None
    return remove_insertions("".join(sequence_parts))


def validate_mutation(mutation: str, sequence: str, offset_idx: int, row_number: int) -> MutationCheck:
    """Validate one single-substitution mutation against the wild-type sequence."""

    stripped_mutation = mutation.strip()
    if any(separator in stripped_mutation for separator in (":", "/", ";", ",", " ")):
        raise ValidationError(
            f"row {row_number}: {stripped_mutation!r} looks like a multi-mutant or invalid token; "
            "the example script expects one substitution such as A24D"
        )

    match = MUTATION_RE.fullmatch(stripped_mutation)
    if not match:
        raise ValidationError(
            f"row {row_number}: mutation {stripped_mutation!r} must match a single-substitution form like A24D"
        )

    wildtype_residue, position_text, mutant_residue = match.groups()
    mutation_position = int(position_text)
    sequence_index = mutation_position - offset_idx

    if sequence_index < 0 or sequence_index >= len(sequence):
        raise ValidationError(
            f"row {row_number}: mutation {stripped_mutation!r} maps to sequence index {sequence_index}; "
            f"valid indexes are 0..{len(sequence) - 1}. Check --offset-idx."
        )

    observed_residue = sequence[sequence_index]
    if observed_residue != wildtype_residue:
        raise ValidationError(
            f"row {row_number}: mutation {stripped_mutation!r} expects wild-type {wildtype_residue} "
            f"at sequence index {sequence_index}, but --sequence has {observed_residue!r}. "
            "Check --offset-idx and the reference sequence."
        )

    warning = None
    if wildtype_residue == mutant_residue:
        warning = f"row {row_number}: {stripped_mutation!r} mutates a residue to itself"
    elif wildtype_residue not in STANDARD_AMINO_ACIDS or mutant_residue not in STANDARD_AMINO_ACIDS:
        warning = f"row {row_number}: {stripped_mutation!r} uses a non-standard amino-acid letter"

    return MutationCheck(
        row_number=row_number,
        mutation=stripped_mutation,
        sequence_index=sequence_index,
        warning=warning,
    )


def validate_dms_csv(
    dms_input: Path,
    mutation_col: str,
    sequence: str,
    offset_idx: int,
    max_rows: int,
) -> tuple[int, list[MutationCheck]]:
    """Validate mutation notation and wild-type consistency in a DMS CSV."""

    if not dms_input.exists():
        raise ValidationError(f"DMS input does not exist: {dms_input}")
    if not dms_input.is_file():
        raise ValidationError(f"DMS input is not a file: {dms_input}")

    checked: list[MutationCheck] = []
    with dms_input.open("r", encoding="utf-8", newline="") as csv_handle:
        reader = csv.DictReader(csv_handle)
        if reader.fieldnames is None:
            raise ValidationError("DMS CSV has no header row")
        if mutation_col not in reader.fieldnames:
            available_columns = ", ".join(reader.fieldnames)
            raise ValidationError(
                f"mutation column {mutation_col!r} not found in DMS CSV; available columns: {available_columns}"
            )

        for zero_based_row_number, row in enumerate(reader, start=2):
            if max_rows and len(checked) >= max_rows:
                break
            mutation = row.get(mutation_col, "")
            if mutation is None or not mutation.strip():
                raise ValidationError(f"row {zero_based_row_number}: mutation column {mutation_col!r} is empty")
            checked.append(validate_mutation(mutation, sequence, offset_idx, zero_based_row_number))

    if not checked:
        raise ValidationError("DMS CSV contains no data rows to validate")
    return len(checked), checked


def model_list_suggests_msa(model_locations: Iterable[str]) -> bool:
    """Return True when model names look like MSA Transformer checkpoints."""

    return any("msa" in Path(model_location).name.lower() for model_location in model_locations)


def validate_strategy(args: argparse.Namespace) -> list[str]:
    """Validate cross-argument constraints and return non-fatal warnings."""

    warnings: list[str] = []
    msa_requested = model_list_suggests_msa(args.model_location) or args.msa_path is not None

    if msa_requested and args.scoring_strategy != "masked-marginals":
        raise ValidationError("MSA Transformer runs require --scoring-strategy masked-marginals")
    if msa_requested and args.msa_path is None:
        raise ValidationError("MSA Transformer runs require --msa-path")
    if args.msa_path is not None:
        if not args.msa_path.exists():
            raise ValidationError(f"MSA path does not exist: {args.msa_path}")
        if args.msa_samples <= 0:
            raise ValidationError("--msa-samples must be a positive integer")
        first_sequence = read_first_msa_sequence(args.msa_path)
        if first_sequence is None:
            raise ValidationError(f"MSA path has no readable FASTA/A3M sequence: {args.msa_path}")
        ungapped_first_sequence = first_sequence.replace("-", "")
        if ungapped_first_sequence != args.sequence:
            warnings.append(
                "first MSA sequence after stripping lowercase insertions, '.', '*', and gaps does not exactly "
                "match --sequence; confirm target numbering before inference"
            )

    bundled_runner = Path(__file__).with_name("run_variant_prediction.py").resolve()
    using_external_runner = args.predict_script.resolve() != bundled_runner
    if using_external_runner and args.nogpu:
        warnings.append(
            "external runners adapted from the original example may still contain tensor .cuda() calls; "
            "confirm CPU handling before relying on --nogpu"
        )

    return warnings


def build_predict_command(args: argparse.Namespace) -> list[str]:
    """Build the command that mirrors the variant prediction example."""

    command = [
        args.python,
        str(args.predict_script),
        "--model-location",
        *args.model_location,
        "--sequence",
        args.sequence,
        "--dms-input",
        str(args.dms_input),
        "--mutation-col",
        args.mutation_col,
        "--dms-output",
        str(args.dms_output),
        "--offset-idx",
        str(args.offset_idx),
        "--scoring-strategy",
        args.scoring_strategy,
    ]
    if args.msa_path is not None:
        command.extend(["--msa-path", str(args.msa_path), "--msa-samples", str(args.msa_samples)])
    if args.nogpu:
        command.append("--nogpu")
    return command


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate DMS mutations and print a safe ESM variant prediction command."
    )
    default_runner = Path(__file__).with_name("run_variant_prediction.py")
    parser.add_argument(
        "--predict-script",
        type=Path,
        default=default_runner,
        help="variant prediction runner to execute; defaults to the bundled skill-owned runner",
    )
    parser.add_argument("--python", default="python", help="Python launcher to place at the start of the printed command")
    parser.add_argument("--model-location", nargs="+", required=True, help="one or more model names or local checkpoint paths")
    parser.add_argument("--sequence", required=True, help="wild-type sequence used by mutation notation")
    parser.add_argument("--dms-input", type=Path, required=True, help="input DMS CSV")
    parser.add_argument("--mutation-col", default="mutant", help="CSV column containing mutations such as A24D")
    parser.add_argument("--dms-output", type=Path, required=True, help="output CSV path for predictions")
    parser.add_argument("--offset-idx", type=int, default=0, help="residue-numbering offset used by mutation notation")
    parser.add_argument(
        "--scoring-strategy",
        choices=["wt-marginals", "pseudo-ppl", "masked-marginals"],
        default="wt-marginals",
        help="prediction scoring strategy",
    )
    parser.add_argument("--msa-path", type=Path, help="A3M/FASTA MSA path required for MSA Transformer")
    parser.add_argument("--msa-samples", type=int, default=400, help="number of MSA sequences to sample from the start")
    parser.add_argument("--nogpu", action="store_true", help="include --nogpu in the printed command")
    parser.add_argument(
        "--max-rows",
        type=int,
        default=0,
        help="maximum DMS rows to validate; 0 validates all rows",
    )
    parser.add_argument("--execute", action="store_true", help="run the command after validation instead of only printing it")
    return parser


def print_validation_summary(checked_count: int, checks: Sequence[MutationCheck], warnings: Sequence[str]) -> None:
    print(f"Validated {checked_count} DMS mutation row(s).", file=sys.stderr)
    for check in checks:
        if check.warning:
            print(f"warning: {check.warning}", file=sys.stderr)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        if args.max_rows < 0:
            raise ValidationError("--max-rows must be 0 or a positive integer")
        sequence = args.sequence.strip().upper()
        if not sequence:
            raise ValidationError("--sequence must not be empty")
        args.sequence = sequence

        strategy_warnings = validate_strategy(args)
        checked_count, checks = validate_dms_csv(
            args.dms_input,
            args.mutation_col,
            args.sequence,
            args.offset_idx,
            args.max_rows,
        )
        command = build_predict_command(args)
    except ValidationError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print_validation_summary(checked_count, checks, strategy_warnings)
    print(shlex.join(command))

    if args.execute:
        return subprocess.run(command, check=False).returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
