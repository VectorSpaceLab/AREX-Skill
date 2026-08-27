#!/usr/bin/env python3
"""Tiny public-API EstimatorQNN/SamplerQNN forward-backward smoke.

The script is intentionally dependency-light and performs no network access. It
imports only public Qiskit and Qiskit Machine Learning APIs, so it can be run
from any current working directory after installing the package.
"""

from __future__ import annotations

import argparse

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from qiskit.quantum_info import SparsePauliOp
from qiskit_machine_learning.neural_networks import EstimatorQNN, SamplerQNN


def run_smoke() -> None:
    """Run one estimator and one sampler QNN forward/backward check."""
    x = Parameter("x")
    w = Parameter("w")

    estimator_circuit = QuantumCircuit(1)
    estimator_circuit.ry(x, 0)
    estimator_circuit.rx(w, 0)
    estimator_qnn = EstimatorQNN(
        circuit=estimator_circuit,
        estimator=StatevectorEstimator(),
        observables=SparsePauliOp.from_list([("Z", 1)]),
        input_params=[x],
        weight_params=[w],
        input_gradients=True,
    )
    estimator_output = np.asarray(estimator_qnn.forward([0.2], [0.3]))
    estimator_input_grad, estimator_weight_grad = estimator_qnn.backward([0.2], [0.3])
    estimator_input_grad = np.asarray(estimator_input_grad)
    estimator_weight_grad = np.asarray(estimator_weight_grad)
    if estimator_output.shape != (1, 1):
        raise AssertionError(f"unexpected estimator output shape: {estimator_output.shape}")
    if estimator_input_grad.shape != (1, 1, 1):
        raise AssertionError(
            f"unexpected estimator input-gradient shape: {estimator_input_grad.shape}"
        )
    if estimator_weight_grad.shape != (1, 1, 1):
        raise AssertionError(
            f"unexpected estimator weight-gradient shape: {estimator_weight_grad.shape}"
        )

    sampler_circuit = QuantumCircuit(1)
    sampler_circuit.ry(x, 0)
    sampler_circuit.rx(w, 0)
    sampler_circuit.measure_all()
    sampler_qnn = SamplerQNN(
        circuit=sampler_circuit,
        sampler=StatevectorSampler(),
        input_params=[x],
        weight_params=[w],
        interpret=lambda measured: measured,
        output_shape=2,
        input_gradients=True,
    )
    sampler_output = np.asarray(sampler_qnn.forward([0.2], [0.3]))
    sampler_input_grad, sampler_weight_grad = sampler_qnn.backward([0.2], [0.3])
    sampler_input_grad = np.asarray(sampler_input_grad)
    sampler_weight_grad = np.asarray(sampler_weight_grad)
    if sampler_output.shape != (1, 2):
        raise AssertionError(f"unexpected sampler output shape: {sampler_output.shape}")
    if sampler_input_grad.shape != (1, 2, 1):
        raise AssertionError(
            f"unexpected sampler input-gradient shape: {sampler_input_grad.shape}"
        )
    if sampler_weight_grad.shape != (1, 2, 1):
        raise AssertionError(
            f"unexpected sampler weight-gradient shape: {sampler_weight_grad.shape}"
        )
    if not np.allclose(sampler_output.sum(axis=1), 1.0, atol=0.08):
        raise AssertionError(f"sampler probabilities do not sum to one: {sampler_output}")

    print("EstimatorQNN:", estimator_output.shape, estimator_input_grad.shape, estimator_weight_grad.shape)
    print("SamplerQNN:", sampler_output.shape, sampler_input_grad.shape, sampler_weight_grad.shape)
    print("qnn smoke passed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a tiny public EstimatorQNN/SamplerQNN forward-backward smoke."
    )
    parser.parse_args()
    run_smoke()


if __name__ == "__main__":
    main()
