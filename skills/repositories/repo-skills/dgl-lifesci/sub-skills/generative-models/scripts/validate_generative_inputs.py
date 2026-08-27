#!/usr/bin/env python3
"""Validate small DGL-LifeSci generative-model SMILES and vocabulary fixtures."""

import argparse
import sys
from collections import Counter
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Validate one-SMILES-per-line fixtures for DGMG/JTVAE planning and "
            "optionally compare a supplied JTVAE vocabulary against MolTree-derived tokens."
        )
    )
    parser.add_argument("--smiles-file", required=True, help="Text file with one SMILES token per line.")
    parser.add_argument("--vocab-file", help="Optional JTVAE vocabulary file with one token SMILES per line.")
    parser.add_argument(
        "--derive-jtvae-vocab",
        action="store_true",
        help="Derive JTVAE MolTree vocabulary tokens from checked SMILES and compare to --vocab-file when supplied.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Maximum number of non-empty SMILES rows to validate.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow empty lines in input files instead of treating them as errors.",
    )
    parser.add_argument(
        "--show-examples",
        type=int,
        default=10,
        help="Maximum number of example errors/tokens to print per category.",
    )
    return parser.parse_args()


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def import_rdkit():
    try:
        from rdkit import Chem
    except Exception as exc:  # pragma: no cover - environment-specific
        raise RuntimeError(f"failed to import RDKit: {exc}") from exc
    return Chem


def import_moltree():
    try:
        from dgllife.utils.jtvae.mol_tree import MolTree
    except Exception as exc:  # pragma: no cover - environment-specific
        raise RuntimeError(f"failed to import DGL-LifeSci JTVAE MolTree utilities: {exc}") from exc
    return MolTree


def read_token_lines(path, max_rows=None, allow_empty=False, label="file"):
    tokens = []
    empty_rows = []
    with path.open("r", encoding="utf-8") as handle:
        for row_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if stripped == "":
                if not allow_empty:
                    empty_rows.append(row_number)
                continue
            token = stripped.split()[0]
            tokens.append({"row_number": row_number, "token": token})
            if max_rows is not None and len(tokens) >= max_rows:
                break
    if not tokens:
        raise ValueError(f"{label} has no non-empty token rows")
    return tokens, empty_rows


def count_duplicates(items):
    counts = Counter(item["token"] for item in items)
    return {token: count for token, count in counts.items() if count > 1}


def validate_smiles(Chem, items):
    valid = []
    invalid = []
    atom_types = set()
    bond_types = set()
    canonical_counts = Counter()

    for item in items:
        row_number = item["row_number"]
        smiles = item["token"]
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            invalid.append((row_number, smiles, "RDKit could not parse SMILES"))
            continue
        canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
        canonical_counts[canonical] += 1
        for atom in mol.GetAtoms():
            atom_types.add(atom.GetSymbol())
        for bond in mol.GetBonds():
            bond_types.add(str(bond.GetBondType()))
        valid.append({"row_number": row_number, "smiles": smiles, "canonical": canonical, "mol": mol})

    canonical_duplicates = {smiles: count for smiles, count in canonical_counts.items() if count > 1}
    return valid, invalid, sorted(atom_types), sorted(bond_types), canonical_duplicates


def derive_jtvae_tokens(MolTree, valid_smiles):
    derived = set()
    failures = []
    for item in valid_smiles:
        row_number = item["row_number"]
        smiles = item["smiles"]
        try:
            mol_tree = MolTree(smiles)
        except Exception as exc:  # pragma: no cover - dependency-specific error type
            failures.append((row_number, smiles, f"MolTree construction failed: {exc}"))
            continue
        if not mol_tree.nodes_dict:
            failures.append((row_number, smiles, "MolTree produced no vocabulary nodes"))
            continue
        for node in mol_tree.nodes_dict.values():
            token = node.get("smiles")
            if token:
                derived.add(token)
    return derived, failures


def print_examples(prefix, values, limit, stream=sys.stdout):
    for value in list(values)[:limit]:
        print(f"{prefix}: {value}", file=stream)
    if len(values) > limit:
        print(f"{prefix}: ... {len(values) - limit} more", file=stream)


def main():
    args = parse_args()
    if args.max_rows is not None and args.max_rows <= 0:
        return fail("--max-rows must be positive when provided")
    if args.show_examples < 0:
        return fail("--show-examples must be non-negative")
    if args.derive_jtvae_vocab and args.vocab_file is None:
        print("NOTE: deriving JTVAE tokens without --vocab-file; coverage comparison will be skipped.")

    smiles_path = Path(args.smiles_file)
    if not smiles_path.is_file():
        return fail(f"SMILES file does not exist: {smiles_path}")
    vocab_path = Path(args.vocab_file) if args.vocab_file else None
    if vocab_path is not None and not vocab_path.is_file():
        return fail(f"vocabulary file does not exist: {vocab_path}")

    try:
        Chem = import_rdkit()
    except RuntimeError as exc:
        return fail(str(exc))

    try:
        smiles_items, empty_smiles_rows = read_token_lines(
            smiles_path,
            max_rows=args.max_rows,
            allow_empty=args.allow_empty,
            label="SMILES file",
        )
    except (OSError, ValueError) as exc:
        return fail(str(exc))

    vocab_items = []
    empty_vocab_rows = []
    if vocab_path is not None:
        try:
            vocab_items, empty_vocab_rows = read_token_lines(
                vocab_path,
                allow_empty=args.allow_empty,
                label="vocabulary file",
            )
        except (OSError, ValueError) as exc:
            return fail(str(exc))

    valid_smiles, invalid_smiles, atom_types, bond_types, canonical_duplicates = validate_smiles(Chem, smiles_items)
    raw_smiles_duplicates = count_duplicates(smiles_items)

    invalid_vocab = []
    vocab_duplicates = {}
    vocab_set = set()
    if vocab_items:
        valid_vocab, invalid_vocab, _, _, _ = validate_smiles(Chem, vocab_items)
        vocab_duplicates = count_duplicates(vocab_items)
        vocab_set = {item["smiles"] for item in valid_vocab}

    derived_tokens = set()
    moltree_failures = []
    missing_vocab_tokens = set()
    unused_vocab_tokens = set()
    if args.derive_jtvae_vocab:
        try:
            MolTree = import_moltree()
        except RuntimeError as exc:
            return fail(str(exc))
        derived_tokens, moltree_failures = derive_jtvae_tokens(MolTree, valid_smiles)
        if vocab_set:
            missing_vocab_tokens = derived_tokens.difference(vocab_set)
            unused_vocab_tokens = vocab_set.difference(derived_tokens)

    print(f"smiles_file: {smiles_path}")
    print(f"smiles_rows_checked: {len(smiles_items)}")
    print(f"valid_smiles: {len(valid_smiles)}")
    print(f"invalid_smiles: {len(invalid_smiles)}")
    print(f"raw_duplicate_smiles: {len(raw_smiles_duplicates)}")
    print(f"canonical_duplicate_smiles: {len(canonical_duplicates)}")
    print(f"atom_types: {', '.join(atom_types) if atom_types else '(none)'}")
    print(f"bond_types: {', '.join(bond_types) if bond_types else '(none)'}")

    if vocab_path is not None:
        print(f"vocab_file: {vocab_path}")
        print(f"vocab_tokens_checked: {len(vocab_items)}")
        print(f"invalid_vocab_tokens: {len(invalid_vocab)}")
        print(f"duplicate_vocab_tokens: {len(vocab_duplicates)}")

    if args.derive_jtvae_vocab:
        print(f"jtvae_derived_tokens: {len(derived_tokens)}")
        print(f"jtvae_moltree_failures: {len(moltree_failures)}")
        if vocab_set:
            print(f"jtvae_missing_vocab_tokens: {len(missing_vocab_tokens)}")
            print(f"jtvae_unused_vocab_tokens: {len(unused_vocab_tokens)}")

    if args.show_examples:
        print_examples("empty_smiles_row", empty_smiles_rows, args.show_examples, sys.stderr)
        print_examples("empty_vocab_row", empty_vocab_rows, args.show_examples, sys.stderr)
        for row_number, smiles, reason in invalid_smiles[: args.show_examples]:
            print(f"invalid_smiles_row: row={row_number} smiles={smiles!r} reason={reason}", file=sys.stderr)
        for row_number, token, reason in invalid_vocab[: args.show_examples]:
            print(f"invalid_vocab_row: row={row_number} token={token!r} reason={reason}", file=sys.stderr)
        for token, count in list(raw_smiles_duplicates.items())[: args.show_examples]:
            print(f"duplicate_smiles: token={token!r} count={count}", file=sys.stderr)
        for token, count in list(vocab_duplicates.items())[: args.show_examples]:
            print(f"duplicate_vocab_token: token={token!r} count={count}", file=sys.stderr)
        for token, count in list(canonical_duplicates.items())[: args.show_examples]:
            print(f"canonical_duplicate_smiles: smiles={token!r} count={count}", file=sys.stderr)
        for row_number, smiles, reason in moltree_failures[: args.show_examples]:
            print(f"jtvae_moltree_failure: row={row_number} smiles={smiles!r} reason={reason}", file=sys.stderr)
        print_examples("jtvae_missing_vocab_token", sorted(missing_vocab_tokens), args.show_examples, sys.stderr)
        print_examples("jtvae_unused_vocab_token", sorted(unused_vocab_tokens), args.show_examples, sys.stderr)

    has_errors = any(
        [
            empty_smiles_rows,
            empty_vocab_rows,
            invalid_smiles,
            invalid_vocab,
            moltree_failures,
            missing_vocab_tokens,
        ]
    )
    if has_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
