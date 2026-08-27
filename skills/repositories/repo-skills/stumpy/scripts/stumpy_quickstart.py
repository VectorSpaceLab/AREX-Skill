#!/usr/bin/env python3
"""Run a tiny no-network STUMPY quickstart across core workflows."""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run tiny STUMPY quickstart smokes.")
    parser.add_argument("--skip-dask", action="store_true", help="Skip the optional Dask LocalCluster smoke.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        import stumpy
    except ImportError as exc:  # pragma: no cover
        print(f"ERROR: could not import stumpy: {exc}", file=sys.stderr)
        return 1

    T = np.array([0.0, 1.0, 0.0, -1.0, -1.0, 0.0, 1.0, 0.0, -0.5, 2.0, 3.0, 2.0], dtype=np.float64)
    m = 3
    result: dict[str, object] = {}

    mp = stumpy.stump(T, m)
    P = mp[:, 0].astype(float)
    result["stump"] = {"shape": list(mp.shape), "best_index": int(np.nanargmin(P)), "finite": int(np.isfinite(P).sum())}

    aamp = stumpy.aamp(T, m)
    result["aamp"] = {"shape": list(aamp.shape), "finite": int(np.isfinite(aamp[:, 0].astype(float)).sum())}

    Q = T[0:m]
    D = stumpy.mass(Q, T)
    result["mass"] = {"distances": int(D.shape[0]), "best_index": int(np.nanargmin(D.astype(float)))}

    motif_distances, motif_indices = stumpy.motifs(T, mp[:, 0])
    result["motifs"] = {"motif_sets": len(motif_indices), "first_indices": motif_indices[0].astype(int).tolist() if len(motif_indices) else []}

    T_multi = np.vstack([T, np.roll(T, 1)]).astype(np.float64)
    Pm, Im = stumpy.mstump(T_multi, m)
    result["mstump"] = {"P_shape": list(Pm.shape), "I_shape": list(Im.shape)}

    stream = stumpy.stumpi(T[:8], m)
    stream.update(float(T[8]))
    result["stumpi"] = {"P_len": int(stream.P_.shape[0]), "I_len": int(stream.I_.shape[0])}

    if not args.skip_dask:
        try:
            from dask.distributed import Client, LocalCluster
            cluster = LocalCluster(n_workers=1, threads_per_worker=1, processes=False, dashboard_address=None)
            client = Client(cluster)
            try:
                dmp = stumpy.stumped(client, T, m)
                result["stumped"] = {"shape": list(dmp.shape)}
            finally:
                client.close(); cluster.close()
        except Exception as exc:
            result["stumped"] = {"skipped_or_failed": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
