#!/usr/bin/env python3
"""Inspect ProLIF molecule inputs and print a JSON report."""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any


def status_ok(data: dict[str, Any] | list[Any]) -> dict[str, Any]:
    return {"ok": True, "data": data}


def status_error(exc: BaseException) -> dict[str, Any]:
    return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def residue_preview(mol: Any, limit: int) -> list[str]:
    try:
        return [str(residue.resid) for residue in list(mol)[:limit]]
    except Exception:
        return []


def molecule_summary(mol: Any, limit: int) -> dict[str, Any]:
    return {
        "class": type(mol).__name__,
        "atoms": int(mol.GetNumAtoms()),
        "residues": int(getattr(mol, "n_residues", len(getattr(mol, "residues", [])))),
        "residue_preview": residue_preview(mol, limit),
    }


def supplier_summary(supplier: Any, limit: int) -> dict[str, Any]:
    summary: dict[str, Any] = {"class": type(supplier).__name__}
    try:
        summary["pose_count"] = len(supplier)
    except Exception as exc:
        summary["pose_count_error"] = f"{type(exc).__name__}: {exc}"
    poses: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index in range(limit):
        try:
            poses.append({"index": index, **molecule_summary(supplier[index], limit)})
        except IndexError:
            break
        except Exception as exc:
            errors.append({"index": index, "error": f"{type(exc).__name__}: {exc}"})
            break
    summary["pose_preview"] = poses
    if errors:
        summary["pose_errors"] = errors
    return summary


def inspect_sdf(path: str, limit: int) -> dict[str, Any]:
    try:
        import prolif as plf

        supplier = plf.sdf_supplier(path)
        return status_ok(supplier_summary(supplier, limit))
    except Exception as exc:
        return status_error(exc)


def inspect_mol2(path: str, limit: int) -> dict[str, Any]:
    try:
        import prolif as plf

        supplier = plf.mol2_supplier(path)
        return status_ok(supplier_summary(supplier, limit))
    except Exception as exc:
        return status_error(exc)


def build_template(args: argparse.Namespace) -> tuple[Any | None, dict[str, Any]]:
    info: dict[str, Any] = {"source": None}
    if args.pdbqt_template_smiles:
        try:
            from rdkit import Chem

            template = Chem.MolFromSmiles(args.pdbqt_template_smiles)
            if template is None:
                raise ValueError("RDKit returned None for --pdbqt-template-smiles")
            info.update({"source": "smiles", "atoms": int(template.GetNumAtoms())})
            return template, info
        except Exception as exc:
            info.update(status_error(exc))
            return None, info
    if args.pdbqt_template_sdf:
        try:
            from rdkit import Chem

            supplier = Chem.SDMolSupplier(args.pdbqt_template_sdf, removeHs=False)
            template = supplier[0]
            if template is None:
                raise ValueError("first SDF molecule is None")
            info.update({"source": "sdf", "atoms": int(template.GetNumAtoms())})
            return template, info
        except Exception as exc:
            info.update(status_error(exc))
            return None, info
    info["required"] = "Provide --pdbqt-template-smiles or --pdbqt-template-sdf to instantiate pdbqt_supplier."
    return None, info


def inspect_pdbqt(paths: list[str], args: argparse.Namespace, limit: int) -> dict[str, Any]:
    existing = [str(Path(path)) for path in paths if Path(path).exists()]
    missing = [str(Path(path)) for path in paths if not Path(path).exists()]
    template, template_info = build_template(args)
    data: dict[str, Any] = {
        "requested_paths": [str(Path(path)) for path in paths],
        "existing_count": len(existing),
        "missing_paths": missing,
        "template": template_info,
    }
    if template is None:
        data["supplier"] = {"ok": False, "skipped": "pdbqt_supplier requires a template molecule"}
        return status_ok(data)
    try:
        import prolif as plf

        supplier = plf.pdbqt_supplier(existing, template)
        data["supplier"] = supplier_summary(supplier, limit)
        return status_ok(data)
    except Exception as exc:
        data["supplier"] = status_error(exc)
        return status_ok(data)


def package_data_smoke(limit: int) -> dict[str, Any]:
    report: dict[str, Any] = {}
    try:
        import prolif as plf

        report["prolif"] = {"ok": True, "version": getattr(plf, "__version__", "unknown")}
    except Exception as exc:
        return {"prolif": status_error(exc)}

    try:
        from rdkit import Chem, rdBase

        report["rdkit"] = {"ok": True, "version": getattr(rdBase, "rdkitVersion", "unknown")}
        report["rdkit_smiles"] = {"ok": Chem.MolFromSmiles("CCO") is not None}
    except Exception as exc:
        report["rdkit"] = status_error(exc)

    try:
        import MDAnalysis as mda

        report["mdanalysis"] = {"ok": True, "version": getattr(mda, "__version__", "unknown")}
    except Exception as exc:
        report["mdanalysis"] = status_error(exc)

    try:
        import MDAnalysis as mda
        import prolif as plf

        universe = mda.Universe(plf.datafiles.TOP, plf.datafiles.TRAJ)
        ligand = universe.select_atoms("resname LIG")
        protein = universe.select_atoms("protein and byres around 6.5 group ligand", ligand=ligand)
        ligand_mol = plf.Molecule.from_mda(ligand)
        protein_mol = plf.Molecule.from_mda(protein)
        report["package_mda_molecules"] = status_ok(
            {
                "ligand_atoms": int(ligand.n_atoms),
                "protein_atoms": int(protein.n_atoms),
                "ligand_molecule": molecule_summary(ligand_mol, limit),
                "protein_molecule": molecule_summary(protein_mol, limit),
            }
        )
    except Exception as exc:
        report["package_mda_molecules"] = status_error(exc)

    try:
        import prolif as plf

        vina = Path(plf.datafiles.datapath) / "vina"
        report["package_sdf_supplier"] = inspect_sdf(str(vina / "vina_output.sdf"), limit)
        report["package_mol2_supplier"] = inspect_mol2(str(vina / "vina_output.mol2"), limit)
    except Exception as exc:
        report["package_suppliers"] = status_error(exc)

    try:
        from rdkit import Chem
        import prolif as plf

        vina = Path(plf.datafiles.datapath) / "vina"
        pdbqt_paths = sorted(glob.glob(str(vina / "*.pdbqt")))
        template = Chem.MolFromSmiles(
            "C[NH+]1CC(C(=O)NC2(C)OC3(O)C4CCCN4C(=O)"
            "C(Cc4ccccc4)N3C2=O)C=C2c3cccc4[nH]cc(c34)CC21"
        )
        if template is None:
            raise ValueError("package-data PDBQT template SMILES could not be parsed")
        report["package_pdbqt_supplier"] = status_ok(
            supplier_summary(plf.pdbqt_supplier(pdbqt_paths, template), limit)
        )
    except Exception as exc:
        report["package_pdbqt_supplier"] = status_error(exc)

    try:
        from prolif.io import MoleculeStandardizer, cif_template_reader
        import prolif as plf

        template_path = Path(plf.datafiles.datapath) / "molecule_standardizer" / "templates" / "TPO.cif"
        template_doc = cif_template_reader(template_path)
        standardizer = MoleculeStandardizer(templates=[template_doc])
        report["standardizer"] = status_ok(
            {
                "template_blocks": len(template_doc),
                "engine_count": len(standardizer.engines),
                "has_tpo": "TPO" in standardizer.engines,
            }
        )
    except Exception as exc:
        report["standardizer"] = status_error(exc)

    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect ProLIF package data or user SDF/MOL2/PDBQT inputs and print JSON."
    )
    parser.add_argument("--sdf", action="append", default=[], help="SDF file to inspect; may be repeated.")
    parser.add_argument("--mol2", action="append", default=[], help="MOL2 file to inspect; may be repeated.")
    parser.add_argument("--pdbqt", action="append", default=[], help="PDBQT file to inspect; may be repeated.")
    parser.add_argument("--pdbqt-template-smiles", help="SMILES template for PDBQT bond orders and charges.")
    parser.add_argument("--pdbqt-template-sdf", help="SDF file whose first molecule is the PDBQT template.")
    parser.add_argument("--max-items", type=int, default=3, help="Maximum poses/residues to preview per input.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    limit = max(0, args.max_items)
    report: dict[str, Any] = {"mode": "package-data-smoke", "inputs": {}}

    if args.sdf or args.mol2 or args.pdbqt:
        report["mode"] = "user-input-probe"
        report["inputs"]["sdf"] = {path: inspect_sdf(path, limit) for path in args.sdf}
        report["inputs"]["mol2"] = {path: inspect_mol2(path, limit) for path in args.mol2}
        if args.pdbqt:
            report["inputs"]["pdbqt"] = inspect_pdbqt(args.pdbqt, args, limit)
    else:
        report["inputs"] = package_data_smoke(limit)

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
