#!/usr/bin/env python3
"""Smoke-check ProLIF plotting imports and optional LigNetwork HTML export."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any


def import_status(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - report optional backend failures as JSON
        return {"ok": False, "error": type(exc).__name__, "message": str(exc)}
    return {"ok": True, "module": getattr(imported, "__name__", module)}


def build_tiny_network(output_html: Path | None, overwrite: bool) -> dict[str, Any]:
    import prolif as plf
    from rdkit import Chem
    from rdkit.Chem.rdDistGeom import EmbedMolecule

    from prolif.plotting.network import LigNetwork

    ligand = Chem.AddHs(Chem.MolFromSmiles("c1ccccc1"))
    protein = Chem.AddHs(Chem.MolFromSequence("F"), addResidueInfo=True)
    if ligand is None or protein is None:
        raise RuntimeError("RDKit failed to create tiny smoke molecules")
    EmbedMolecule(ligand, randomSeed=0xAC1D)
    EmbedMolecule(protein, randomSeed=0xAC1D)

    lig_mol = plf.Molecule.from_rdkit(ligand, resname="LIG", resnumber=1)
    prot_mol = plf.Molecule.from_rdkit(protein, resname="PHE", resnumber=1, chain="A")
    fp = plf.Fingerprint(["Hydrophobic", "PiStacking"])
    fp.run_from_iterable([lig_mol], prot_mol, progress=False)

    frame_count = len(fp.ifp)
    interaction_count = sum(
        len(interactions)
        for frame_ifp in fp.ifp.values()
        for interactions in frame_ifp.values()
    )
    result: dict[str, Any] = {
        "ran_tiny_fingerprint": True,
        "frames": frame_count,
        "interaction_groups": interaction_count,
        "wrote_html": False,
    }

    if output_html is not None:
        if output_html.exists() and not overwrite:
            raise FileExistsError(
                f"Refusing to overwrite existing file: {output_html}. Use --overwrite."
            )
        output_html.parent.mkdir(parents=True, exist_ok=True)
        net = LigNetwork.from_fingerprint(
            fp,
            lig_mol,
            kind="frame",
            frame=0,
            display_all=False,
        )
        net.save(output_html)
        result.update(
            {
                "wrote_html": True,
                "output_html": str(output_html),
                "output_size_bytes": output_html.stat().st_size,
            }
        )

    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check ProLIF plotting optional imports, optionally run a tiny installed-"
            "package fingerprint, and optionally save a LigNetwork HTML file."
        )
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Check plotting and optional backend imports.",
    )
    parser.add_argument(
        "--run-tiny",
        action="store_true",
        help="Run a tiny RDKit-backed ProLIF fingerprint before plotting.",
    )
    parser.add_argument(
        "--output-html",
        type=Path,
        help="Write a LigNetwork HTML file for the tiny fingerprint.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing --output-html file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.output_html is not None and not args.run_tiny:
        args.run_tiny = True
    if not args.check_imports and not args.run_tiny:
        args.check_imports = True

    payload: dict[str, Any] = {"ok": True, "imports": {}, "tiny": None}
    try:
        if args.check_imports:
            modules = [
                "prolif",
                "prolif.plotting.network",
                "prolif.plotting.barcode",
                "prolif.plotting.complex3d",
                "prolif.plotting.residues",
                "matplotlib",
                "py3Dmol",
                "IPython.display",
            ]
            payload["imports"] = {module: import_status(module) for module in modules}
        if args.run_tiny:
            payload["tiny"] = build_tiny_network(args.output_html, args.overwrite)
    except Exception as exc:  # noqa: BLE001 - top-level JSON error contract
        payload["ok"] = False
        payload["error"] = type(exc).__name__
        payload["message"] = str(exc)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
