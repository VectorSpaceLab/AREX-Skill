#!/usr/bin/env python3
"""Run a minimal ProLIF fingerprint smoke check using installed package data."""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a one-frame ProLIF fingerprint on installed package data and "
            "print a JSON summary."
        ),
    )
    parser.add_argument(
        "--pickle-output",
        type=Path,
        help="Optional path for writing the completed Fingerprint pickle; existing files are not overwritten.",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable tqdm progress output for automated contexts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.pickle_output is not None and args.pickle_output.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {args.pickle_output}")

    showwarning = warnings.showwarning
    warnings.showwarning = lambda *_args, **_kwargs: None
    try:
        import MDAnalysis as mda
        import prolif as plf

        universe = mda.Universe(plf.datafiles.TOP, plf.datafiles.TRAJ)
        ligand = universe.select_atoms("resname LIG")
        protein = universe.select_atoms("protein")

        interactions = ["Hydrophobic", "HBDonor", "HBAcceptor"]
        fingerprint = plf.Fingerprint(interactions)
        fingerprint.run(
            universe.trajectory[:1],
            ligand,
            protein,
            n_jobs=1,
            progress=not args.no_progress,
        )
        dataframe = fingerprint.to_dataframe()

        if args.pickle_output is not None:
            args.pickle_output.parent.mkdir(parents=True, exist_ok=True)
            fingerprint.to_pickle(args.pickle_output)

        summary: dict[str, Any] = {
            "dataframe_shape": list(dataframe.shape),
            "frame_keys": sorted(int(frame) for frame in fingerprint.ifp),
            "interactions": list(fingerprint.interactions),
            "n_interactions": fingerprint.n_interactions,
            "use_segid": fingerprint.use_segid,
            "pickle_output": str(args.pickle_output) if args.pickle_output else None,
        }
    finally:
        warnings.showwarning = showwarning
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
