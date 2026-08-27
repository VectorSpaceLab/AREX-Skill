#!/usr/bin/env python3
"""LightFM install diagnostic for maintainer builds.

The script checks that the active Python can import LightFM, that the compiled
extension wrapper exposes expected symbols, and optionally runs a tiny
in-memory fit/predict smoke test. It has no network side effects.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import platform
import sys
import warnings
from types import ModuleType
from typing import Optional, Sequence, Tuple


EXTENSIONS = {
    "openmp": "lightfm._lightfm_fast_openmp",
    "no-openmp": "lightfm._lightfm_fast_no_openmp",
}

REQUIRED_WRAPPER_SYMBOLS = (
    "CSRMatrix",
    "FastLightFM",
    "fit_logistic",
    "fit_bpr",
    "fit_warp",
    "fit_warp_kos",
    "predict_lightfm",
    "predict_ranks",
)


def _import_module(name: str) -> Tuple[bool, Optional[ModuleType], Optional[str]]:
    try:
        return True, importlib.import_module(name), None
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, None, f"{type(exc).__name__}: {exc}"


def _module_origin(name: str) -> str:
    try:
        spec = importlib.util.find_spec(name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"unavailable ({type(exc).__name__}: {exc})"
    if spec is None:
        return "not found"
    return spec.origin or "built-in/namespace"


def _run_tiny_fit_predict(num_threads: int) -> None:
    import numpy as np
    import scipy.sparse as sp

    from lightfm import LightFM

    rows = np.array([0, 0, 1, 2, 2], dtype=np.int32)
    cols = np.array([0, 2, 1, 0, 3], dtype=np.int32)
    data = np.ones(rows.shape[0], dtype=np.float32)
    interactions = sp.coo_matrix((data, (rows, cols)), shape=(3, 4), dtype=np.float32)

    model = LightFM(no_components=3, loss="logistic", random_state=0)
    model.fit(interactions, epochs=2, num_threads=num_threads)

    user_ids = np.array([0, 1, 2], dtype=np.int32)
    item_ids = np.array([1, 2, 3], dtype=np.int32)
    scores = model.predict(user_ids, item_ids, num_threads=num_threads)

    if scores.shape != (3,):
        raise RuntimeError(f"unexpected prediction shape: {scores.shape!r}")
    if not np.all(np.isfinite(scores)):
        raise RuntimeError(f"non-finite prediction scores: {scores!r}")

    rounded = np.round(scores.astype(float), 6).tolist()
    print(f"tiny fit/predict: ok; scores={rounded}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check that the active Python can import LightFM, load a compiled "
            "extension backend, and optionally run a tiny in-memory fit/predict."
        )
    )
    parser.add_argument(
        "--tiny-run",
        action="store_true",
        help="run a tiny in-memory LightFM fit/predict smoke test after import checks",
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        default=1,
        help="num_threads value for --tiny-run (default: 1)",
    )
    parser.add_argument(
        "--expect-extension",
        choices=("any", "openmp", "no-openmp"),
        default="any",
        help="fail unless the selected compiled extension variant is importable",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print full exception tracebacks for import or tiny-run failures",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.num_threads < 1:
        parser.error("--num-threads must be >= 1")

    print(f"python: {sys.version.split()[0]} ({sys.executable})")
    print(f"platform: {platform.platform()}")
    with warnings.catch_warnings(record=True) as import_warnings:
        warnings.simplefilter("always")
        ok_lightfm, lightfm_module, lightfm_error = _import_module("lightfm")

    for warning in import_warnings:
        print(f"import warning: {warning.message}")

    if not ok_lightfm:
        print(f"import lightfm: FAILED: {lightfm_error}", file=sys.stderr)
        print(
            "hint: install the checkout editable with `python -m pip install -e .` "
            "from the repository root, then rerun this diagnostic.",
            file=sys.stderr,
        )
        if args.verbose:
            raise SystemExit(1)
        return 1

    version = getattr(lightfm_module, "__version__", "unknown")
    print(f"import lightfm: ok; __version__={version}")
    print(f"lightfm module origin: {_module_origin('lightfm')}")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ok_wrapper, wrapper_module, wrapper_error = _import_module("lightfm._lightfm_fast")

    if not ok_wrapper or wrapper_module is None:
        print(f"import lightfm._lightfm_fast: FAILED: {wrapper_error}", file=sys.stderr)
        return 1

    print("import lightfm._lightfm_fast: ok")
    for warning in caught:
        print(f"wrapper warning: {warning.message}")

    missing = [name for name in REQUIRED_WRAPPER_SYMBOLS if not hasattr(wrapper_module, name)]
    if missing:
        print(f"compiled wrapper missing symbols: {', '.join(missing)}", file=sys.stderr)
        return 1
    print("compiled wrapper symbols: ok")

    extension_results = {}
    for label, module_name in EXTENSIONS.items():
        ok_ext, _module, error = _import_module(module_name)
        extension_results[label] = ok_ext
        if ok_ext:
            print(f"extension {label}: ok; origin={_module_origin(module_name)}")
        else:
            print(f"extension {label}: unavailable ({error})")

    if args.expect_extension == "any":
        if not any(extension_results.values()):
            print("no compiled extension variant could be imported", file=sys.stderr)
            return 1
    elif not extension_results[args.expect_extension]:
        print(f"expected extension is not importable: {args.expect_extension}", file=sys.stderr)
        return 1

    if args.tiny_run:
        try:
            _run_tiny_fit_predict(args.num_threads)
        except Exception as exc:  # pragma: no cover - diagnostic path
            print(f"tiny fit/predict: FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
            if args.verbose:
                raise
            return 1

    print("diagnostic: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
