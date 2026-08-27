#!/usr/bin/env python3
"""Report RDKit chemical features for SMILES using an installed RDKit package."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Iterable


_DELIMITERS = {
    "space": " ",
    "tab": "\t",
    "comma": ",",
}


def default_fdef_path(rd_config) -> str:
    return os.path.join(rd_config.RDDataDir, "BaseFeatures.fdef")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Annotate SMILES with RDKit chemical features from an FDef file.",
    )
    parser.add_argument(
        "--smiles",
        nargs="*",
        default=[],
        help="SMILES strings to annotate. Use --input for files or '-' for stdin.",
    )
    parser.add_argument(
        "--input",
        help="Optional delimited input file. Use '-' to read from stdin.",
    )
    parser.add_argument(
        "--delimiter",
        choices=sorted(_DELIMITERS),
        default="space",
        help="Delimiter for --input; default: space.",
    )
    parser.add_argument(
        "--smiles-column",
        type=int,
        default=0,
        help="Zero-based SMILES column for --input; default: 0.",
    )
    parser.add_argument(
        "--name-column",
        type=int,
        default=1,
        help="Zero-based name column for --input; ignored when absent; default: 1.",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Treat the first input row as data instead of skipping it as a header.",
    )
    parser.add_argument(
        "--fdef",
        help="Feature definition file; default: RDKit RDDataDir/BaseFeatures.fdef.",
    )
    parser.add_argument(
        "--include-only",
        default="",
        help="Optional feature family filter passed to GetFeaturesForMol.",
    )
    parser.add_argument(
        "--conf-id",
        type=int,
        default=-1,
        help="Conformer id for feature positions; default: -1.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON records instead of tab-separated text.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Also print per-molecule feature counts to stderr.",
    )
    parser.add_argument(
        "--show-env",
        action="store_true",
        help="Print RDKit version, import location, and RDDataDir to stderr.",
    )
    return parser


def input_rows(args: argparse.Namespace) -> Iterable[tuple[int, str, str]]:
    index = 0
    for smiles in args.smiles:
        index += 1
        yield index, f"mol_{index}", smiles

    if not args.input:
        return

    handle = sys.stdin if args.input == "-" else open(args.input, newline="", encoding="utf-8")
    try:
        reader = csv.reader(handle, delimiter=_DELIMITERS[args.delimiter])
        for row_number, row in enumerate(reader, start=1):
            if row_number == 1 and not args.no_header:
                continue
            if not row or args.smiles_column >= len(row):
                print(f"warning: skipped row {row_number}: missing SMILES column", file=sys.stderr)
                continue
            name = row[args.name_column] if args.name_column < len(row) and row[args.name_column] else f"row_{row_number}"
            index += 1
            yield index, name, row[args.smiles_column]
    finally:
        if handle is not sys.stdin:
            handle.close()


def feature_record(index: int, name: str, smiles: str, feature, include_coordinates: bool) -> dict[str, object]:
    coordinates = (None, None, None)
    if include_coordinates:
        try:
            position = feature.GetPos()
            coordinates = (position.x, position.y, position.z)
        except RuntimeError:
            coordinates = (None, None, None)

    return {
        "index": index,
        "name": name,
        "smiles": smiles,
        "family": feature.GetFamily(),
        "type": feature.GetType(),
        "atom_ids": list(feature.GetAtomIds()),
        "x": coordinates[0],
        "y": coordinates[1],
        "z": coordinates[2],
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        from rdkit import Chem, RDConfig, rdBase
        from rdkit.Chem import ChemicalFeatures
    except ImportError as exc:
        print(f"error: RDKit is not importable: {exc}", file=sys.stderr)
        print("hint: run this helper in an environment where the rdkit package is installed", file=sys.stderr)
        return 2

    if args.fdef is None:
        args.fdef = default_fdef_path(RDConfig)

    if args.show_env:
        import rdkit
        print(f"rdkit_version={rdBase.rdkitVersion}", file=sys.stderr)
        print(f"rdkit_module={getattr(rdkit, '__file__', '<unknown>')}", file=sys.stderr)
        print(f"rdkit_data_dir={RDConfig.RDDataDir}", file=sys.stderr)
        print(f"default_fdef={default_fdef_path(RDConfig)}", file=sys.stderr)

    if not os.path.exists(args.fdef):
        print(f"error: feature definition file not found: {args.fdef}", file=sys.stderr)
        print("hint: inspect rdkit.RDConfig.RDDataDir or pass --fdef explicitly", file=sys.stderr)
        return 2

    try:
        factory = ChemicalFeatures.BuildFeatureFactory(args.fdef)
    except Exception as exc:
        print(f"error: could not build feature factory from {args.fdef}: {exc}", file=sys.stderr)
        return 2

    rows = list(input_rows(args))
    if not rows:
        print("error: provide --smiles values or --input", file=sys.stderr)
        return 2

    if not args.json:
        print("index\tname\tsmiles\tfamily\ttype\tatom_ids\tx\ty\tz")

    had_invalid = False
    for index, name, smiles in rows:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            had_invalid = True
            print(f"warning: invalid SMILES at index {index} ({name!r}): {smiles}", file=sys.stderr)
            continue

        features = factory.GetFeaturesForMol(mol, includeOnly=args.include_only, confId=args.conf_id)
        if args.summary:
            print(f"{index}\t{name}\t{len(features)} features", file=sys.stderr)

        for feature in features:
            record = feature_record(index, name, smiles, feature, mol.GetNumConformers() > 0)
            if args.json:
                print(json.dumps(record, sort_keys=True))
            else:
                values = {
                    "index": record["index"],
                    "name": record["name"],
                    "smiles": record["smiles"],
                    "family": record["family"],
                    "type": record["type"],
                    "atom_ids": ",".join(str(atom_id) for atom_id in record["atom_ids"]),
                    "x": "" if record["x"] is None else f"{record['x']:.6g}",
                    "y": "" if record["y"] is None else f"{record['y']:.6g}",
                    "z": "" if record["z"] is None else f"{record['z']:.6g}",
                }
                print("{index}\t{name}\t{smiles}\t{family}\t{type}\t{atom_ids}\t{x}\t{y}\t{z}".format(**values))

    return 1 if had_invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
