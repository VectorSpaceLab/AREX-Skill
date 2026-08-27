#!/usr/bin/env python3
"""Safe datamol visualization and utility smoke test."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Iterable


def _smiles_length(smiles: str) -> int:
    return len(smiles)


def _batch_lengths(smiles_batch: Iterable[str]) -> list[int]:
    return [len(smiles) for smiles in smiles_batch]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render a tiny datamol SVG grid, optionally render a lasso-highlight SVG, "
            "exercise fsspec path helpers, and run deterministic parallel utility calls."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for generated SVG files. Defaults to a new temporary directory.",
    )
    parser.add_argument(
        "--scheduler",
        choices=["threads", "processes"],
        default="threads",
        help="Scheduler passed to dm.parallelized for the tiny utility job.",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=1,
        help="Number of jobs for the tiny utility job. Use 1 for deterministic sequential behavior.",
    )
    parser.add_argument(
        "--no-lasso",
        action="store_true",
        help="Skip lasso-highlight rendering and only create the base molecule grid.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    import datamol as dm

    if args.output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="datamol-viz-smoke-"))
    else:
        output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    smiles = ["CCO", "c1ccccc1", "CC(=O)O"]
    mols = [dm.to_mol(item) for item in smiles]
    if any(mol is None for mol in mols):
        raise RuntimeError("A built-in smoke-test SMILES failed to parse.")

    grid_path = output_dir / "datamol_grid.svg"
    with dm.without_rdkit_log():
        grid_image = dm.viz.to_image(
            mols,
            legends=smiles,
            n_cols=3,
            use_svg=True,
            mol_size=(220, 180),
            outfile=str(grid_path),
        )

    lasso_path = None
    if not args.no_lasso:
        lasso_path = output_dir / "datamol_lasso.svg"
        lasso_svg = dm.viz.lasso_highlight_image(
            target_molecules="CC(=O)Oc1ccccc1C(=O)O",
            search_molecules="c1ccccc1",
            legends="aspirin aromatic ring",
            use_svg=True,
            mol_size=(260, 220),
            color_list=["#ff1472"],
        )
        lasso_path.write_text(lasso_svg, encoding="utf-8")

    lengths = dm.parallelized(
        _smiles_length,
        smiles,
        scheduler=args.scheduler,
        n_jobs=args.n_jobs,
        progress=False,
    )
    batched_lengths = dm.parallelized_with_batches(
        _batch_lengths,
        smiles,
        batch_size=2,
        scheduler=args.scheduler,
        n_jobs=args.n_jobs,
        progress=False,
    )

    summary = {
        "ok": True,
        "output_dir": str(output_dir),
        "grid_svg": str(grid_path),
        "grid_exists": dm.utils.fs.is_file(grid_path),
        "grid_protocol": dm.utils.fs.get_protocol(grid_path),
        "grid_extension": dm.utils.fs.get_extension(grid_path),
        "grid_return_type": type(grid_image).__name__,
        "lasso_svg": str(lasso_path) if lasso_path is not None else None,
        "lasso_exists": dm.utils.fs.is_file(lasso_path) if lasso_path is not None else False,
        "lengths": list(lengths),
        "batched_lengths": list(batched_lengths),
        "rdkit_ge_2023_03": bool(dm.is_greater_eq_than_current_rdkit_version("2023.03")),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
