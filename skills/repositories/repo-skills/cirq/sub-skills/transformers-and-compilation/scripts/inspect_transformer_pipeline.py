#!/usr/bin/env python3
"""Inspect a tiny Cirq transformer/target-gateset pipeline offline.

This helper is intentionally local and deterministic: it builds a small circuit,
runs a few public Cirq transformer passes, compiles to a selected target gateset,
and checks unitary equivalence. It never contacts provider services.
"""

from __future__ import annotations

import argparse
import collections
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import cirq


def build_circuit() -> cirq.Circuit:
    """Return a tiny measurement-free circuit suitable for unitary comparison."""
    q0, q1 = cirq.LineQubit.range(2)
    return cirq.Circuit(
        cirq.Moment([cirq.H(q0)]),
        cirq.Moment(),
        cirq.Moment([cirq.CNOT(q0, q1)]),
        cirq.Moment([cirq.Z(q0) ** 0.25, cirq.X(q1) ** 0.5]),
        cirq.Moment([cirq.CZ(q0, q1) ** 0.5]),
        cirq.Moment([cirq.Y(q0) ** -0.25]),
    )


def choose_gateset(target: str, atol: float) -> tuple[Any, str]:
    if target == "cz":
        return cirq.CZTargetGateset(atol=atol), "cirq.CZTargetGateset"
    if target == "sycamore":
        try:
            import cirq_google as cg  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - depends on optional install
            raise SystemExit(
                "--target sycamore requires the optional cirq_google package; "
                "rerun with --target cz or install cirq-google."
            ) from exc
        return cg.SycamoreTargetGateset(atol=atol), "cirq_google.SycamoreTargetGateset"
    raise ValueError(f"Unknown target: {target}")


def operation_histogram(circuit: cirq.AbstractCircuit) -> collections.Counter[str]:
    counts: collections.Counter[str] = collections.Counter()
    for op in circuit.all_operations():
        gate = op.gate
        counts[type(gate).__name__ if gate is not None else type(op).__name__] += 1
    return counts


def format_histogram(circuit: cirq.AbstractCircuit) -> str:
    counts = operation_histogram(circuit)
    if not counts:
        return "<empty>"
    return ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))


def compile_circuit(args: argparse.Namespace) -> tuple[cirq.Circuit, cirq.Circuit, Any, str, cirq.TransformerContext]:
    gateset, gateset_name = choose_gateset(args.target, args.atol)
    logger = cirq.TransformerLogger() if args.show_logger else None
    context = cirq.TransformerContext(logger=logger) if logger else cirq.TransformerContext()

    original = build_circuit()
    cleaned = cirq.drop_empty_moments(original, context=context)
    cleaned = cirq.eject_z(cleaned, context=context, atol=args.atol)
    cleaned = cirq.merge_single_qubit_gates_to_phxz(cleaned, context=context, atol=args.atol)

    compiled = cirq.optimize_for_target_gateset(
        cleaned,
        context=context,
        gateset=gateset,
        ignore_failures=False,
        max_num_passes=args.max_passes,
    )
    return cleaned, compiled, gateset, gateset_name, context


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect an offline Cirq transformer pipeline on a tiny circuit."
    )
    parser.add_argument(
        "--target",
        choices=("cz", "sycamore"),
        default="cz",
        help="Target gateset for optimize_for_target_gateset. Sycamore requires cirq_google.",
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=1e-8,
        help="Absolute tolerance for target gateset compilation and equivalence checks.",
    )
    parser.add_argument(
        "--max-passes",
        type=int,
        default=1,
        help="Maximum optimize_for_target_gateset passes to run.",
    )
    parser.add_argument(
        "--show-logger",
        action="store_true",
        help="Print Cirq TransformerLogger details after compilation.",
    )
    args = parser.parse_args(argv)

    global cirq
    try:
        import cirq as _cirq
    except ImportError:
        print(
            "This helper requires the cirq Python package. Install Cirq in the current "
            "environment, then rerun the script.",
            file=sys.stderr,
        )
        return 2
    cirq = _cirq

    original = build_circuit()
    print("Target:", args.target)
    print("Original circuit:")
    print(original)
    print("Original ops:", format_histogram(original))
    print()

    cleaned, compiled, gateset, gateset_name, context = compile_circuit(args)
    print("After built-in cleanup pipeline:")
    print(cleaned)
    print("Cleaned ops:", format_histogram(cleaned))
    print()

    print(f"After optimize_for_target_gateset using {gateset_name}:")
    print(compiled)
    print("Compiled ops:", format_histogram(compiled))
    print()

    unsupported = [op for op in compiled.all_operations() if op not in gateset]
    if unsupported:
        print("Unsupported operations remain:", file=sys.stderr)
        for op in unsupported:
            print(f"  {op!r}", file=sys.stderr)
        return 1
    print("Gateset membership: ok")

    equivalent = cirq.linalg.allclose_up_to_global_phase(
        cirq.unitary(original), cirq.unitary(compiled), atol=args.atol
    )
    print("Unitary equivalence up to global phase:", "ok" if equivalent else "FAILED")
    if args.show_logger:
        print()
        print("Transformer log:")
        context.logger.show()
    return 0 if equivalent else 1


if __name__ == "__main__":
    raise SystemExit(main())
