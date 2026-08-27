#!/usr/bin/env python3
"""Small, dependency-aware fidelity statevector kernel smoke check."""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a two-feature FidelityStatevectorKernel and assert "
            "matrix shape, symmetry, and unit self-fidelity."
        )
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print the training and asymmetric matrices",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Imports are intentionally lazy so --help works even before Qiskit is
    # installed and the script remains safe to invoke from any working dir.
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.circuit import ParameterVector
    from qiskit_machine_learning.kernels import FidelityStatevectorKernel

    data_parameters = ParameterVector("x", 2)
    feature_map = QuantumCircuit(2)
    feature_map.ry(data_parameters[0], 0)
    feature_map.ry(data_parameters[1], 1)

    samples = np.asarray([[0.0, 0.0], [0.25, -0.5], [1.0, 0.75]])
    query = samples[:1]
    kernel = FidelityStatevectorKernel(feature_map=feature_map)

    training = kernel.evaluate(samples)
    asymmetric = kernel.evaluate(query, samples)

    assert training.shape == (3, 3), training.shape
    assert asymmetric.shape == (1, 3), asymmetric.shape
    assert np.allclose(training, training.T), training
    assert np.allclose(np.diag(training), 1.0), np.diag(training)
    assert np.allclose(training[0], asymmetric[0]), (training[0], asymmetric[0])

    if args.verbose:
        print("training matrix:\n", training)
        print("asymmetric matrix:\n", asymmetric)
    print("kernel smoke check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
