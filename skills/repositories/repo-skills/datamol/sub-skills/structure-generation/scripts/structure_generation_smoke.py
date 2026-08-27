#!/usr/bin/env python3
"""Deterministic smoke check for datamol structure-generation APIs."""

import argparse
import json
import sys


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run tiny local datamol structure-generation operations and print JSON."
    )
    parser.add_argument(
        "--smiles",
        default="CC(=O)Oc1ccccc1C(=O)O",
        help="Input SMILES for conformer and scaffold checks.",
    )
    parser.add_argument(
        "--reaction-smarts",
        default="[C:1](=[O:2])O.[N:3]>>[C:1](=[O:2])[N:3]",
        help="Reaction SMARTS used for the tiny reaction check.",
    )
    parser.add_argument(
        "--reactant-a",
        default="CC(=O)O",
        help="First reaction reactant SMILES.",
    )
    parser.add_argument(
        "--reactant-b",
        default="NCC",
        help="Second reaction reactant SMILES.",
    )
    parser.add_argument(
        "--num-confs",
        type=int,
        default=3,
        help="Small number of conformers to generate.",
    )
    parser.add_argument(
        "--stereo-smiles",
        default="CC=CC",
        help="SMILES used for stereoisomer counting.",
    )
    return parser


def mol_to_smiles_list(dm, values):
    smiles = []
    for value in values:
        if isinstance(value, (list, tuple)):
            smiles.extend(mol_to_smiles_list(dm, value))
        elif isinstance(value, str):
            smiles.append(value)
        elif value is not None:
            converted = dm.to_smiles(value, allow_to_fail=True)
            if converted:
                smiles.append(converted)
    return sorted({item for item in smiles if item})


def run(args):
    try:
        import datamol as dm
    except Exception as exc:  # pragma: no cover - environment dependent
        raise SystemExit(f"Unable to import datamol: {exc}") from exc

    mol = dm.to_mol(args.smiles)
    if mol is None:
        raise SystemExit(f"Invalid --smiles: {args.smiles}")

    mol3d = dm.conformers.generate(
        mol,
        n_confs=args.num_confs,
        minimize_energy=False,
        rms_cutoff=None,
        random_seed=19,
        num_threads=1,
    )
    scaffold = dm.to_scaffold_murcko(mol)
    fragments = dm.fragment.anybreak(mol, remove_parent=True)

    rxn = dm.reactions.rxn_from_smarts(args.reaction_smarts)
    reactants = (dm.to_mol(args.reactant_a), dm.to_mol(args.reactant_b))
    if any(reactant is None for reactant in reactants):
        raise SystemExit("Invalid reaction reactant SMILES")
    products = dm.reactions.apply_reaction(
        rxn,
        reactants=reactants,
        product_index=0,
        single_product_group=False,
        as_smiles=True,
        sanitize=True,
    )

    stereo_mol = dm.to_mol(args.stereo_smiles)
    if stereo_mol is None:
        raise SystemExit(f"Invalid --stereo-smiles: {args.stereo_smiles}")
    stereo_count = dm.count_stereoisomers(stereo_mol, undefined_only=True, precise=False)

    result = {
        "input_smiles": dm.to_smiles(mol),
        "conformer_count": mol3d.GetNumConformers(),
        "scaffold_smiles": dm.to_smiles(scaffold, allow_to_fail=True),
        "fragment_count": len(fragments),
        "reaction_ok": dm.reactions.is_reaction_ok(rxn),
        "reaction_products": mol_to_smiles_list(dm, products),
        "stereoisomer_count": int(stereo_count),
    }
    print(json.dumps(result, sort_keys=True))


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.num_confs < 1 or args.num_confs > 20:
        parser.error("--num-confs must be between 1 and 20 for this smoke script")
    run(args)


if __name__ == "__main__":
    main()
