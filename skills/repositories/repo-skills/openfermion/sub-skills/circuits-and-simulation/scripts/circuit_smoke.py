#!/usr/bin/env python3
"""Build a deterministic, tiny OpenFermion-to-Cirq circuit smoke check.

The helper has no network, credential, filesystem-write, plugin, or large
workload behavior.  The optional Slater example checks the same bounded
register using the public state-preparation API.
"""

from __future__ import annotations

import argparse
import sys


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a two-qubit Trotter product from a tiny QubitOperator and "
            "report Cirq qubits, operations, and depth."
        )
    )
    parser.add_argument(
        "--tiny",
        action="store_true",
        help="run the bounded two-term example (the safe default behavior)",
    )
    parser.add_argument(
        "--with-slater",
        action="store_true",
        help="also build a two-mode, one-particle Slater preparation circuit",
    )
    return parser


def _build_trotter_circuit():
    import cirq
    import openfermion as of

    qubits = cirq.LineQubit.range(2)
    hamiltonian = of.QubitOperator("Z0", 0.5) + of.QubitOperator("X0 X1", 0.25)
    factors = list(of.trotter_operator_grouping(hamiltonian, trotter_order=1))

    circuit = cirq.Circuit()
    for factor in factors:
        pauli_sum = of.qubit_operator_to_pauli_sum(factor, qubits)
        # Each factor contains one Pauli term, so Cirq's commuting-term
        # precondition is explicit and the example remains deterministic.
        circuit.append(cirq.PauliSumExponential(pauli_sum, exponent=-0.2))
    return hamiltonian, qubits, factors, circuit


def _build_slater_circuit():
    import cirq
    import numpy
    import openfermion as of

    qubits = cirq.LineQubit.range(2)
    matrix = numpy.array([[1.0, 1.0]]) / numpy.sqrt(2.0)
    circuit = cirq.Circuit(of.prepare_slater_determinant(qubits, matrix))
    return matrix, qubits, circuit


def _report(label, qubits, circuit) -> None:
    operations = list(circuit.all_operations())
    print(f"{label}:")
    print(f"  qubits: {len(qubits)}")
    print(f"  operations: {len(operations)}")
    print(f"  depth: {len(circuit)}")


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    # --tiny is an explicit, readable spelling for the default bounded mode;
    # no alternate large mode is exposed by this helper.
    del args.tiny
    try:
        hamiltonian, qubits, factors, circuit = _build_trotter_circuit()
    except ImportError as exc:
        parser.exit(
            2,
            "circuit_smoke.py requires public OpenFermion and Cirq imports: "
            f"{exc}\n",
        )

    print("tiny_trotter:")
    print(f"  hamiltonian_terms: {len(hamiltonian.terms)}")
    print(f"  grouped_factors: {len(factors)}")
    _report("  circuit", qubits, circuit)

    if args.with_slater:
        try:
            matrix, slater_qubits, slater_circuit = _build_slater_circuit()
        except ImportError as exc:
            parser.exit(2, f"Slater demonstration requires public imports: {exc}\n")
        print(f"slater_matrix_shape: {matrix.shape}")
        _report("slater_preparation", slater_qubits, slater_circuit)

    return 0


if __name__ == "__main__":
    sys.exit(main())
