#!/usr/bin/env python3
"""Smoke test RDKit conformer generation and SVG drawing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

Chem: Any = None
AllChem: Any = None
Draw: Any = None
rdBase: Any = None


def _require_rdkit() -> None:
    global Chem, AllChem, Draw, rdBase
    if Chem is not None:
        return
    try:
        from rdkit import Chem as rdkit_chem
        from rdkit import rdBase as rdkit_base
        from rdkit.Chem import AllChem as rdkit_all_chem
        from rdkit.Chem import Draw as rdkit_draw
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "RDKit is not importable in this Python environment; install RDKit or run "
            "with an environment that provides the rdkit package"
        ) from exc
    Chem = rdkit_chem
    AllChem = rdkit_all_chem
    Draw = rdkit_draw
    rdBase = rdkit_base


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a tiny RDKit 3D conformer summary and a 2D SVG drawing. "
            "Defaults to ethanol and writes conformer_smoke.svg."
        )
    )
    parser.add_argument(
        "--smiles",
        default="CCO",
        help="SMILES string to embed and draw (default: CCO).",
    )
    parser.add_argument(
        "--legend",
        default="ethanol",
        help="Legend text for the SVG drawing (default: ethanol).",
    )
    parser.add_argument(
        "--svg-out",
        default="conformer_smoke.svg",
        help="Output SVG path (default: conformer_smoke.svg).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=61453,
        help="Deterministic embedding seed (default: 61453).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the summary as JSON instead of human-readable lines.",
    )
    return parser


def _embed_with_retry(mol: Any, seed: int) -> tuple[Any, str, int]:
    work = Chem.AddHs(Chem.Mol(mol))
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    status = AllChem.EmbedMolecule(work, params)
    if status >= 0:
        return work, "ETKDGv3", status

    retry_params = AllChem.ETKDGv3()
    retry_params.randomSeed = seed
    retry_params.useRandomCoords = True
    retry_params.maxIterations = 1000
    retry_status = AllChem.EmbedMolecule(work, retry_params)
    if retry_status >= 0:
        return work, "ETKDGv3 random-coords retry", retry_status

    raise RuntimeError(
        f"embedding failed: initial status {status}, retry status {retry_status}"
    )


def _optimize(mol: Any) -> tuple[str, int | None]:
    if mol.GetNumConformers() == 0:
        raise ValueError("cannot optimize a molecule without conformers")

    if AllChem.MMFFHasAllMoleculeParams(mol):
        return "MMFF94", AllChem.MMFFOptimizeMolecule(mol, maxIters=200)

    if hasattr(AllChem, "UFFHasAllMoleculeParams") and not AllChem.UFFHasAllMoleculeParams(mol):
        return "none: no MMFF/UFF parameters", None

    return "UFF", AllChem.UFFOptimizeMolecule(mol, maxIters=200)


def _write_svg(mol: Any, legend: str, svg_out: Path) -> int:
    display = Chem.Mol(mol)
    AllChem.Compute2DCoords(display)
    svg = Draw.MolsToGridImage(
        [display],
        legends=[legend],
        molsPerRow=1,
        subImgSize=(280, 220),
        useSVG=True,
    )
    svg_text = str(svg)
    if "<svg" not in svg_text and "<?xml" not in svg_text:
        raise RuntimeError("RDKit did not return SVG markup")
    svg_out.parent.mkdir(parents=True, exist_ok=True)
    svg_out.write_text(svg_text, encoding="utf-8")
    return svg_out.stat().st_size


def run(smiles: str, legend: str, svg_out: Path, seed: int) -> dict[str, object]:
    _require_rdkit()
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"invalid SMILES: {smiles!r}")

    embedded, embed_method, embed_status = _embed_with_retry(mol, seed)
    opt_method, opt_status = _optimize(embedded)
    svg_bytes = _write_svg(mol, legend, svg_out)

    return {
        "rdkit_version": rdBase.rdkitVersion,
        "input_smiles": smiles,
        "canonical_smiles": Chem.MolToSmiles(mol),
        "atoms_with_hydrogens": embedded.GetNumAtoms(),
        "conformers": embedded.GetNumConformers(),
        "embed_method": embed_method,
        "embed_status": embed_status,
        "optimization_method": opt_method,
        "optimization_status": opt_status,
        "svg_out": str(svg_out),
        "svg_bytes": svg_bytes,
    }


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        summary = run(args.smiles, args.legend, Path(args.svg_out), args.seed)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("RDKit conformer/drawing smoke succeeded")
        for key, value in summary.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
