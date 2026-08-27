#!/usr/bin/env python3
"""Run a tiny CPU or conditional CUDA TorchConnector forward/backward smoke.

CUDA is never assumed: ``--device cuda`` reports a skip when CUDA is not
available. The smoke uses a one-qubit EstimatorQNN and an exact reference
estimator, so it checks the public connector path without training a model.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np


def main(argv: list[str] | None = None) -> int:
    """Run the connector smoke on CPU or, when available, CUDA."""
    parser = argparse.ArgumentParser(description="Smoke-test TorchConnector forward and backward.")
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda"),
        default="cpu",
        help="Torch device; CUDA is checked and skipped when unavailable",
    )
    args = parser.parse_args(argv)

    try:
        import torch
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"TorchConnector smoke could not import PyTorch: {exc}")
        print("Install it with: python -m pip install 'qiskit-machine-learning[torch]'")
        return 2

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA is not available in this interpreter; connector CUDA smoke skipped.")
        return 0

    device = torch.device(args.device)
    try:
        from qiskit_machine_learning.circuit.library import qnn_circuit
        from qiskit_machine_learning.connectors import TorchConnector
        from qiskit_machine_learning.neural_networks import EstimatorQNN
        from qiskit_machine_learning.primitives import QMLEstimator

        circuit, input_params, weight_params = qnn_circuit(num_qubits=1)
        qnn = EstimatorQNN(
            circuit=circuit,
            estimator=QMLEstimator(),
            input_params=input_params,
            weight_params=weight_params,
            input_gradients=True,
        )
        initial_weights = np.zeros(qnn.num_weights, dtype=float)
        connector = TorchConnector(
            qnn,
            initial_weights=initial_weights,
            sparse=False,
        ).to(device)

        inputs = torch.tensor([[0.125]], dtype=torch.float32, device=device, requires_grad=True)
        output = connector(inputs)
        if tuple(output.shape) != (1, 1):
            raise AssertionError(f"unexpected connector output shape: {tuple(output.shape)}")
        output.square().sum().backward()
        if inputs.grad is None:
            raise AssertionError("input gradient was not produced")
        if connector.weight.grad is None:
            raise AssertionError("weight gradient was not produced")
        print(
            "TorchConnector smoke OK; "
            f"device={device}, output_shape={tuple(output.shape)}, "
            f"input_grad_shape={tuple(inputs.grad.shape)}, "
            f"weight_grad_shape={tuple(connector.weight.grad.shape)}"
        )
        return 0
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"TorchConnector smoke could not import a Qiskit ML dependency: {exc}")
        print("Install the base package with: python -m pip install qiskit-machine-learning")
        return 2
    except Exception as exc:  # preserve the exact failure for diagnosis
        print(f"TorchConnector smoke FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
