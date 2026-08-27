#!/usr/bin/env python3
"""Safe TensorFlow Quantum smoke checks.

This helper is intentionally small and self-contained. It validates that the
installed TensorFlow Quantum package imports cleanly, that the public export
surface is present, and that a few tiny TFQ behaviors still work.

Usage:
  python scripts/tfq_smoke_check.py --quick
  python scripts/tfq_smoke_check.py --quick --layers --datasets --differentiators --math

Optional `--repo-root` can be used for local debugging from a checkout, but the
helper does not depend on the checkout by default.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def prepare_import_path(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def import_package():
    os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
    import cirq  # noqa: F401
    import sympy  # noqa: F401
    import tensorflow as tf
    import tensorflow_quantum as tfq

    return tf, tfq, cirq, sympy


def check_public_surface(tfq) -> None:
    top_level = [
        "layers",
        "differentiators",
        "datasets",
        "optimizers",
        "math",
        "noise",
        "util",
        "get_expectation_op",
        "get_sampled_expectation_op",
        "get_sampling_op",
        "get_state_op",
        "get_unitary_op",
        "append_circuit",
        "padded_to_ragged",
        "padded_to_ragged2d",
        "resolve_parameters",
        "convert_to_tensor",
        "from_tensor",
        "get_quantum_concurrent_op_mode",
        "set_quantum_concurrent_op_mode",
    ]
    for name in top_level:
        require(hasattr(tfq, name), f"missing top-level export: {name}")

    layer_names = [
        "AddCircuit",
        "Expectation",
        "Sample",
        "SampledExpectation",
        "State",
        "Unitary",
        "PQC",
        "ControlledPQC",
        "NoisyPQC",
        "NoisyControlledPQC",
    ]
    for name in layer_names:
        require(hasattr(tfq.layers, name), f"missing layer export: {name}")

    diff_names = [
        "ParameterShift",
        "ForwardDifference",
        "CentralDifference",
        "LinearCombination",
        "Adjoint",
        "Differentiator",
    ]
    for name in diff_names:
        require(hasattr(tfq.differentiators, name),
                f"missing differentiator export: {name}")

    math_names = [
        "inner_product",
        "fidelity",
        "mps_1d_expectation",
        "mps_1d_sample",
        "mps_1d_sampled_expectation",
    ]
    for name in math_names:
        require(hasattr(tfq.math, name), f"missing math export: {name}")


def quick_smoke(tfq, tf, cirq, sympy) -> None:
    q = cirq.GridQubit(0, 0)
    theta = sympy.Symbol("theta")
    circuit = cirq.Circuit(cirq.X(q) ** theta)
    serialized = tfq.convert_to_tensor([circuit])
    round_tripped = tfq.from_tensor(serialized)
    require(len(round_tripped) == 1, "round trip should preserve batch size")
    require(round_tripped[0] == circuit, "round trip should preserve circuit")

    observable = tfq.convert_to_tensor([[cirq.Z(q)]])
    expectation = tfq.get_expectation_op()
    value = expectation(serialized, ["theta"], [[0.0]], observable)
    require(value.shape == (1, 1), f"unexpected expectation shape: {value.shape}")
    require(abs(float(value.numpy()[0, 0]) - 1.0) < 1e-5,
            f"unexpected expectation value: {value.numpy()}")

    print("quick import/version smoke passed")
    print(f"tensorflow_quantum={getattr(tfq, '__version__', 'unknown')}")
    print(f"tensorflow={tf.__version__}")


def layer_smoke(tfq, tf, cirq, sympy) -> None:
    q = cirq.GridQubit(0, 0)
    inputs = tf.keras.Input(shape=(), dtype=tf.string)
    helper = cirq.Circuit(cirq.X(q))
    model_circuit = cirq.Circuit(cirq.ry(sympy.Symbol("theta"))(q))

    augmented = tfq.layers.AddCircuit()(inputs, append=helper)
    outputs = tfq.layers.PQC(model_circuit, cirq.Z(q))(augmented)
    model = tf.keras.Model(inputs, outputs)

    data = tfq.convert_to_tensor([cirq.Circuit(), cirq.Circuit(cirq.H(q))])
    out = model(data)
    require(out.shape[0] == 2, f"unexpected layer batch size: {out.shape}")
    require(bool(tf.reduce_all(tf.math.is_finite(out)).numpy()),
            "layer output must be finite")
    print("layer smoke passed")


def dataset_smoke(tfq, cirq) -> None:
    qubits = cirq.GridQubit.rect(1, 5)
    circuits, labels = tfq.datasets.excited_cluster_states(qubits)
    require(len(circuits) == 6, f"unexpected cluster-state count: {len(circuits)}")
    require(len(labels) == 6, f"unexpected label count: {len(labels)}")
    require(labels[-1] == -1, "cluster-state reference label should be -1")
    print("dataset smoke passed")


def math_smoke(tfq, cirq, sympy) -> None:
    q = cirq.GridQubit(0, 0)
    alpha = sympy.Symbol("alpha")
    program = cirq.Circuit(cirq.X(q) ** alpha)
    reference = cirq.Circuit(cirq.X(q))
    programs = tfq.convert_to_tensor([program])
    references = tfq.convert_to_tensor([[reference]])

    inner = tfq.math.inner_product(programs, ["alpha"], [[1.0]], references)
    fidelity = tfq.math.fidelity(programs, ["alpha"], [[1.0]], references)
    require(tuple(inner.shape) == (1, 1), f"unexpected inner product shape: {inner.shape}")
    require(tuple(fidelity.shape) == (1, 1), f"unexpected fidelity shape: {fidelity.shape}")

    qubits = cirq.GridQubit.rect(1, 5)
    beta = sympy.Symbol("beta")
    mps_program = cirq.Circuit(
        cirq.X(qubits[0]) ** beta,
        cirq.Z(qubits[1]),
        cirq.CNOT(qubits[2], qubits[3]),
        cirq.Y(qubits[4]) ** beta,
    )
    mps_programs = tfq.convert_to_tensor([mps_program])
    mps_ops = tfq.convert_to_tensor([[cirq.Z(qubits[0])]])
    mps_expectation = tfq.math.mps_1d_expectation(
        mps_programs, ["beta"], [[0.123]], mps_ops, bond_dim=4)
    mps_samples = tfq.math.mps_1d_sample(
        mps_programs, ["beta"], [[0.123]], [3], bond_dim=4)
    mps_sampled_expectation = tfq.math.mps_1d_sampled_expectation(
        mps_programs, ["beta"], [[0.123]], mps_ops, [[10]], bond_dim=4)
    require(tuple(mps_expectation.shape) == (1, 1),
            f"unexpected MPS expectation shape: {mps_expectation.shape}")
    require(mps_samples.shape[0] == 1,
            f"unexpected MPS sample batch shape: {mps_samples.shape}")
    require(tuple(mps_sampled_expectation.shape) == (1, 1),
            "unexpected MPS sampled expectation shape: "
            f"{mps_sampled_expectation.shape}")
    print("math smoke passed")


def differentiator_smoke(tfq, tf, cirq, sympy) -> None:
    q = cirq.GridQubit(0, 0)
    theta = sympy.Symbol("theta")
    circuit = cirq.Circuit(cirq.Y(q) ** theta)
    layer = tfq.layers.Expectation(
        differentiator=tfq.differentiators.ParameterShift())

    values = tf.Variable([[0.3]], dtype=tf.float32)
    with tf.GradientTape() as tape:
        output = layer(circuit,
                       symbol_names=["theta"],
                       symbol_values=values,
                       operators=cirq.X(q))
    grad = tape.gradient(output, values)
    require(grad is not None, "differentiator gradient should exist")
    require(tuple(grad.shape) == (1, 1), f"unexpected gradient shape: {grad.shape}")
    require(bool(tf.reduce_all(tf.math.is_finite(grad)).numpy()),
            "gradient must be finite")
    print("differentiator smoke passed")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None,
                        help="Optional local checkout root for debugging.")
    parser.add_argument("--quick", action="store_true",
                        help="Run the minimal import and behavior smoke.")
    parser.add_argument("--layers", action="store_true",
                        help="Add a tiny AddCircuit plus PQC layer check.")
    parser.add_argument("--datasets", action="store_true",
                        help="Add the five-qubit excited-cluster dataset smoke.")
    parser.add_argument("--differentiators", action="store_true",
                        help="Add a tiny ParameterShift gradient smoke.")
    parser.add_argument("--math", action="store_true",
                        help="Add inner-product, fidelity, and tiny MPS helper checks.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    prepare_import_path(args.repo_root)
    tf, tfq, cirq, sympy = import_package()

    check_public_surface(tfq)
    if not args.quick and not (args.layers or args.datasets or args.differentiators or args.math):
        args.quick = True

    if args.quick:
        quick_smoke(tfq, tf, cirq, sympy)
    if args.layers:
        layer_smoke(tfq, tf, cirq, sympy)
    if args.datasets:
        dataset_smoke(tfq, cirq)
    if args.differentiators:
        differentiator_smoke(tfq, tf, cirq, sympy)
    if args.math:
        math_smoke(tfq, cirq, sympy)

    print("SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
