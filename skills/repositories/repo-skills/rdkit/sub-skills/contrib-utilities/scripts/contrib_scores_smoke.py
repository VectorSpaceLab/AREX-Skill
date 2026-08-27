#!/usr/bin/env python3
"""Report availability of optional RDKit Contrib SA/NP scorers."""

from __future__ import annotations

import argparse
import importlib
import json
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Parse small SMILES with RDKit and report whether optional "
            "Contrib SA Score and NP Score utilities are importable and usable."
        )
    )
    parser.add_argument(
        "--smiles",
        nargs="+",
        default=["CCO", "c1ccccc1O"],
        help="SMILES strings to parse for the smoke check.",
    )
    parser.add_argument(
        "--sa-data",
        help="Optional explicit SA Score fpscores.pkl.gz path for sascorer.readFragmentScores().",
    )
    parser.add_argument(
        "--np-model",
        help="Optional explicit NP Score publicnp.model.gz path for npscorer.readNPModel().",
    )
    return parser.parse_args()


def status(name: str, available: bool, detail: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"name": name, "available": available, "detail": detail}
    if extra:
        result.update(extra)
    return result


def check_rdkit(smiles: list[str]) -> tuple[dict[str, Any], list[Any]]:
    try:
        from rdkit import Chem, rdBase
    except Exception as err:  # pragma: no cover - depends on environment
        return status("rdkit", False, f"import failed: {err}"), []

    mols = []
    invalid = []
    canonical = []
    for item in smiles:
        mol = Chem.MolFromSmiles(item)
        if mol is None:
            invalid.append(item)
        else:
            mols.append(mol)
            canonical.append(Chem.MolToSmiles(mol, isomericSmiles=True))

    if invalid:
        return status(
            "rdkit",
            False,
            "one or more SMILES failed to parse",
            {"version": rdBase.rdkitVersion, "invalid_smiles": invalid, "canonical_smiles": canonical},
        ), mols

    return status(
        "rdkit",
        True,
        "imported and parsed input molecules",
        {"version": rdBase.rdkitVersion, "canonical_smiles": canonical},
    ), mols


def check_sa_score(mols: list[Any], data_path: str | None) -> dict[str, Any]:
    try:
        sascorer = importlib.import_module("sascorer")
    except Exception as err:
        return status("sa_score", False, f"sascorer import failed: {err}")

    try:
        if data_path:
            sascorer.readFragmentScores(data_path)
        values = [round(float(sascorer.calculateScore(mol)), 4) for mol in mols]
    except Exception as err:
        return status("sa_score", False, f"scorer present but data/scoring failed: {err}")

    return status("sa_score", True, "scored molecules", {"scores": values})


def check_np_score(mols: list[Any], model_path: str | None) -> dict[str, Any]:
    try:
        npscorer = importlib.import_module("npscorer")
    except Exception as err:
        return status("np_score", False, f"npscorer import failed: {err}")

    try:
        model = npscorer.readNPModel(model_path) if model_path else npscorer.readNPModel()
        values = []
        for mol in mols:
            scored = npscorer.scoreMolWConfidence(mol, model)
            values.append(
                {
                    "nplikeness": round(float(scored.nplikeness), 4),
                    "confidence": round(float(scored.confidence), 4),
                }
            )
    except Exception as err:
        return status("np_score", False, f"scorer present but model/scoring failed: {err}")

    return status("np_score", True, "scored molecules", {"scores": values})


def main() -> int:
    args = parse_args()
    rdkit_status, mols = check_rdkit(args.smiles)
    results = [rdkit_status]

    if rdkit_status["available"]:
        results.append(check_sa_score(mols, args.sa_data))
        results.append(check_np_score(mols, args.np_model))

    print(json.dumps({"checks": results}, indent=2, sort_keys=True))
    return 0 if rdkit_status["available"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
