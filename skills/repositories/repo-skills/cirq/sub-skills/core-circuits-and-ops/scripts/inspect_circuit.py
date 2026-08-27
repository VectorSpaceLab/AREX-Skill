#!/usr/bin/env python3
"""Build and inspect a small parameterized Cirq circuit.

The script is deterministic, local-only, and intended as a quick smoke helper
for the core-circuits-and-ops sub-skill. It does not run a simulator, contact
network services, or read an original repository checkout.
"""

from __future__ import annotations

import argparse
from collections import Counter
import sys

try:
    import cirq
    import sympy
except ImportError as exc:  # pragma: no cover - depends on caller environment.
    raise SystemExit(f"Missing dependency: {exc}. Install Cirq in the active Python environment.")


def build_circuit(num_qubits: int) -> tuple[cirq.Circuit, sympy.Symbol]:
    """Return a small parameterized circuit with explicit measurement keys."""

    qubits = cirq.LineQubit.range(num_qubits)
    theta = sympy.Symbol("theta")
    circuit = cirq.Circuit()

    circuit.append(cirq.H(qubits[0]))
    if num_qubits == 1:
        circuit.append(cirq.X(qubits[0]) ** theta)
    else:
        for control, target in zip(qubits, qubits[1:]):
            circuit.append(cirq.CNOT(control, target))
        circuit.append(cirq.Z(qubits[-1]) ** theta)

    measurements = [cirq.measure(q, key=f"m{i}") for i, q in enumerate(qubits)]
    circuit.append(measurements, strategy=cirq.InsertStrategy.NEW_THEN_INLINE)
    return circuit, theta


def duplicate_measurement_keys(circuit: cirq.Circuit) -> dict[str, list[str]]:
    """Return measurement keys that occur in more than one measurement op."""

    counts: Counter[str] = Counter()
    locations: dict[str, list[str]] = {}
    for moment_index, op in circuit.findall_operations(cirq.is_measurement):
        for key in sorted(str(k) for k in cirq.measurement_key_names(op)):
            counts[key] += 1
            locations.setdefault(key, []).append(f"moment {moment_index}: {op!r}")
    return {key: locations[key] for key, count in counts.items() if count > 1}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a small parameterized Cirq circuit, print text diagrams, "
            "validate measurement-key uniqueness, and optionally JSON roundtrip it."
        )
    )
    parser.add_argument(
        "--qubits",
        type=int,
        default=2,
        help="Number of line qubits to include, from 1 to 8. Default: 2.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Roundtrip the parameterized circuit through cirq.to_json/read_json.",
    )
    parser.add_argument(
        "--allow-duplicate-keys",
        action="store_true",
        help="Report but do not fail if duplicate measurement keys are found.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not 1 <= args.qubits <= 8:
        raise SystemExit("--qubits must be between 1 and 8")

    circuit, theta = build_circuit(args.qubits)

    print("Parameterized circuit:")
    print(circuit.to_text_diagram())
    print()

    parameter_names = sorted(cirq.parameter_names(circuit))
    print("Unresolved parameters:", ", ".join(parameter_names) or "none")
    print("Measurement keys:", ", ".join(sorted(circuit.all_measurement_key_names())) or "none")

    duplicates = duplicate_measurement_keys(circuit)
    if duplicates:
        print("Duplicate measurement keys detected:")
        for key, locs in duplicates.items():
            print(f"  {key}:")
            for loc in locs:
                print(f"    {loc}")
        if not args.allow_duplicate_keys:
            return 2
    else:
        print("Measurement key uniqueness: ok")

    resolver = cirq.ParamResolver({str(theta): 0.25})
    resolved = cirq.resolve_parameters(circuit, resolver)
    print()
    print("Resolved circuit with theta=0.25:")
    print(resolved.to_text_diagram())

    unitary_prefix = cirq.Circuit(
        op for op in resolved.all_operations() if not cirq.is_measurement(op)
    )
    print()
    print("Non-measurement prefix has unitary:", cirq.has_unitary(unitary_prefix))

    if args.json:
        json_text = cirq.to_json(circuit)
        restored = cirq.read_json(json_text=json_text)
        if restored != circuit:
            raise SystemExit("JSON roundtrip failed: restored circuit differs")
        print("JSON roundtrip: ok")
        print("JSON bytes:", len(json_text.encode("utf-8")))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
