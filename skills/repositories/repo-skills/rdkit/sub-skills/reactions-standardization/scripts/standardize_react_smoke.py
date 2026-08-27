#!/usr/bin/env python3
"""Tiny RDKit MolStandardize plus reaction SMARTS smoke test."""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a tiny RDKit cleanup/fragment-parent and reaction SMARTS smoke test."
    )
    parser.add_argument(
        "--smiles",
        default="CC(=O)[O-].[Na+]",
        help="SMILES to clean and reduce to a fragment parent (default: acetate sodium salt).",
    )
    parser.add_argument(
        "--reactant",
        default="CC=O",
        help="Reactant SMILES for the default carbonyl reduction reaction (default: CC=O).",
    )
    parser.add_argument(
        "--reaction-smarts",
        default="[C:1]=[O:2]>>[C:1][O:2]",
        help="Reaction SMARTS to run against --reactant.",
    )
    parser.add_argument(
        "--bad-reaction",
        action="store_true",
        help="Also try an intentionally invalid reaction SMARTS and report the caught error.",
    )
    return parser


def require_mol(Chem, smiles: str, label: str):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"{label} is not a valid SMILES: {smiles!r}")
    return mol


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        from rdkit import Chem
        from rdkit.Chem import rdChemReactions
        from rdkit.Chem.MolStandardize import rdMolStandardize
    except Exception as exc:
        raise SystemExit(
            "Could not import RDKit. Run this from an environment with an installed RDKit package; "
            "avoid running from an unbuilt RDKit source checkout that shadows compiled modules."
        ) from exc

    mol = require_mol(Chem, args.smiles, "--smiles")
    clean = rdMolStandardize.Cleanup(mol)
    parent = rdMolStandardize.FragmentParent(clean)
    clean_smiles = Chem.MolToSmiles(clean, isomericSmiles=True)
    parent_smiles = Chem.MolToSmiles(parent, isomericSmiles=True)

    try:
        rxn = rdChemReactions.ReactionFromSmarts(args.reaction_smarts)
    except Exception as exc:
        raise SystemExit(f"Invalid reaction SMARTS: {exc}") from exc

    warnings, errors = rxn.Validate()
    if errors:
        raise SystemExit(f"Reaction validation failed: {errors} errors, {warnings} warnings")
    if rxn.GetNumReactantTemplates() != 1:
        raise SystemExit(
            f"Smoke script expects one reactant template; got {rxn.GetNumReactantTemplates()}"
        )

    reactant = require_mol(Chem, args.reactant, "--reactant")
    product_sets = rxn.RunReactants((reactant,))
    if not product_sets:
        raise SystemExit("Reaction produced no products for the supplied reactant")

    product = product_sets[0][0]
    try:
        Chem.SanitizeMol(product)
    except Exception as exc:
        unsanitized = Chem.MolToSmiles(product, isomericSmiles=True, canonical=False)
        raise SystemExit(f"First product failed sanitization ({unsanitized}): {exc}") from exc
    product_smiles = Chem.MolToSmiles(product, isomericSmiles=True)

    print(f"RDKit cleanup: {args.smiles} -> {clean_smiles}")
    print(f"RDKit fragment parent: {parent_smiles}")
    print(f"RDKit reaction product: {args.reactant} -> {product_smiles}")

    if args.bad_reaction:
        try:
            rdChemReactions.ReactionFromSmarts("[C:1]>>[C:1")
        except Exception as exc:
            print(f"Caught expected invalid reaction SMARTS: {exc.__class__.__name__}: {exc}")
        else:
            raise SystemExit("Expected invalid reaction SMARTS to fail, but it parsed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
