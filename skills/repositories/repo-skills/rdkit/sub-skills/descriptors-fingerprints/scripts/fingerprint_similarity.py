#!/usr/bin/env python3
"""Small RDKit Morgan fingerprint similarity helper.

Accepts a tiny list of SMILES, reports invalid inputs, and prints either a
query-vs-library top-k ranking or an all-pairs Tanimoto table.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from typing import Iterable



@dataclass(frozen=True)
class FingerprintRow:
    index: int
    input_smiles: str
    canonical_smiles: str
    fingerprint: object


@dataclass(frozen=True)
class InvalidRow:
    index: int
    input_smiles: str
    error: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate Morgan generator fingerprints and Tanimoto similarities for small SMILES lists.",
    )
    parser.add_argument(
        "--smiles",
        nargs="+",
        required=True,
        help="Library SMILES strings. Quote shell-special characters.",
    )
    parser.add_argument(
        "--query",
        help="Optional query SMILES. If omitted, all valid --smiles entries are compared pairwise.",
    )
    parser.add_argument("--radius", type=int, default=2, help="Morgan fingerprint radius. Default: 2.")
    parser.add_argument("--fp-size", type=int, default=2048, help="Morgan fingerprint bit length. Default: 2048.")
    parser.add_argument("--top-k", type=int, default=5, help="Maximum hits to print for query search. Default: 5.")
    parser.add_argument(
        "--include-chirality",
        action="store_true",
        help="Include chirality in Morgan fingerprints.",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Write machine-readable CSV to stdout instead of aligned text.",
    )
    parser.add_argument(
        "--fail-on-invalid",
        action="store_true",
        help="Exit with status 2 if any input SMILES is invalid.",
    )
    return parser


def parse_and_fingerprint(smiles_values: Iterable[str], generator, chem) -> tuple[list[FingerprintRow], list[InvalidRow]]:
    valid_rows: list[FingerprintRow] = []
    invalid_rows: list[InvalidRow] = []
    for index, smiles in enumerate(smiles_values):
        mol = chem.MolFromSmiles(smiles)
        if mol is None:
            invalid_rows.append(InvalidRow(index=index, input_smiles=smiles, error="invalid SMILES"))
            continue
        valid_rows.append(
            FingerprintRow(
                index=index,
                input_smiles=smiles,
                canonical_smiles=chem.MolToSmiles(mol),
                fingerprint=generator.GetFingerprint(mol),
            )
        )
    return valid_rows, invalid_rows


def parse_query(query_smiles: str, generator, chem) -> tuple[FingerprintRow | None, InvalidRow | None]:
    valid_rows, invalid_rows = parse_and_fingerprint([query_smiles], generator, chem)
    if invalid_rows:
        return None, invalid_rows[0]
    return valid_rows[0], None


def query_scores(query: FingerprintRow, library: list[FingerprintRow], top_k: int) -> list[tuple[FingerprintRow, float]]:
    from rdkit import DataStructs

    scores = DataStructs.BulkTanimotoSimilarity(query.fingerprint, [row.fingerprint for row in library])
    ranked = sorted(zip(library, scores), key=lambda item: (-item[1], item[0].index))
    return ranked[: max(top_k, 0)]


def pairwise_scores(rows: list[FingerprintRow]) -> list[tuple[FingerprintRow, FingerprintRow, float]]:
    results: list[tuple[FingerprintRow, FingerprintRow, float]] = []
    for left_pos, left in enumerate(rows):
        for right in rows[left_pos + 1 :]:
            from rdkit import DataStructs

            score = DataStructs.TanimotoSimilarity(left.fingerprint, right.fingerprint)
            results.append((left, right, score))
    return results


def write_invalid(invalid_rows: list[InvalidRow], csv_mode: bool) -> None:
    if not invalid_rows:
        return
    if csv_mode:
        writer = csv.DictWriter(sys.stderr, fieldnames=["record_type", "index", "input_smiles", "error"])
        writer.writeheader()
        for row in invalid_rows:
            writer.writerow(
                {
                    "record_type": "invalid",
                    "index": row.index,
                    "input_smiles": row.input_smiles,
                    "error": row.error,
                }
            )
    else:
        print("Invalid inputs:", file=sys.stderr)
        for row in invalid_rows:
            print(f"  [{row.index}] {row.input_smiles!r}: {row.error}", file=sys.stderr)


def print_query_results(query: FingerprintRow, ranked: list[tuple[FingerprintRow, float]], csv_mode: bool) -> None:
    if csv_mode:
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=[
                "rank",
                "query_smiles",
                "library_index",
                "library_input_smiles",
                "library_canonical_smiles",
                "tanimoto",
            ],
        )
        writer.writeheader()
        for rank, (row, score) in enumerate(ranked, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "query_smiles": query.input_smiles,
                    "library_index": row.index,
                    "library_input_smiles": row.input_smiles,
                    "library_canonical_smiles": row.canonical_smiles,
                    "tanimoto": f"{score:.6f}",
                }
            )
        return

    print(f"Query: {query.input_smiles} ({query.canonical_smiles})")
    print("rank  index  tanimoto  canonical_smiles  input_smiles")
    for rank, (row, score) in enumerate(ranked, start=1):
        print(f"{rank:>4}  {row.index:>5}  {score:>8.4f}  {row.canonical_smiles:<18}  {row.input_smiles}")


def print_pairwise_results(results: list[tuple[FingerprintRow, FingerprintRow, float]], csv_mode: bool) -> None:
    if csv_mode:
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=["left_index", "right_index", "left_smiles", "right_smiles", "tanimoto"],
        )
        writer.writeheader()
        for left, right, score in results:
            writer.writerow(
                {
                    "left_index": left.index,
                    "right_index": right.index,
                    "left_smiles": left.canonical_smiles,
                    "right_smiles": right.canonical_smiles,
                    "tanimoto": f"{score:.6f}",
                }
            )
        return

    print("left  right  tanimoto  left_smiles         right_smiles")
    for left, right, score in results:
        print(f"{left.index:>4}  {right.index:>5}  {score:>8.4f}  {left.canonical_smiles:<18}  {right.canonical_smiles}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.fp_size <= 0:
        print("--fp-size must be positive", file=sys.stderr)
        return 2
    if args.radius < 0:
        print("--radius must be non-negative", file=sys.stderr)
        return 2

    try:
        from rdkit import Chem
        from rdkit.Chem import rdFingerprintGenerator
    except ImportError as exc:
        print(f"RDKit is required to calculate fingerprints: {exc}", file=sys.stderr)
        return 1

    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=args.radius,
        fpSize=args.fp_size,
        includeChirality=args.include_chirality,
    )
    library, invalid_rows = parse_and_fingerprint(args.smiles, generator, Chem)

    query = None
    if args.query is not None:
        query, invalid_query = parse_query(args.query, generator, Chem)
        if invalid_query is not None:
            invalid_rows = [invalid_query, *invalid_rows]

    write_invalid(invalid_rows, args.csv)
    if args.fail_on_invalid and invalid_rows:
        return 2
    if not library:
        print("No valid library SMILES were provided.", file=sys.stderr)
        return 2
    if args.query is not None and query is None:
        print("Query SMILES is invalid; no similarities calculated.", file=sys.stderr)
        return 2

    if query is not None:
        print_query_results(query, query_scores(query, library, args.top_k), args.csv)
    else:
        print_pairwise_results(pairwise_scores(library), args.csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
