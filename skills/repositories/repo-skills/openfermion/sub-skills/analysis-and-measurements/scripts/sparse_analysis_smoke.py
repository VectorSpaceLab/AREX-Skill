#!/usr/bin/env python3
"""Run a deterministic, tiny OpenFermion sparse-analysis smoke check.

The helper builds a public two-qubit Hamiltonian, converts it to a sparse
matrix, computes a bounded ground state and dense spectrum, and prints the
shape and eigenvalues. It never downloads data, writes files, or creates a
matrix larger than 16 by 16 (the optional ``--n-qubits`` bound is 4).

Example:
    python sparse_analysis_smoke.py
    python sparse_analysis_smoke.py --n-qubits 3
"""

from __future__ import annotations

import argparse
import sys

import numpy as np


MAX_QUBITS = 4


def build_hamiltonian():
    from openfermion import QubitOperator
    """Return a fixed two-qubit Hamiltonian embedded in a requested space."""
    return (
        QubitOperator((), 0.1)
        + QubitOperator("Z0", -0.75)
        + QubitOperator("Z1", -0.50)
        + QubitOperator("X0 X1", -0.20)
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse safe, bounded command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--n-qubits",
        type=int,
        default=2,
        help=f"Hilbert-space qubit count; choose 2 through {MAX_QUBITS} (default: 2).",
    )
    args = parser.parse_args(argv)
    if not 2 <= args.n_qubits <= MAX_QUBITS:
        parser.error(f"--n-qubits must be between 2 and {MAX_QUBITS}")
    return args


def main(argv: list[str] | None = None) -> int:
    """Execute the bounded numerical check and print reproducible diagnostics."""
    args = parse_args(argv)
    try:
        from openfermion.linalg import get_ground_state, get_sparse_operator, sparse_eigenspectrum
    except ImportError as exc:
        print(f"OpenFermion import failed: {exc}", file=sys.stderr)
        return 2
    hamiltonian = build_hamiltonian()
    sparse_matrix = get_sparse_operator(hamiltonian, n_qubits=args.n_qubits)
    expected_dimension = 2**args.n_qubits
    if sparse_matrix.shape != (expected_dimension, expected_dimension):
        raise RuntimeError(
            f"unexpected matrix shape {sparse_matrix.shape}; "
            f"expected {(expected_dimension, expected_dimension)}"
        )

    ground_energy, ground_state = get_ground_state(sparse_matrix)
    spectrum = sparse_eigenspectrum(sparse_matrix)
    residual = np.linalg.norm(sparse_matrix @ ground_state - ground_energy * ground_state)
    if not np.isclose(np.linalg.norm(ground_state), 1.0, atol=1e-8):
        raise RuntimeError("ground-state vector is not normalized")
    if not np.isclose(residual, 0.0, atol=1e-8):
        raise RuntimeError(f"ground-state residual is too large: {residual}")

    print(f"matrix_shape={sparse_matrix.shape} nnz={sparse_matrix.nnz}")
    print(f"ground_energy={ground_energy:.12f}")
    print("eigenvalues=" + np.array2string(spectrum, precision=12, separator=","))
    print(f"ground_residual={residual:.3e}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (TypeError, ValueError, RuntimeError) as exc:
        print(f"sparse-analysis smoke check failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
