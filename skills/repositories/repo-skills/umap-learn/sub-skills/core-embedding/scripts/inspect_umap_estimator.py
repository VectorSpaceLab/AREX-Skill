#!/usr/bin/env python3
"""Inspect installed umap.UMAP APIs and optionally a trusted fitted estimator.

Help and argument parsing work without umap-learn installed. Loading pickle files
is inherently unsafe for untrusted files; this script requires --allow-unsafe-pickle
before reading one.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import pickle
import sys
import traceback
from pathlib import Path
from typing import Any


UMAP_SIGNATURE = "(n_neighbors=15, n_components=2, metric='euclidean', metric_kwds=None, output_metric='euclidean', output_metric_kwds=None, n_epochs=None, learning_rate=1.0, init='spectral', min_dist=0.1, spread=1.0, low_memory=True, n_jobs=-1, set_op_mix_ratio=1.0, local_connectivity=1.0, repulsion_strength=1.0, negative_sample_rate=5, transform_queue_size=4.0, a=None, b=None, random_state=None, angular_rp_forest=False, target_n_neighbors=-1, target_metric='categorical', target_metric_kwds=None, target_weight=0.5, transform_seed=42, transform_mode='embedding', force_approximation_algorithm=False, verbose=False, tqdm_kwds=None, unique=False, densmap=False, dens_lambda=2.0, dens_frac=0.3, dens_var_shift=0.1, output_dens=False, disconnection_distance=None, precomputed_knn=(None, None, None))"
METHOD_SIGNATURES = {
    "fit": "(self, X, y=None, ensure_all_finite=True, **kwargs)",
    "fit_transform": "(self, X, y=None, ensure_all_finite=True, **kwargs)",
    "transform": "(self, X, ensure_all_finite=True)",
    "inverse_transform": "(self, X)",
    "update": "(self, X, ensure_all_finite=True)",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print installed umap.UMAP version/signatures and optionally inspect a "
            "trusted fitted estimator pickle/joblib-like pickle path."
        )
    )
    parser.add_argument(
        "--pickle",
        type=Path,
        help="Trusted pickle/joblib-compatible estimator path to inspect. Requires --allow-unsafe-pickle.",
    )
    parser.add_argument(
        "--allow-unsafe-pickle",
        action="store_true",
        help="Acknowledge that pickle loading can execute code and the file is trusted.",
    )
    parser.add_argument(
        "--expect-fitted",
        action="store_true",
        help="Return nonzero if --pickle is supplied and the estimator lacks fitted UMAP attributes.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    parser.add_argument(
        "--verbose-errors",
        action="store_true",
        help="Include tracebacks in dependency or pickle errors.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON output (default behavior).",
    )
    return parser


def dependency_advice(exc: BaseException) -> str:
    return (
        f"{exc.__class__.__name__}: {exc}. Install the base package and required "
        "runtime dependencies, for example: python -m pip install umap-learn "
        "scikit-learn scipy numpy numba pynndescent tqdm. Optional extras such as "
        "plot, parametric_umap, and tbb are not required for this inspector."
    )


def import_umap_payload(verbose_errors: bool) -> tuple[dict[str, Any], Any | None]:
    payload: dict[str, Any] = {
        "import_ok": False,
        "distribution_version": None,
        "module_version": None,
        "module_file_present": None,
        "signatures": {
            "UMAP": UMAP_SIGNATURE,
            **{f"UMAP.{name}": sig for name, sig in METHOD_SIGNATURES.items()},
        },
        "signature_source": "documented-fallback",
        "error": None,
    }
    try:
        import importlib.metadata as metadata
        umap = importlib.import_module("umap")
        distribution_version = metadata.version("umap-learn")
        payload.update(
            {
                "import_ok": True,
                "distribution_version": distribution_version,
                "module_version": getattr(umap, "__version__", None),
                "module_file_present": bool(getattr(umap, "__file__", None)),
                "signatures": {
                    "UMAP": str(inspect.signature(umap.UMAP)),
                    "UMAP.fit": str(inspect.signature(umap.UMAP.fit)),
                    "UMAP.fit_transform": str(inspect.signature(umap.UMAP.fit_transform)),
                    "UMAP.transform": str(inspect.signature(umap.UMAP.transform)),
                    "UMAP.inverse_transform": str(inspect.signature(umap.UMAP.inverse_transform)),
                    "UMAP.update": str(inspect.signature(umap.UMAP.update)),
                },
                "signature_source": "runtime-inspection",
            }
        )
        return payload, umap
    except Exception as exc:  # pragma: no cover - depends on caller env
        err: dict[str, Any] = {"message": dependency_advice(exc)}
        if verbose_errors:
            err["traceback"] = traceback.format_exc()
        payload["error"] = err
        return payload, None


def try_joblib_or_pickle_load(path: Path) -> Any:
    try:
        joblib = importlib.import_module("joblib")
        return joblib.load(path)
    except ModuleNotFoundError:
        with path.open("rb") as handle:
            return pickle.load(handle)


def array_shape_dtype(value: Any) -> dict[str, Any]:
    shape = getattr(value, "shape", None)
    dtype = getattr(value, "dtype", None)
    return {
        "present": value is not None,
        "shape": list(shape) if shape is not None else None,
        "dtype": str(dtype) if dtype is not None else None,
    }


def inspect_estimator(obj: Any, umap_module: Any | None) -> dict[str, Any]:
    cls = obj.__class__
    info: dict[str, Any] = {
        "class": f"{cls.__module__}.{cls.__name__}",
        "is_umap_instance": bool(umap_module is not None and isinstance(obj, umap_module.UMAP)),
        "params": {},
        "fitted": False,
        "attributes": {},
        "warnings": [],
    }

    if hasattr(obj, "get_params"):
        try:
            params = obj.get_params(deep=False)
            keep = [
                "n_neighbors",
                "n_components",
                "metric",
                "output_metric",
                "min_dist",
                "spread",
                "random_state",
                "n_jobs",
                "low_memory",
                "transform_seed",
                "transform_mode",
                "force_approximation_algorithm",
                "unique",
                "densmap",
                "precomputed_knn",
            ]
            info["params"] = {k: repr(params.get(k)) for k in keep if k in params}
        except Exception as exc:
            info["warnings"].append(f"get_params failed: {exc}")

    embedding = getattr(obj, "embedding_", None)
    graph = getattr(obj, "graph_", None)
    raw_data = getattr(obj, "_raw_data", None)
    info["attributes"] = {
        "embedding_": array_shape_dtype(embedding),
        "graph_": array_shape_dtype(graph),
        "_raw_data": array_shape_dtype(raw_data),
        "_knn_search_index_is_none": getattr(obj, "_knn_search_index", "missing") is None,
        "has_rad_orig_": hasattr(obj, "rad_orig_"),
        "has_rad_emb_": hasattr(obj, "rad_emb_"),
        "has_embedding_list_": hasattr(obj, "embedding_list_"),
        "has_unique_inverse_": hasattr(obj, "_unique_inverse_"),
    }
    info["fitted"] = bool(embedding is not None or graph is not None)

    if getattr(obj, "metric", None) == "precomputed" and raw_data is not None:
        shape = getattr(raw_data, "shape", None)
        if shape is not None:
            info["precomputed_transform_advice"] = (
                "For metric='precomputed', transform input must have shape "
                f"(n_new, {shape[0]}) with columns ordered like the original training rows."
            )
    if getattr(obj, "densmap", False):
        info["warnings"].append("densmap=True: transform and inverse_transform are not supported for new data in base UMAP.")
    if getattr(obj, "metric", None) == "precomputed":
        info["warnings"].append("metric='precomputed': inverse_transform and update are unavailable.")
    if info["attributes"].get("_knn_search_index_is_none") is True:
        info["warnings"].append("No k-NN search index: raw-data transform may be unavailable after two-array precomputed_knn.")
    if getattr(obj, "random_state", None) is not None and getattr(obj, "n_jobs", 1) == 1:
        info["warnings"].append("random_state is set; UMAP uses n_jobs=1 for reproducibility.")

    return info


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    package_payload, umap_module = import_umap_payload(args.verbose_errors)
    payload: dict[str, Any] = {
        "status": "passed" if package_payload["import_ok"] else "dependency_error",
        "package": package_payload,
        "pickle": None,
    }
    exit_code = 0 if package_payload["import_ok"] else 2

    if args.pickle is not None:
        pickle_payload: dict[str, Any] = {
            "path_name": args.pickle.name,
            "loaded": False,
            "error": None,
            "estimator": None,
        }
        payload["pickle"] = pickle_payload
        if not args.allow_unsafe_pickle:
            pickle_payload["error"] = (
                "Refusing to load pickle without --allow-unsafe-pickle. "
                "Only load pickle/joblib files from trusted sources."
            )
            payload["status"] = "failed"
            exit_code = 1
        elif not args.pickle.exists():
            pickle_payload["error"] = "Pickle path does not exist."
            payload["status"] = "failed"
            exit_code = 1
        else:
            try:
                obj = try_joblib_or_pickle_load(args.pickle)
                pickle_payload["loaded"] = True
                pickle_payload["estimator"] = inspect_estimator(obj, umap_module)
                if args.expect_fitted and not pickle_payload["estimator"]["fitted"]:
                    pickle_payload["error"] = "Object loaded but does not look like a fitted UMAP estimator."
                    payload["status"] = "failed"
                    exit_code = 1
                elif package_payload["import_ok"]:
                    payload["status"] = "passed"
            except Exception as exc:  # pragma: no cover - diagnostic path
                err: dict[str, Any] = {"type": exc.__class__.__name__, "message": str(exc)}
                if args.verbose_errors:
                    err["traceback"] = traceback.format_exc()
                pickle_payload["error"] = err
                payload["status"] = "failed"
                exit_code = 1

    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
