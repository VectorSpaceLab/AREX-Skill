#!/usr/bin/env python3
"""Smoke-check public scikit-bio sequence and alignment APIs."""

from __future__ import annotations

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Construct DNA/RNA/Protein objects, align short DNA sequences, "
            "build a TabularMSA, and print a compact JSON summary."
        )
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=None,
        help="Pretty-print JSON with this indentation level.",
    )
    return parser


def run_smoke() -> dict[str, object]:
    try:
        from skbio import DNA, Protein, RNA
        from skbio.alignment import TabularMSA, align_score, pair_align_nucl
    except ImportError as error:
        raise RuntimeError(
            "Unable to import public scikit-bio sequence/alignment APIs. "
            "Install scikit-bio with its runtime dependencies before running this smoke check."
        ) from error

    try:
        dna = DNA(
            "acgtNN--",
            metadata={"id": "dna-smoke"},
            positional_metadata={"quality": [30, 31, 32, 33, 10, 10, 5, 5]},
            lowercase="was_lowercase",
        )
        rna = dna.degap().transcribe()
        protein = RNA("AUGCCACUUUAA").translate(stop="ignore")
        explicit_protein = Protein("MPL*")

        seq1 = DNA("GATCGTC", metadata={"id": "query"})
        seq2 = DNA("ATCGCTC", metadata={"id": "target"})
        result = pair_align_nucl(seq1, seq2)
        if not result.paths:
            raise ValueError("pair_align_nucl returned no alignment path for smoke inputs")
        path = result.paths[0]
        aligned = path.to_aligned((seq1, seq2))
        msa = TabularMSA.from_path_seqs(path, (seq1, seq2))
        checked_score = align_score((path, (seq1, seq2)), sub_score=(2, -3), gap_cost=(5, 2))
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"scikit-bio sequence/alignment validation failed: {error}") from error

    return {
        "dna": {
            "sequence": str(dna),
            "length": len(dna),
            "has_gaps": bool(dna.has_gaps()),
            "has_degenerates": bool(dna.has_degenerates()),
            "lowercase_recorded": int(dna.positional_metadata["was_lowercase"].sum()),
        },
        "rna": str(rna),
        "protein": {
            "translated": str(protein),
            "explicit": str(explicit_protein),
            "matches": str(protein) == str(explicit_protein),
        },
        "alignment": {
            "score": result.score,
            "score_validated": checked_score,
            "cigar": path.to_cigar(),
            "aligned": [str(item) for item in aligned],
        },
        "msa": {
            "sequence_count": msa.shape.sequence,
            "position_count": msa.shape.position,
            "dtype": msa.dtype.__name__,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        summary = run_smoke()
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True, indent=args.indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
