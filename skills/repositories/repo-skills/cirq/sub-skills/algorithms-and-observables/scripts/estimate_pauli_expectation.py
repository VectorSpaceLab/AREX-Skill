#!/usr/bin/env python3
"""Compute a tiny deterministic Pauli expectation with public Cirq APIs.

This helper is intentionally self-contained: it uses only an installed Cirq
package plus NumPy, creates either |00> or a Bell state, evaluates a small
PauliString or PauliSum, and exits non-zero if the result differs from the
known expectation.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    import cirq
except ImportError as exc:  # pragma: no cover - exercised only without Cirq.
    raise SystemExit(
        "Cirq is not importable. Install cirq before running this helper."
    ) from exc


@dataclass(frozen=True)
class ObservableSpec:
    label: str
    observable: Any
    expected_by_state: dict[str, complex]
    measurement_compatible: bool


def build_state(state_name: str, seed: int):
    q0, q1 = cirq.LineQubit.range(2)
    qubits = [q0, q1]
    if state_name == "zero":
        circuit = cirq.Circuit()
    elif state_name == "bell":
        circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    else:  # pragma: no cover - argparse enforces choices.
        raise ValueError(f"Unknown state {state_name!r}")

    result = cirq.Simulator(seed=seed).simulate(circuit, qubit_order=qubits)
    return qubits, circuit, result.final_state_vector.astype(np.complex128, copy=False), result.qubit_map


def build_observable(name: str, qubits: list[cirq.Qid]) -> ObservableSpec:
    q0, q1 = qubits
    specs = {
        "zz": ObservableSpec(
            label="Z(q0)*Z(q1)",
            observable=cirq.Z(q0) * cirq.Z(q1),
            expected_by_state={"zero": 1 + 0j, "bell": 1 + 0j},
            measurement_compatible=True,
        ),
        "xx": ObservableSpec(
            label="X(q0)*X(q1)",
            observable=cirq.X(q0) * cirq.X(q1),
            expected_by_state={"zero": 0 + 0j, "bell": 1 + 0j},
            measurement_compatible=True,
        ),
        "zi": ObservableSpec(
            label="Z(q0)",
            observable=cirq.Z(q0),
            expected_by_state={"zero": 1 + 0j, "bell": 0 + 0j},
            measurement_compatible=True,
        ),
        "sum": ObservableSpec(
            label="Z(q0)*Z(q1) + 0.5*X(q0)*X(q1)",
            observable=cirq.Z(q0) * cirq.Z(q1) + 0.5 * cirq.X(q0) * cirq.X(q1),
            expected_by_state={"zero": 1 + 0j, "bell": 1.5 + 0j},
            measurement_compatible=False,
        ),
    }
    return specs[name]


def complex_to_json(value: complex) -> dict[str, float]:
    return {"real": float(np.real(value)), "imag": float(np.imag(value))}


def format_complex(value: complex) -> str:
    real = float(np.real(value))
    imag = float(np.imag(value))
    if abs(imag) < 1e-12:
        return f"{real:.12g}"
    sign = "+" if imag >= 0 else "-"
    return f"{real:.12g}{sign}{abs(imag):.12g}j"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute a known Pauli expectation on |00> or a Bell state using "
            "Cirq.PauliString/PauliSum public APIs."
        )
    )
    parser.add_argument(
        "--state",
        choices=("zero", "bell"),
        default="bell",
        help="Prepared two-qubit state: |00> or (|00> + |11>) / sqrt(2).",
    )
    parser.add_argument(
        "--observable",
        choices=("zz", "xx", "zi", "sum"),
        default="zz",
        help=(
            "Observable to evaluate: zz=Z0Z1, xx=X0X1, zi=Z0, "
            "sum=Z0Z1 + 0.5*X0X1."
        ),
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=1e-7,
        help="Absolute tolerance for validation.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1234,
        help="Deterministic simulator seed. The default is stable.",
    )
    parser.add_argument(
        "--skip-preconditions",
        action="store_true",
        help="Pass check_preconditions=False to the expectation API.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a compact JSON result instead of human-readable text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    qubits, circuit, state_vector, qubit_map = build_state(args.state, args.seed)
    spec = build_observable(args.observable, qubits)

    value = spec.observable.expectation_from_state_vector(
        state_vector,
        qubit_map,
        atol=args.atol,
        check_preconditions=not args.skip_preconditions,
    )
    expected = spec.expected_by_state[args.state]
    passed = bool(abs(value - expected) <= args.atol)

    measurement_op = None
    if spec.measurement_compatible:
        measurement_op = str(cirq.measure_single_paulistring(spec.observable, key="obs"))

    payload = {
        "state": args.state,
        "observable": args.observable,
        "observable_label": spec.label,
        "expectation": complex_to_json(complex(value)),
        "expected": complex_to_json(complex(expected)),
        "atol": args.atol,
        "passed": passed,
        "qubit_order": [str(q) for q in qubits],
        "qubit_map": {str(k): int(v) for k, v in qubit_map.items()},
        "measurement_operation": measurement_op,
    }

    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print("Cirq Pauli expectation smoke check")
        print(f"state: {args.state}")
        print(f"circuit: {circuit if len(circuit) else 'empty circuit for |00>'}")
        print(f"qubit_order: {[str(q) for q in qubits]}")
        print(f"qubit_map: {payload['qubit_map']}")
        print(f"observable: {spec.label}")
        print(f"expectation: {format_complex(complex(value))}")
        print(f"expected: {format_complex(complex(expected))}")
        if measurement_op is not None:
            print(f"equivalent measurement op: {measurement_op}")
        print("status: PASS" if passed else "status: FAIL")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
