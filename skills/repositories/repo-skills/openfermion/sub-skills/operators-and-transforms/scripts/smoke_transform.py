#!/usr/bin/env python3
"""Map a deterministic two-mode hopping operator and optionally make a sparse matrix.

This helper intentionally uses only public OpenFermion APIs and tiny inputs. It
is safe to run from any working directory and performs no network or file I/O.
"""

from __future__ import annotations

import argparse

def _term_text(operator) -> str:
    """Return stable, concise text for an operator's nonzero term dictionary."""
    if not operator.terms:
        return "0"
    items = sorted(operator.terms.items(), key=lambda item: repr(item[0]))
    return "; ".join(f"{term!r}: {coefficient!r}" for term, coefficient in items)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize and map a tiny two-mode FermionOperator hopping term."
    )
    parser.add_argument(
        "--mapping",
        choices=("jw", "bk", "binary"),
        default="jw",
        help="Mapping to apply: Jordan-Wigner, standard Bravyi-Kitaev, or JW BinaryCode.",
    )
    parser.add_argument(
        "--n-qubits",
        type=int,
        default=None,
        help="Optional padded count for BK/sparse output; must be at least 2.",
    )
    parser.add_argument(
        "--sparse",
        action="store_true",
        help="Also print the tiny SciPy sparse matrix shape.",
    )
    return parser


def main() -> int:
    """Run the deterministic smoke transformation."""
    parser = _build_parser()
    args = parser.parse_args()
    if args.n_qubits is not None and args.n_qubits < 2:
        parser.error("--n-qubits must be at least 2 for this two-mode fixture")

    try:
        from openfermion import (
            FermionOperator,
            binary_code_transform,
            bravyi_kitaev,
            count_qubits,
            get_sparse_operator,
            hermitian_conjugated,
            jordan_wigner,
            jordan_wigner_code,
            normal_ordered,
        )
    except ImportError as exc:
        parser.exit(2, f"OpenFermion import failed: {exc}\\n")
    if args.mapping == "binary" and args.n_qubits not in (None, 2):
        parser.error("the fixed two-mode BinaryCode mapping cannot be padded")

    hopping = FermionOperator("0^ 1", 0.5)
    hopping += hermitian_conjugated(hopping)
    normalized = normal_ordered(hopping)

    if args.mapping == "jw":
        mapped = jordan_wigner(normalized)
    elif args.mapping == "bk":
        mapped = bravyi_kitaev(normalized, n_qubits=args.n_qubits)
    else:
        mapped = binary_code_transform(normalized, jordan_wigner_code(2))

    print(f"normalized_terms={_term_text(normalized)}")
    print(f"mapping={args.mapping} mapped_terms={_term_text(mapped)}")
    if args.sparse:
        matrix_qubits = args.n_qubits or count_qubits(mapped)
        matrix = get_sparse_operator(mapped, n_qubits=matrix_qubits)
        print(f"sparse_shape={matrix.shape} format={matrix.format}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
