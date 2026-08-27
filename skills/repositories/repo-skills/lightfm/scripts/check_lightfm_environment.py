#!/usr/bin/env python3
"""Check that the active Python can import and run LightFM.

This script is safe by default: it performs no network access, reads no source
checkout files, and optionally trains a tiny in-memory CPU model.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import platform
import sys
from typing import Any


def _module_origin(name: str) -> str:
    try:
        spec = importlib.util.find_spec(name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"unavailable ({type(exc).__name__}: {exc})"
    if spec is None:
        return "not found"
    return spec.origin or "built-in/namespace"


def _try_import(name: str) -> tuple[bool, Any | None, str | None]:
    try:
        return True, importlib.import_module(name), None
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, None, f"{type(exc).__name__}: {exc}"


def _tiny_run(threads: int) -> dict[str, Any]:
    import numpy as np
    import scipy.sparse as sp

    from lightfm import LightFM
    from lightfm.evaluation import precision_at_k

    rows = np.array([0, 0, 1, 1, 2, 2, 3, 3], dtype=np.int32)
    cols = np.array([0, 1, 1, 2, 2, 3, 3, 4], dtype=np.int32)
    data = np.ones(rows.shape[0], dtype=np.float32)
    train = sp.coo_matrix((data, (rows, cols)), shape=(4, 6), dtype=np.float32)

    test_rows = np.array([0, 1, 2, 3], dtype=np.int32)
    test_cols = np.array([2, 3, 4, 5], dtype=np.int32)
    test = sp.coo_matrix(
        (np.ones(test_rows.shape[0], dtype=np.float32), (test_rows, test_cols)),
        shape=train.shape,
        dtype=np.float32,
    )

    model = LightFM(no_components=4, loss="warp", random_state=13)
    model.fit(train, epochs=2, num_threads=threads)

    scores = model.predict(0, np.arange(train.shape[1], dtype=np.int32), num_threads=threads)
    precision = precision_at_k(
        model,
        test,
        train_interactions=train,
        k=3,
        num_threads=threads,
        check_intersections=True,
    )

    if not np.isfinite(scores).all():
        raise RuntimeError("non-finite prediction scores")
    if not np.isfinite(precision).all():
        raise RuntimeError("non-finite precision values")

    return {
        "train_shape": list(train.shape),
        "train_nnz": int(train.nnz),
        "test_nnz": int(test.nnz),
        "score_min": float(np.min(scores)),
        "score_max": float(np.max(scores)),
        "precision_at_3_mean": float(precision.mean()),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check LightFM import, compiled extension availability, and optional tiny CPU training."
    )
    parser.add_argument(
        "--tiny-run",
        action="store_true",
        help="train/evaluate a tiny no-network in-memory model after import checks",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=1,
        help="CPU thread count for --tiny-run (default: 1)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the diagnostic report as JSON instead of human-readable lines",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.threads < 1:
        parser.error("--threads must be >= 1")

    report: dict[str, Any] = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "gpu_supported_by_lightfm": False,
        "imports": {},
        "origins": {},
        "checks": {},
    }

    ok_lightfm, lightfm_module, lightfm_error = _try_import("lightfm")
    report["imports"]["lightfm"] = {"ok": ok_lightfm, "error": lightfm_error}
    report["origins"]["lightfm"] = _module_origin("lightfm")
    if not ok_lightfm or lightfm_module is None:
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"import lightfm: FAILED: {lightfm_error}", file=sys.stderr)
            print("Install with `python -m pip install lightfm` or use a working editable install.", file=sys.stderr)
        return 1

    report["lightfm_version"] = getattr(lightfm_module, "__version__", "unknown")

    ok_fast, fast_module, fast_error = _try_import("lightfm._lightfm_fast")
    report["imports"]["lightfm._lightfm_fast"] = {"ok": ok_fast, "error": fast_error}
    report["origins"]["lightfm._lightfm_fast"] = _module_origin("lightfm._lightfm_fast")
    if not ok_fast or fast_module is None:
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"import lightfm._lightfm_fast: FAILED: {fast_error}", file=sys.stderr)
            print("The compiled extension is missing or broken; use repo-development troubleshooting.", file=sys.stderr)
        return 1

    required_symbols = [
        "CSRMatrix",
        "FastLightFM",
        "fit_logistic",
        "fit_bpr",
        "fit_warp",
        "fit_warp_kos",
        "predict_lightfm",
        "predict_ranks",
    ]
    missing = [name for name in required_symbols if not hasattr(fast_module, name)]
    report["checks"]["compiled_wrapper_symbols"] = {"ok": not missing, "missing": missing}
    if missing:
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"compiled extension missing symbols: {', '.join(missing)}", file=sys.stderr)
        return 1

    if args.tiny_run:
        try:
            report["tiny_run"] = _tiny_run(args.threads)
            report["checks"]["tiny_run"] = {"ok": True}
        except Exception as exc:  # pragma: no cover - diagnostic path
            report["checks"]["tiny_run"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print(f"tiny run: FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"import lightfm: ok; version={report['lightfm_version']}")
        print(f"compiled extension: ok; origin={report['origins']['lightfm._lightfm_fast']}")
        print("gpu support: not available in LightFM; use CPU/OpenMP threads only")
        if args.tiny_run:
            tiny = report["tiny_run"]
            print(
                "tiny run: ok; "
                f"shape={tuple(tiny['train_shape'])} precision@3={tiny['precision_at_3_mean']:.6f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
