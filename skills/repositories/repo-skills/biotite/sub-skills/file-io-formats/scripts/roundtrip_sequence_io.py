#!/usr/bin/env python3
"""Round-trip or validate FASTA files with Biotite, without network access."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any


def _load_biotite() -> tuple[Any, Any]:
    try:
        import biotite.sequence as seq
        import biotite.sequence.io.fasta as fasta
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(
            "Biotite FASTA imports failed. Install/import Biotite in the active "
            f"environment first. Original error: {type(exc).__name__}: {exc}"
        ) from exc
    return seq, fasta


def _sequence_type(seq_module: Any, type_name: str) -> type | None:
    if type_name == "auto":
        return None
    if type_name == "protein":
        return seq_module.ProteinSequence
    if type_name == "nucleotide":
        return seq_module.NucleotideSequence
    raise ValueError(f"Unsupported sequence type: {type_name}")


def roundtrip_literal(chars_per_line: int, forced_type: str) -> dict[str, str]:
    seq, fasta = _load_biotite()
    seq_type = _sequence_type(seq, forced_type)

    original = fasta.FastaFile(chars_per_line=chars_per_line)
    fasta.set_sequence(original, seq.ProteinSequence("ACDEFGHIK"), header="protein")
    fasta.set_sequence(
        original,
        seq.NucleotideSequence("ACGTTGCA", ambiguous=False),
        header="dna",
    )

    with tempfile.NamedTemporaryFile("w+", suffix=".fasta") as handle:
        original.write(handle.name)
        parsed = fasta.FastaFile.read(handle.name, chars_per_line=chars_per_line)

    if dict(parsed.items()) != dict(original.items()):
        raise AssertionError("Raw FASTA entries changed during round trip")

    sequences = fasta.get_sequences(parsed, seq_type=seq_type)
    if set(sequences) != {"protein", "dna"}:
        raise AssertionError("Unexpected FASTA headers after conversion")

    return {header: type(sequence).__name__ for header, sequence in sequences.items()}


def validate_fasta(path: Path, forced_type: str) -> dict[str, Any]:
    seq, fasta = _load_biotite()
    seq_type = _sequence_type(seq, forced_type)

    fasta_file = fasta.FastaFile.read(path)
    entries = dict(fasta_file.items())
    if not entries:
        raise AssertionError("FASTA file contains no entries")

    sequences = fasta.get_sequences(fasta_file, seq_type=seq_type)
    lengths = {header: len(sequence) for header, sequence in sequences.items()}
    raw_lengths = {header: len(seq_string) for header, seq_string in entries.items()}
    if set(lengths) != set(raw_lengths):
        raise AssertionError("Converted sequence headers differ from raw FASTA headers")

    return {
        "entries": len(entries),
        "headers": list(entries),
        "converted_types": {
            header: type(sequence).__name__ for header, sequence in sequences.items()
        },
        "lengths": lengths,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Round-trip a tiny literal FASTA or validate a provided FASTA path "
            "with Biotite. No network or repository fixtures are used."
        )
    )
    parser.add_argument(
        "fasta_path",
        nargs="?",
        type=Path,
        help="Optional local FASTA path to validate instead of running the literal round trip.",
    )
    parser.add_argument(
        "--seq-type",
        choices=["auto", "protein", "nucleotide"],
        default="auto",
        help="Force FASTA conversion type; default lets Biotite infer the type.",
    )
    parser.add_argument(
        "--chars-per-line",
        type=int,
        default=80,
        help="Line wrap length for the bundled literal round trip.",
    )
    args = parser.parse_args(argv)

    try:
        if args.fasta_path is None:
            result = roundtrip_literal(args.chars_per_line, args.seq_type)
            print("OK literal FASTA round trip")
            print("converted_types=" + repr(result))
        else:
            result = validate_fasta(args.fasta_path, args.seq_type)
            print("OK FASTA validation")
            print("entries=" + str(result["entries"]))
            print("headers=" + repr(result["headers"]))
            print("converted_types=" + repr(result["converted_types"]))
            print("lengths=" + repr(result["lengths"]))
        return 0
    except Exception as exc:
        print(f"FASTA check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
