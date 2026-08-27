#!/usr/bin/env python3
"""Exercise fastdup search and vector-search on a tiny synthetic fixture."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import fastdup
from fastdup.synthetic_image_data import create_synthetic_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny search smoke test")
    parser.add_argument("--root", required=True, help="Workspace root for images and work_dir")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    img_dir = root / "images"
    work_dir = root / "work"
    img_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    annot, *_ = create_synthetic_data(str(img_dir), n_valid=4, n_corrupted=0, n_duplicated=1, n_no_annotation=0, n_no_image=0)
    annot = annot.copy()
    annot["filename"] = annot["filename"].apply(lambda name: str(img_dir / name))

    fd = fastdup.create(work_dir=str(work_dir), input_dir=str(img_dir))
    ret = fd.run(annotations=annot, num_images=20, print_summary=False, verbose=False)
    if ret != 0:
        raise RuntimeError(f"fastdup run returned {ret}")

    init_ret = fd.init_search(2, verbose=False)
    if init_ret != 0:
        raise RuntimeError(f"init_search returned {init_ret}")

    query = annot.iloc[0]["filename"]
    search_df = fd.search(query)
    if search_df is None:
        raise RuntimeError("search returned no dataframe")

    feature_path = work_dir / "atrain_features.dat"
    _, mat = fastdup.load_binary_feature(str(feature_path), d=fd.config["d"])
    vector_df = fd.vector_search(vec=mat[0])
    if vector_df is None:
        raise RuntimeError("vector_search returned no dataframe")

    print(f"search_rows={len(search_df)}")
    print(f"vector_rows={len(vector_df)}")
    print(f"work_dir={work_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
