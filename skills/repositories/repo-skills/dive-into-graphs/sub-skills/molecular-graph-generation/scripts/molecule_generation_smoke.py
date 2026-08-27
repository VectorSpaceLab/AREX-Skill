#!/usr/bin/env python3
"""Tiny DIG molecular-generation smoke check.

Uses only in-memory RDKit molecules and small tensors. No downloads.
"""
import argparse
import json

import torch
from rdkit import Chem

from dig.ggraph.evaluation import ConstPropOptEvaluator, PropOptEvaluator, RandGenEvaluator
from dig.ggraph.utils import check_chemical_validity, check_valency, gen_mol_from_one_shot_tensor


def tiny_one_shot_mols():
    adj = torch.zeros(2, 4, 5, 5)
    x = torch.zeros(2, 10, 5)
    # sample 1: methane-like single atom
    x[0, 0, 0] = 1
    # sample 2: water-like 3 atoms with a single bond pattern in channel 0
    x[1, 0, 0] = 1
    x[1, 1, 1] = 1
    x[1, 2, 2] = 1
    adj[1, 0, 1] = adj[1, 1, 0] = 1
    adj[1, 1, 2] = adj[1, 2, 1] = 1
    atomic_num_list = [6, 7, 8, 9, 15, 16, 17, 35, 53, 0]
    return gen_mol_from_one_shot_tensor(adj, x, atomic_num_list)


def main():
    parser = argparse.ArgumentParser(description="Tiny DIG molecular-generation smoke check.")
    parser.parse_args()

    mols = [Chem.MolFromSmiles(s) for s in ["C", "N", "O"]]
    rand_eval = RandGenEvaluator()
    prop_eval = PropOptEvaluator()
    const_eval = ConstPropOptEvaluator()

    tiny = tiny_one_shot_mols()
    validity = [bool(m and check_chemical_validity(m) and check_valency(m)) for m in tiny]

    rand = rand_eval.eval({"mols": mols, "train_smiles": [Chem.MolToSmiles(m) for m in mols]})
    prop = prop_eval.eval({"mols": mols})
    const = const_eval.eval({
        "mols_0": mols,
        "mols_2": mols,
        "mols_4": mols,
        "mols_6": mols,
        "inp_smiles": [Chem.MolToSmiles(m) for m in mols],
    })

    print(json.dumps({
        "validity": validity,
        "rand": rand,
        "prop": prop,
        "const_keys": sorted(const.keys()),
        "tiny_count": len(tiny),
    }, indent=2, sort_keys=True))
    print("molecule_generation_smoke: ok")


if __name__ == "__main__":
    main()
