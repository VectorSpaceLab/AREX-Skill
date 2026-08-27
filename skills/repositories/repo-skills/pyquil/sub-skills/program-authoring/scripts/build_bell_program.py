#!/usr/bin/env python3
"""Build and validate a deterministic two-qubit Bell Program without services.

This helper constructs Quil, checks its canonical serialization, and optionally
prints it. It never compiles, simulates, submits, contacts a QVM/QPU, or reads
credentials. Run from any working directory, for example:

    python scripts/build_bell_program.py --validate-only
    python scripts/build_bell_program.py
"""

from __future__ import annotations

import argparse
import sys


EXPECTED_QUIL = (
    "DECLARE ro BIT[2]\n"
    "H 0\n"
    "CNOT 0 1\n"
    "MEASURE 0 ro[0]\n"
    "MEASURE 1 ro[1]\n"
)


def build_bell_program():
    """Return a service-free Bell-state construction with explicit readout."""
    from pyquil import Program
    from pyquil.gates import CNOT, H, MEASURE

    program = Program()
    ro = program.declare("ro", "BIT", 2)
    program += H(0)
    program += CNOT(0, 1)
    program += MEASURE(0, ro[0])
    program += MEASURE(1, ro[1])
    return program


def validate_program() -> str:
    """Build, serialize, round-trip parse, and return canonical Quil."""
    program = build_bell_program()
    quil = program.out()
    if quil != EXPECTED_QUIL:
        raise AssertionError(f"Unexpected canonical Quil:\n{quil!r}")
    reparsed = type(program)(quil)
    if reparsed.out() != EXPECTED_QUIL:
        raise AssertionError("Quil round-trip changed the canonical program")
    if program.get_qubit_indices() != {0, 1}:
        raise AssertionError("Bell program did not reference exactly qubits 0 and 1")
    if program.declarations["ro"].memory_size != 2:
        raise AssertionError("Bell readout declaration is not BIT[2]")
    return quil


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run local checks, and optionally print Quil."""
    parser = argparse.ArgumentParser(
        description="Construct and validate a canonical Bell Program; this does not execute it."
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="run construction and serialization assertions without printing Quil",
    )
    args = parser.parse_args(argv)

    try:
        quil = validate_program()
    except Exception as exc:  # noqa: BLE001 - concise helper diagnostic
        print(f"Bell Program validation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if not args.validate_only:
        print(quil, end="")
    else:
        print("Bell Program construction and Quil round-trip validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
