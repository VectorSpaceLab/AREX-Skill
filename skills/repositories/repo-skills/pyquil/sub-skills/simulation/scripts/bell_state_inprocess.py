#!/usr/bin/env python3
"""Deterministic, service-free PyQuil Bell-state simulation smoke test.

This helper uses only in-process PyQuil APIs. It compares the flat reference
simulator with PyQVM's default NumPy simulator, checks the canonical basis
order (q0 is the rightmost bit), and prints a concise success line.

Example:
    python scripts/bell_state_inprocess.py
"""

from __future__ import annotations

import argparse

import numpy as np

from pyquil import Program
from pyquil.gates import CNOT, H, X
from pyquil.paulis import sX, sY, sZ
from pyquil.pyqvm import PyQVM
from pyquil.simulation import ReferenceWavefunctionSimulator


def bell_program() -> Program:
    """Return the two-qubit Bell preparation program."""
    return Program(H(0), CNOT(0, 1))


def run_check() -> None:
    """Run deterministic local assertions and raise on any mismatch."""
    n_qubits = 2
    program = bell_program()
    expected = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)

    reference = ReferenceWavefunctionSimulator(n_qubits=n_qubits).do_program(program)
    qam = PyQVM(n_qubits=n_qubits, seed=123).execute(program)
    numpy_tensor = qam.wf_simulator.wf
    # NumPy's tensor axes put q0 on the left; reverse them for canonical flat order.
    numpy_vector = numpy_tensor.transpose().reshape(-1)

    np.testing.assert_allclose(reference.wf, expected, atol=1e-12)
    np.testing.assert_allclose(numpy_vector, expected, atol=1e-12)
    np.testing.assert_allclose(np.abs(reference.wf) ** 2, [0.5, 0.0, 0.0, 0.5], atol=1e-12)

    # A basis probe catches accidental q0-left/q0-right flattening.
    q0_probe = ReferenceWavefunctionSimulator(n_qubits=n_qubits).do_program(Program(X(0)))
    np.testing.assert_allclose(q0_probe.wf, [0.0, 1.0, 0.0, 0.0], atol=1e-12)

    for operator, expected_value in (
        (sX(0) * sX(1), 1.0),
        (sY(0) * sY(1), -1.0),
        (sZ(0) * sZ(1), 1.0),
    ):
        assert np.isclose(reference.expectation(operator), expected_value, atol=1e-12)


def main() -> int:
    """Parse safe CLI arguments, run checks, and report success."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    run_check()
    print("OK: local Bell state, canonical ordering, probabilities, and Pauli expectations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
