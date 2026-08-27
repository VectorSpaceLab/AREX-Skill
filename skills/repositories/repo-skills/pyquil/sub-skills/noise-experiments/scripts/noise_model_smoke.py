#!/usr/bin/env python3
"""Run a deterministic, service-free PyQuil noise-model smoke check.

The check validates legacy Kraus completeness, an asymmetric assignment matrix,
readout probability round-tripping, and the Quil transformation produced by
``apply_noise_model``. It never starts a QVM/QPU/QCS service, reads credentials,
compiles, submits, or downloads data.

Examples:
    python scripts/noise_model_smoke.py --help
    python scripts/noise_model_smoke.py
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

import networkx as nx
import numpy as np

from pyquil import Program
from pyquil.gates import CZ, RX, RZ
from pyquil.noise import (
    apply_noise_model,
    combine_kraus_maps,
    corrupt_bitstring_probs,
    correct_bitstring_probs,
    damping_after_dephasing,
    damping_kraus_map,
    decoherence_noise_with_asymmetric_ro,
    dephasing_kraus_map,
    estimate_bitstring_probs,
    tensor_kraus_maps,
)
from pyquil.quantum_processor import NxQuantumProcessor


def _assert_kraus_complete(kraus_ops: list[np.ndarray], qubits: int) -> None:
    """Check dimensions and the trace-preserving completeness relation."""
    dimension = 2**qubits
    if not kraus_ops:
        raise AssertionError("a Kraus map must contain at least one operator")
    for operator in kraus_ops:
        array = np.asarray(operator, dtype=complex)
        if array.shape != (dimension, dimension):
            raise AssertionError(f"expected {(dimension, dimension)}, got {array.shape}")
        if not np.all(np.isfinite(array)):
            raise AssertionError("Kraus operator contains non-finite values")
    completeness = sum(operator.conj().T @ operator for operator in kraus_ops)
    if not np.allclose(completeness, np.eye(dimension), atol=1e-10):
        raise AssertionError(f"Kraus completeness failed:\n{completeness}")


def _check_readout(model: Any, p00: float, p11: float) -> None:
    """Check the legacy column-stochastic assignment matrices."""
    # The legacy NoiseModel stores this row-stochastic helper layout. The
    # READOUT-POVM pragma uses a different flattened conditional layout; the
    # header reconstructs that layout from the diagonal values.
    expected_internal = np.array([[p00, 1.0 - p00], [1.0 - p11, p11]])
    if not model.assignment_probs:
        raise AssertionError("model has no assignment probabilities")
    for qubit, matrix in model.assignment_probs.items():
        matrix = np.asarray(matrix, dtype=float)
        if matrix.shape != (2, 2):
            raise AssertionError(f"assignment matrix for {qubit} has shape {matrix.shape}")
        if np.any(matrix < 0.0) or not np.allclose(matrix.sum(axis=1), 1.0):
            raise AssertionError(f"assignment matrix for {qubit} is not row-stochastic")
        if not np.allclose(matrix, expected_internal):
            raise AssertionError(f"unexpected internal assignment matrix for {qubit}: {matrix}")


def run_check(p00: float, p11: float) -> dict[str, Any]:
    """Build and validate a tiny model and transformed program."""
    if not (0.0 <= p00 <= 1.0 and 0.0 <= p11 <= 1.0):
        raise ValueError("p00 and p11 must be between 0 and 1")

    # Validate the public helper primitives independently of the ISA-derived model.
    damping = damping_kraus_map(0.05)
    dephasing = dephasing_kraus_map(0.04)
    _assert_kraus_complete(damping, 1)
    _assert_kraus_complete(dephasing, 1)
    _assert_kraus_complete(tensor_kraus_maps(damping, dephasing), 2)
    _assert_kraus_complete(combine_kraus_maps(damping, dephasing), 1)
    _assert_kraus_complete(damping_after_dephasing(30e-6, 20e-6, 40e-9), 1)

    # A two-node processor supplies a local legacy CompilerISA; no service is queried.
    processor = NxQuantumProcessor(nx.complete_graph(2))
    model = decoherence_noise_with_asymmetric_ro(processor.to_compiler_isa(), p00=p00, p11=p11)
    _check_readout(model, p00, p11)
    for gate_model in model.gates:
        _assert_kraus_complete(list(gate_model.kraus_ops), len(gate_model.targets))

    program = Program(RX(np.pi / 2, 0), CZ(0, 1), RZ(0.25, 1))
    transformed = apply_noise_model(program, model)
    quil = transformed.out()
    if "NOISY-RX-PLUS-90 0" not in quil or "NOISY-CZ 0 1" not in quil:
        raise AssertionError("recognized gates were not transformed")
    if "RZ(0.25) 1" not in quil or "NOISY-RZ" in quil:
        raise AssertionError("RZ should remain the documented noiseless boundary")
    if quil.count("PRAGMA READOUT-POVM") != 2:
        raise AssertionError("expected one readout pragma per model qubit")
    if "PRAGMA ADD-KRAUS" not in quil or "DEFGATE NOISY-" not in quil:
        raise AssertionError("expected transformed noise definitions")
    povm_match = re.search(r'PRAGMA READOUT-POVM 0 "\(([^)]*)\)"', quil)
    if povm_match is None:
        raise AssertionError("noise-model header did not emit a qubit-0 POVM")
    povm_values = np.fromstring(povm_match.group(1), sep=" ")
    expected_povm = np.array([p00, 1.0 - p11, 1.0 - p00, p11])
    if not np.allclose(povm_values, expected_povm):
        raise AssertionError(f"unexpected POVM values: {povm_values}")

    # Synthetic shot post-processing is exact up to floating point error.
    shots = np.array([[0, 0], [0, 1], [1, 1], [0, 0]], dtype=int)
    true_probs = estimate_bitstring_probs(shots)
    assignment = [
        np.array([[0.90, 0.20], [0.10, 0.80]]),
        np.array([[0.95, 0.15], [0.05, 0.85]]),
    ]
    corrupted = corrupt_bitstring_probs(true_probs, assignment)
    recovered = correct_bitstring_probs(corrupted, assignment)
    if true_probs.shape != (2, 2) or not np.isclose(true_probs.sum(), 1.0):
        raise AssertionError("unexpected bitstring probability tensor")
    if not np.allclose(recovered, true_probs, atol=1e-10):
        raise AssertionError("readout correction failed its deterministic round trip")

    return {
        "channel_checks": "passed",
        "gate_models": len(model.gates),
        "assignment_qubits": sorted(model.assignment_probs),
        "assignment_layouts_checked": ["NoiseModel internal row layout", "READOUT-POVM conditional layout"],
        "transformed_contains": ["DEFGATE", "ADD-KRAUS", "READOUT-POVM"],
        "transformed_program_is_not_executed": True,
        "probability_shape": list(true_probs.shape),
        "probability_round_trip": "passed",
    }


def main() -> int:
    """Parse arguments and print a small JSON summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p00", type=float, default=0.93, help="probability of observing 0 when 0 was prepared")
    parser.add_argument("--p11", type=float, default=0.82, help="probability of observing 1 when 1 was prepared")
    args = parser.parse_args()
    print(json.dumps(run_check(args.p00, args.p11), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
