#!/usr/bin/env python3
"""Tiny Mars Learn smoke helper.

This helper imports representative Mars Learn estimators and, unless
`--imports-only` is set, runs a small CPU PCA + nearest-neighbor workflow.
It does not require optional external integrations such as Dask, Joblib,
Proxima, PyTorch, TensorFlow, XGBoost, LightGBM, or Statsmodels.

Examples:
  python scripts/check_mars_learn.py --imports-only
  python scripts/check_mars_learn.py --json

Run it with the Python interpreter from the environment where `pymars` is
installed; a direct shebang run can use the wrong interpreter if `PATH` points
at a different Python.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--imports-only",
        action="store_true",
        help="only import representative Mars Learn APIs",
    )
    parser.add_argument("--json", action="store_true", help="print JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        import mars
        import mars.tensor as mt
        from mars.config import options
        from mars.learn.cluster import KMeans
        from mars.learn.decomposition import PCA
        from mars.learn.neighbors import NearestNeighbors
    except Exception as exc:  # pragma: no cover - user-facing smoke path
        payload = {"status": "import_failed", "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(payload["error"], file=sys.stderr)
        return 1

    result: Dict[str, Any] = {
        "status": "ok",
        "mars_version": mars.__version__,
        "imports": [KMeans.__name__, PCA.__name__, NearestNeighbors.__name__],
    }

    if not args.imports_only:
        session = None
        try:
            options.show_progress = False
            session = mars.new_session()
            X = mt.random.RandomState(0).rand(20, 3, chunk_size=10)
            pca = PCA(n_components=2)
            pca.fit(X)
            transformed = pca.transform(X)
            nn = NearestNeighbors(n_neighbors=2)
            nn.fit(X)
            distances, indices = nn.kneighbors(X[:3])
            result["smoke"] = {
                "pca_shape": tuple(transformed.shape),
                "neighbor_distance_shape": tuple(getattr(distances, "shape", ())),
                "neighbor_index_shape": tuple(getattr(indices, "shape", ())),
            }
        except Exception as exc:  # pragma: no cover - user-facing smoke path
            result.update({"status": "failed", "error": f"{type(exc).__name__}: {exc}"})
            if args.json:
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                print(result["error"], file=sys.stderr)
            return 1
        finally:
            if session is not None:
                try:
                    mars.stop_server()
                except Exception:
                    pass

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"mars={result['mars_version']}")
        print(f"imports={','.join(result['imports'])}")
        if "smoke" in result:
            print(f"smoke={result['smoke']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
