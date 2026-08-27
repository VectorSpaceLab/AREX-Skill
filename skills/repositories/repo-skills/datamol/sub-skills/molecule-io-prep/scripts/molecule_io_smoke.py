#!/usr/bin/env python3
"""Tiny datamol molecule IO/prep smoke check."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a deterministic datamol molecule construction, dataframe, and SDF roundtrip smoke check.",
    )
    parser.add_argument(
        "--input-smiles",
        default="CCO",
        help="Input SMILES to parse and roundtrip. Default: CCO.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory where tiny CSV and SDF outputs are written. A temporary directory is used if omitted.",
    )
    parser.add_argument(
        "--keep-output",
        action="store_true",
        help="Keep the temporary directory when --output-dir is omitted and print its path.",
    )
    return parser


def run_smoke(input_smiles: str, output_dir: Path) -> dict[str, Any]:
    import datamol as dm

    mol = dm.to_mol(input_smiles)
    if mol is None:
        raise ValueError(f"Could not parse --input-smiles: {input_smiles!r}")

    canonical_smiles = dm.to_smiles(mol)
    if canonical_smiles is None:
        raise ValueError("datamol failed to convert parsed molecule back to SMILES")

    mol = dm.set_mol_props(mol, {"source": "molecule_io_smoke", "canonical": canonical_smiles}, copy=True)
    dataframe = dm.to_df([mol], smiles_column="smiles", mol_column="mol")
    dataframe_mols = dm.from_df(dataframe, mol_column="mol")
    assert len(dataframe_mols) == 1
    assert dm.to_smiles(dataframe_mols[0]) == canonical_smiles
    assert dataframe_mols[0].GetPropsAsDict()["source"] == "molecule_io_smoke"

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "molecule_io_smoke.csv"
    sdf_path = output_dir / "molecule_io_smoke.sdf"

    dm.save_df(dataframe.drop(columns=["mol"]), str(csv_path))
    csv_roundtrip = dm.open_df(str(csv_path))
    assert csv_roundtrip.loc[0, "smiles"] == canonical_smiles

    sdf_frame = dataframe.drop(columns=["smiles"])
    dm.to_sdf(sdf_frame, str(sdf_path), mol_column="mol")
    sdf_roundtrip = dm.read_sdf(
        str(sdf_path),
        as_df=True,
        smiles_column="roundtrip_smiles",
        mol_column="mol",
    )
    assert len(sdf_roundtrip) == 1
    assert sdf_roundtrip.loc[0, "roundtrip_smiles"] == canonical_smiles
    assert dm.to_smiles(sdf_roundtrip.loc[0, "mol"]) == canonical_smiles
    assert sdf_roundtrip.loc[0, "source"] == "molecule_io_smoke"

    neutral = dm.to_smiles(dm.to_neutral(dm.copy_mol(mol)))
    assert neutral is not None

    return {
        "input_smiles": input_smiles,
        "canonical_smiles": canonical_smiles,
        "num_atoms": mol.GetNumAtoms(),
        "csv_path": str(csv_path),
        "sdf_path": str(sdf_path),
        "dataframe_columns": list(dataframe.columns),
        "neutral_smiles": neutral,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.output_dir is not None:
        summary = run_smoke(args.input_smiles, args.output_dir)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    with tempfile.TemporaryDirectory(prefix="datamol-molecule-io-smoke-") as temp_dir:
        summary = run_smoke(args.input_smiles, Path(temp_dir))
        if args.keep_output:
            keep_dir = Path.cwd() / Path(temp_dir).name
            keep_dir.mkdir(parents=True, exist_ok=False)
            for source_path in Path(temp_dir).iterdir():
                source_path.replace(keep_dir / source_path.name)
            summary["csv_path"] = str(keep_dir / "molecule_io_smoke.csv")
            summary["sdf_path"] = str(keep_dir / "molecule_io_smoke.sdf")
            summary["kept_output_dir"] = str(keep_dir)
        else:
            summary.pop("csv_path", None)
            summary.pop("sdf_path", None)
            summary["temporary_output_removed"] = True
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
