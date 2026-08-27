#!/usr/bin/env python3
"""Deterministic smoke test for datamol fingerprint/similarity workflows."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny deterministic datamol fingerprint, distance, clustering, "
            "diversity-picking, centroid-picking, and MCS smoke test."
        )
    )
    parser.add_argument(
        "--smiles",
        nargs="+",
        default=["CCO", "CCN", "CCCO", "c1ccccc1", "c1ccncc1"],
        help="SMILES strings to analyze. Defaults to five tiny molecules.",
    )
    parser.add_argument(
        "--fp-type",
        default="ecfp",
        help="Fingerprint type passed to datamol.to_fp/pdist/cdist. Default: ecfp.",
    )
    parser.add_argument(
        "--fold-size",
        type=int,
        default=None,
        help="Optional fold size passed to datamol.to_fp/pdist/cdist.",
    )
    parser.add_argument(
        "--cluster-cutoff",
        type=float,
        default=0.4,
        help="Butina clustering distance cutoff. Default: 0.4.",
    )
    parser.add_argument(
        "--npick",
        type=int,
        default=2,
        help="Number of diverse/centroid molecules to pick. Default: 2.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=19,
        help="Seed for deterministic diverse picking. Default: 19.",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=1,
        help="Datamol fingerprint parallelism. Default: 1.",
    )
    return parser.parse_args()


def _load_datamol():
    try:
        import datamol as dm  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller environment
        raise SystemExit(
            "Could not import datamol and its chemistry dependencies. "
            "Install datamol with RDKit support in the active Python environment. "
            f"Original error: {exc}"
        ) from exc
    return dm


def _round_matrix(matrix) -> list[list[float]]:
    return [[round(float(value), 4) for value in row] for row in matrix.tolist()]


def _validate_molecules(dm, smiles: Sequence[str]):
    mols = [dm.to_mol(item) for item in smiles]
    invalid = [index for index, mol in enumerate(mols) if mol is None]
    if invalid:
        bad = [smiles[index] for index in invalid]
        raise SystemExit(f"Invalid SMILES at positions {invalid}: {bad}")
    return mols


def main() -> int:
    args = _parse_args()
    dm = _load_datamol()

    supported = sorted(dm.list_supported_fingerprints())
    if args.fp_type not in supported:
        raise SystemExit(
            f"Unsupported --fp-type {args.fp_type!r}. Supported fingerprints: {', '.join(supported)}"
        )

    mols = _validate_molecules(dm, args.smiles)
    npick = min(args.npick, len(mols))
    fp_kwargs = {"fp_type": args.fp_type}
    if args.fold_size is not None:
        fp_kwargs["fold_size"] = args.fold_size

    fingerprints = [dm.to_fp(mol, as_array=True, **fp_kwargs) for mol in mols]
    fp_shape = [len(fingerprints), int(fingerprints[0].shape[0]) if fingerprints else 0]
    fp_sums = [float(fp.sum()) for fp in fingerprints]

    pairwise = dm.pdist(mols, n_jobs=args.n_jobs, squareform=True, **fp_kwargs)
    cross = dm.cdist(mols[:npick], mols, n_jobs=args.n_jobs, **fp_kwargs)

    cluster_indices, cluster_mols = dm.cluster_mols(
        mols,
        cutoff=args.cluster_cutoff,
        n_jobs=args.n_jobs,
    )
    diverse_indices, diverse_mols = dm.pick_diverse(
        mols,
        npick=npick,
        seed=args.seed,
        n_jobs=args.n_jobs,
    )
    centroid_indices, centroid_mols = dm.pick_centroids(
        mols,
        npick=npick,
        threshold=args.cluster_cutoff,
        method="sphere",
        n_jobs=args.n_jobs,
    )

    mcs_smarts = dm.find_mcs(mols[: max(2, npick)], timeout=2, threshold=0.5)

    result = {
        "supported_fingerprints": supported,
        "input_smiles": list(args.smiles),
        "fp_type": args.fp_type,
        "fingerprint_shape": fp_shape,
        "fingerprint_sums": [round(value, 4) for value in fp_sums],
        "pairwise_distance": _round_matrix(pairwise),
        "cross_distance_shape": list(cross.shape),
        "cluster_indices": [list(cluster) for cluster in cluster_indices],
        "cluster_sizes": [len(group) for group in cluster_mols],
        "diverse_indices": diverse_indices.astype(int).tolist(),
        "diverse_smiles": [dm.to_smiles(mol) for mol in diverse_mols],
        "centroid_indices": centroid_indices.astype(int).tolist(),
        "centroid_smiles": [dm.to_smiles(mol) for mol in centroid_mols],
        "mcs_smarts": mcs_smarts,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
