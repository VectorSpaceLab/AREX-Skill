#!/usr/bin/env python3
"""Run safe local PyQuil installation and capability checks.

This helper performs no network calls, starts no QVM/quilc process, reads no QCS
credentials, and writes no files. It checks distribution metadata, imports, a
small Program serialization, an in-process PyQVM/reference simulation, a tiny
processor/noise model, and optional LaTeX source generation.

Examples:
    python scripts/check_pyquil_install.py --help
    python scripts/check_pyquil_install.py
"""

from __future__ import annotations

import argparse
import importlib.metadata
import shutil
import sys
from typing import Any


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-latex",
        action="store_true",
        help="skip the optional pyquil.latex source-generation check",
    )
    return parser


def _bell_program() -> Any:
    from pyquil import Program
    from pyquil.gates import CNOT, H, MEASURE

    program = Program()
    readout = program.declare("ro", "BIT", 2)
    program += [H(0), CNOT(0, 1), MEASURE(0, readout[0]), MEASURE(1, readout[1])]
    program.wrap_in_numshots_loop(4)
    return program


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        version = importlib.metadata.version("pyquil")
        import pyquil

        print(f"pyquil {version}: {pyquil.__file__}")
        program = _bell_program()
        quil = program.out()
        if "DECLARE ro BIT[2]" not in quil or "CNOT 0 1" not in quil:
            raise AssertionError("Bell Program serialization did not contain expected Quil")
        print("Program serialization: PASS")

        from pyquil.pyqvm import PyQVM
        from pyquil.simulation import ReferenceWavefunctionSimulator
        from pyquil.gates import CNOT, H

        gate_program = pyquil.Program(H(0), CNOT(0, 1))
        reference = ReferenceWavefunctionSimulator(n_qubits=2)
        reference.do_program(gate_program)
        expected = 2**-0.5
        if abs(abs(reference.wf[0]) - expected) > 1e-9 or abs(abs(reference.wf[3]) - expected) > 1e-9:
            raise AssertionError("reference Bell-state amplitudes were unexpected")
        local_qvm = PyQVM(n_qubits=2, seed=11)
        if local_qvm.wf_simulator is None:
            raise AssertionError("PyQVM did not initialize a simulator")
        print(f"In-process simulation: PASS ({type(local_qvm.wf_simulator).__name__})")

        import networkx as nx
        from pyquil.noise import decoherence_noise_with_asymmetric_ro
        from pyquil.quantum_processor import NxQuantumProcessor

        processor = NxQuantumProcessor(nx.Graph([(0, 1)]))
        isa = processor.to_compiler_isa()
        noise_model = decoherence_noise_with_asymmetric_ro(isa)
        if len(isa.qubits) != 2 or len(isa.edges) != 1 or not noise_model.gates:
            raise AssertionError("processor/noise capability check returned incomplete metadata")
        print("Processor and noise model construction: PASS")

        if not args.skip_latex:
            from pyquil.latex import to_latex

            latex = to_latex(gate_program)
            if "documentclass" not in latex:
                raise AssertionError("LaTeX source did not contain a document header")
            print("LaTeX source generation: PASS")

        print(f"Optional local services: quilc={shutil.which('quilc') or 'not-found'}, qvm={shutil.which('qvm') or 'not-found'}")
        print("No compiler, QVM, QPU, QCS, credentials, or external service was contacted.")
        return 0
    except Exception as exc:  # noqa: BLE001 - diagnostic helper needs a concise actionable error
        print(f"PyQuil local check FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("Use the routed troubleshooting reference; do not infer service or QPU availability from this failure.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
