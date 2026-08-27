#!/usr/bin/env python3
"""Check core OpenFermion imports and a tiny public API smoke path.

Run from any working directory with the target environment's Python. This
script is read-only: it performs no network calls, file writes, plugin loading,
or large numerical work.
"""

from __future__ import annotations

import argparse
import importlib
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print a compact JSON result")
    args = parser.parse_args(argv)

    try:
        import openfermion
        from openfermion import FermionOperator, QubitOperator, get_sparse_operator, jordan_wigner
    except ImportError as exc:
        print(f"OpenFermion core import failed: {exc}", file=sys.stderr)
        return 2

    optional = {}
    for name in ("cirq", "numpy", "scipy", "sympy", "h5py"):
        try:
            module = importlib.import_module(name)
            optional[name] = getattr(module, "__version__", "available")
        except ImportError:
            optional[name] = "missing"

    hopping = FermionOperator("0^ 1", 0.5)
    mapped = jordan_wigner(hopping + FermionOperator("1^ 0", 0.5))
    matrix = get_sparse_operator(QubitOperator("Z0"), n_qubits=1)
    result = {
        "openfermion": openfermion.__version__,
        "core_smoke": {
            "fermion_terms": len(hopping.terms),
            "mapped_terms": len(mapped.terms),
            "matrix_shape": list(matrix.shape),
        },
        "optional_runtime_modules": optional,
    }
    if args.json:
        import json
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"openfermion={result['openfermion']}")
        print(f"core_smoke={result['core_smoke']}")
        print(f"optional_runtime_modules={optional}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
