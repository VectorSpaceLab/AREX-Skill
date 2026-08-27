#!/usr/bin/env python3
"""Create or load a tiny CSV and convert it to a DeepChem dataset."""

import argparse
import csv
from pathlib import Path


DEFAULT_ROWS = [
    {"compound_id": "cmpd-ethanol", "smiles": "CCO", "activity": "1.2"},
    {"compound_id": "cmpd-benzene", "smiles": "c1ccccc1", "activity": "0.4"},
    {"compound_id": "cmpd-acetic-acid", "smiles": "CC(=O)O", "activity": "0.8"},
    {"compound_id": "cmpd-cyclohexane", "smiles": "C1CCCCC1", "activity": "0.1"},
]


def write_default_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["compound_id", "smiles", "activity"])
        writer.writeheader()
        writer.writerows(DEFAULT_ROWS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path("tiny_deepchem_data.csv"),
                        help="CSV path to load. Created with tiny demo rows if missing.")
    parser.add_argument("--task", default="activity", help="Label/task column name.")
    parser.add_argument("--feature-field", default="smiles", help="SMILES or feature column name.")
    parser.add_argument("--id-field", default="compound_id", help="Identifier column name.")
    parser.add_argument("--fingerprint-size", type=int, default=16,
                        help="Circular fingerprint size for the demo featurizer.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.csv.exists():
        write_default_csv(args.csv)
        print(f"created_demo_csv={args.csv}")

    import deepchem as dc

    featurizer = dc.feat.CircularFingerprint(size=args.fingerprint_size)
    loader = dc.data.CSVLoader(
        tasks=[args.task],
        feature_field=args.feature_field,
        id_field=args.id_field,
        featurizer=featurizer,
    )
    dataset = loader.create_dataset(str(args.csv))

    print(f"samples={len(dataset)}")
    print(f"X_shape={getattr(dataset.X, 'shape', None)}")
    print(f"y_shape={getattr(dataset.y, 'shape', None)}")
    print(f"w_shape={getattr(dataset.w, 'shape', None)}")
    print(f"ids={list(dataset.ids)}")


if __name__ == "__main__":
    main()
