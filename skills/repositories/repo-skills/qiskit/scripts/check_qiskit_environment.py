#!/usr/bin/env python3
"""Source-free smoke checks for a Qiskit installation.

The script exercises a small, representative slice of the public package:
core imports, transpilation, primitives, serialization, visualization,
providers, and the public C API. Use ``--sections`` to narrow the checks and
``--json`` for machine-readable output.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")


SECTIONS = [
    "core",
    "transpiler",
    "primitives",
    "serialization",
    "quantum-info",
    "visualization",
    "providers",
    "capi",
]


@dataclass
class SectionResult:
    status: str
    message: str
    details: dict[str, object] | None = None


def _ok(message: str, **details: object) -> SectionResult:
    return SectionResult("passed", message, details or None)


def _skip(message: str, **details: object) -> SectionResult:
    return SectionResult("skipped", message, details or None)


def _fail(message: str, **details: object) -> SectionResult:
    return SectionResult("failed", message, details or None)


def _section_core() -> SectionResult:
    import qiskit
    from qiskit import QuantumCircuit
    from qiskit.circuit import ClassicalRegister, QuantumRegister

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return _ok(
        "core imports succeeded",
        version=qiskit.__version__,
        circuit_qubits=qc.num_qubits,
        registers=[QuantumRegister.__name__, ClassicalRegister.__name__],
    )


def _section_transpiler() -> SectionResult:
    from qiskit import QuantumCircuit
    from qiskit.providers.fake_provider import GenericBackendV2
    from qiskit.transpiler import generate_preset_pass_manager

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    backend = GenericBackendV2(num_qubits=2, seed=123)
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    transpiled = pm.run(qc)
    return _ok(
        "preset pass manager transpilation succeeded",
        transpiled_ops=dict(transpiled.count_ops()),
        backend_name=backend.name,
    )


def _section_primitives() -> SectionResult:
    from qiskit import QuantumCircuit
    from qiskit.primitives import StatevectorEstimator, StatevectorSampler
    from qiskit.quantum_info import SparsePauliOp

    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])

    sampler = StatevectorSampler(seed=123)
    sample_result = sampler.run([qc], shots=128).result()[0]
    sample_key = next(iter(sample_result.data.keys()))
    counts = sample_result.data[sample_key].get_counts()

    estimator = StatevectorEstimator()
    circ = QuantumCircuit(1)
    circ.h(0)
    evs = estimator.run([(circ, SparsePauliOp("Z"))]).result()[0].data.evs
    evs_value = evs.tolist()
    if isinstance(evs_value, list):
        evs_summary = [float(x) for x in evs_value]
    else:
        evs_summary = [float(evs_value)]
    return _ok(
        "primitive sampling and estimation succeeded",
        sampler_counts=dict(sorted(counts.items())),
        estimator_evs=evs_summary,
    )


def _section_serialization() -> SectionResult:
    from qiskit import QuantumCircuit, qasm2, qasm3, qpy
    from qiskit.utils import optionals

    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])

    qasm2_text = qasm2.dumps(qc)
    if qasm2.loads(qasm2_text) != qc:
        return _fail("QASM2 round-trip failed")

    qpy_buffer = io.BytesIO()
    qpy.dump(qc, qpy_buffer)
    qpy_buffer.seek(0)
    if qpy.load(qpy_buffer)[0] != qc:
        return _fail("QPY round-trip failed")

    details: dict[str, object] = {
        "qasm2_length": len(qasm2_text),
        "qpy_version": qpy.get_qpy_version(io.BytesIO(qpy_buffer.getvalue())),
    }

    if optionals.HAS_QASM3_IMPORT:
        qasm3_text = qasm3.dumps(qc)
        if qasm3.loads(qasm3_text) != qc:
            return _fail("OpenQASM 3 round-trip failed")
        details["qasm3_length"] = len(qasm3_text)
    else:
        details["qasm3"] = "skipped: qiskit-qasm3-import not installed"

    return _ok("serialization round-trips succeeded", **details)


def _section_quantum_info() -> SectionResult:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Operator, SparsePauliOp, Statevector, random_unitary

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    state = Statevector.from_circuit(qc)
    op = Operator.from_circuit(qc)
    observable = SparsePauliOp.from_list([("ZZ", 1), ("XX", 1)])
    unitary = random_unitary(2, seed=123)
    return _ok(
        "quantum-info objects constructed",
        state_dim=state.dim,
        operator_dim=op.dim,
        observable_terms=len(observable),
        random_unitary_dim=unitary.dim,
    )


def _section_visualization() -> SectionResult:
    from qiskit import QuantumCircuit
    from qiskit.visualization import circuit_drawer

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    text_draw = circuit_drawer(qc, output="text")

    try:
        from matplotlib.figure import Figure
        from qiskit.visualization import plot_histogram
    except Exception as exc:  # pragma: no cover - import error is an explicit skip
        return _skip(
            f"matplotlib or plotting helpers not available: {exc}",
            text_type=type(text_draw).__name__,
        )

    fig = plot_histogram({"0": 1, "1": 1})
    if not isinstance(fig, Figure):
        return _fail("plot_histogram did not return a matplotlib Figure")
    return _ok(
        "visualization helpers succeeded",
        text_type=type(text_draw).__name__,
        figure_type=type(fig).__name__,
    )


def _section_providers() -> SectionResult:
    from qiskit import QuantumCircuit
    from qiskit.providers.basic_provider import BasicProvider
    from qiskit.providers.fake_provider import GenericBackendV2
    from qiskit.transpiler import generate_preset_pass_manager

    provider = BasicProvider()
    backend = provider.get_backend("basic_simulator")

    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    basic_counts = backend.run(qc).result().get_counts()

    fake = GenericBackendV2(num_qubits=2, seed=123)
    pm = generate_preset_pass_manager(backend=fake, optimization_level=1)
    transpiled = pm.run(qc)
    fake_counts = fake.run(transpiled, shots=128, seed_simulator=123).result().get_counts()

    return _ok(
        "provider and fake-backend execution succeeded",
        provider=str(provider),
        backend_name=backend.name,
        basic_counts=basic_counts,
        fake_counts=fake_counts,
    )


def _section_capi() -> SectionResult:
    from qiskit import capi

    include = Path(capi.get_include())
    lib = Path(capi.get_lib())
    if not include.exists():
        return _fail("C API include directory does not exist", include=str(include))
    if not lib.exists():
        return _fail("C API shared library does not exist", library=str(lib))
    return _ok("C API paths resolved", include=str(include), library=str(lib))


SECTION_HANDLERS = {
    "core": _section_core,
    "transpiler": _section_transpiler,
    "primitives": _section_primitives,
    "serialization": _section_serialization,
    "quantum-info": _section_quantum_info,
    "visualization": _section_visualization,
    "providers": _section_providers,
    "capi": _section_capi,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sections",
        nargs="*",
        choices=SECTIONS,
        default=SECTIONS,
        help="Sections to run (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary instead of a human-readable report",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results: dict[str, SectionResult] = {}

    try:
        import qiskit  # noqa: F401
    except Exception as exc:
        print(f"core import failed before section execution: {exc}", file=sys.stderr)
        return 2

    for name in args.sections:
        try:
            results[name] = SECTION_HANDLERS[name]()
        except Exception as exc:  # pragma: no cover - intentionally surfaced in CLI output
            results[name] = _fail(f"{name} section raised {exc.__class__.__name__}: {exc}")

    exit_code = 0 if all(result.status != "failed" for result in results.values()) else 1

    if args.json:
        payload = {
            "sections": {name: asdict(result) for name, result in results.items()},
            "exit_code": exit_code,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for name in args.sections:
            result = results[name]
            print(f"[{name}] {result.status}: {result.message}")
            if result.details:
                for key, value in result.details.items():
                    print(f"  - {key}: {value}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
