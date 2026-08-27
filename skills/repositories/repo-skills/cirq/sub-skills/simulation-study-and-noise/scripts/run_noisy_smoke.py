#!/usr/bin/env python3
"""Deterministic one-qubit Cirq noisy-sampling smoke demo."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def _probability(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("value must be between 0 and 1 inclusive")
    return parsed


def _format_counter(counter) -> str:
    items = ", ".join(f"{key}: {counter[key]}" for key in sorted(counter))
    return "{" + items + "}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic one-qubit Cirq sampling demo with an amplitude-damping "
            "ConstantQubitNoiseModel and print measurement histograms."
        )
    )
    parser.add_argument(
        "--repetitions",
        type=_positive_int,
        default=100,
        help="number of sampling repetitions to run (default: 100)",
    )
    parser.add_argument(
        "--amplitude-damp",
        type=_probability,
        default=0.4,
        help="amplitude damping gamma in [0, 1] (default: 0.4)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1234,
        help="integer random seed for deterministic sampling (default: 1234)",
    )
    return parser


def run_demo(repetitions: int, amplitude_damp: float, seed: int) -> int:
    import cirq

    q = cirq.NamedQubit("q")
    circuit = cirq.Circuit(
        cirq.measure(q, key="initial_state"),
        cirq.X(q),
        cirq.measure(q, key="after_not_gate"),
    )
    noise = cirq.ConstantQubitNoiseModel(cirq.amplitude_damp(amplitude_damp))
    result = cirq.sample(program=circuit, noise=noise, repetitions=repetitions, seed=seed)

    initial_counts = result.histogram(key="initial_state")
    after_counts = result.histogram(key="after_not_gate")

    print("Cirq noisy one-qubit sampling smoke")
    print(f"repetitions: {repetitions}")
    print(f"amplitude_damp: {amplitude_damp}")
    print(f"seed: {seed}")
    print("circuit:")
    print(circuit)
    print(f"noise: {noise!r}")
    print(f"histogram initial_state: {_format_counter(initial_counts)}")
    print(f"histogram after_not_gate: {_format_counter(after_counts)}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return run_demo(
        repetitions=args.repetitions,
        amplitude_damp=args.amplitude_damp,
        seed=args.seed,
    )


if __name__ == "__main__":
    raise SystemExit(main())
