#!/usr/bin/env python3
"""Check that datamol and core RDKit-backed APIs work in the current Python."""

import argparse
import json
import sys


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run a small datamol import, RDKit, IO, fingerprint, and rendering capability check."
    )
    parser.add_argument(
        "--smiles",
        default="CCO",
        help="SMILES used for the tiny molecule smoke check. Default: CCO.",
    )
    parser.add_argument(
        "--require-render",
        action="store_true",
        help="Fail if SVG rendering through datamol.viz.to_image is unavailable.",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        import datamol as dm
        from rdkit import Chem, rdBase
    except Exception as exc:
        raise SystemExit(f"Unable to import datamol/RDKit: {exc}") from exc

    mol = dm.to_mol(args.smiles)
    if mol is None:
        raise SystemExit(f"datamol imported, but --smiles could not be parsed: {args.smiles}")

    canonical = dm.to_smiles(mol)
    fp = dm.to_fp(mol, as_array=True)
    dataframe = dm.to_df([mol], smiles_column="smiles", mol_column="mol", render_df_mol=False)
    render_ok = False
    render_error = None
    try:
        image = dm.to_image([mol], legends=[canonical], use_svg=True)
        render_ok = isinstance(image, str) and "<svg" in image.lower()
    except Exception as exc:  # pragma: no cover - optional renderer dependent
        render_error = str(exc)

    if args.require_render and not render_ok:
        raise SystemExit(f"SVG rendering failed: {render_error or 'unknown error'}")

    result = {
        "datamol_version": getattr(dm, "__version__", None),
        "rdkit_version": rdBase.rdkitVersion,
        "canonical_smiles": canonical,
        "num_atoms": mol.GetNumAtoms(),
        "fingerprint_length": int(getattr(fp, "shape", [len(fp)])[0]),
        "dataframe_columns": list(dataframe.columns),
        "render_svg_ok": render_ok,
        "render_error": render_error,
        "rdkit_mol_class": Chem.Mol.__name__,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
