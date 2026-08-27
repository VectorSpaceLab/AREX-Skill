#!/usr/bin/env python3
"""Create a tiny local CSV and run a bounded automl-gs XGBoost search.

The helper is offline, creates its own work directory, and defaults to a single
sampled hyperparameter trial with one boosting round so it stays fast.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import random
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

for _env_var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_env_var, "1")

# automl_gs chooses the subprocess Python with shutil.which('python3'/'python')
# inside the package. Make sure this smoke run resolves back to the same
# environment interpreter that imported automl_gs.
_bin_dir = str(Path(sys.executable).parent)
os.environ["PATH"] = _bin_dir + os.pathsep + os.environ.get("PATH", "")


@contextlib.contextmanager
def pushd(path: Path):
    original = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def _split_ratio(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a floating-point split ratio, got {value!r}") from exc
    if not 0.0 < parsed < 1.0:
        raise argparse.ArgumentTypeError("split must be between 0 and 1")
    return parsed


def _import_pandas():
    try:
        import pandas as pd  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user's environment
        print(
            "Unable to import pandas. This usually means a pandas/numpy binary mismatch "
            "or a broken wheel/conda environment.",
            file=sys.stderr,
        )
        print(f"Import error: {exc}", file=sys.stderr)
        return None
    return pd


def _import_search():
    try:
        from automl_gs import automl_grid_search  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user's environment
        print(
            "Unable to import automl_gs. Make sure the package is installed in the "
            "current environment and that setuptools/pkg_resources is available.",
            file=sys.stderr,
        )
        print(f"Import error: {exc}", file=sys.stderr)
        return None

    try:
        import xgboost  # noqa: F401  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user's environment
        print(
            "xgboost is required for this smoke test. Install it in the same environment "
            "before running the helper.",
            file=sys.stderr,
        )
        print(f"Import error: {exc}", file=sys.stderr)
        return None

    return automl_grid_search


def _build_fixture(pd, csv_path: Path):
    frame = pd.DataFrame(
        {
            "id": range(1, 13),
            "region_code": list(range(101, 113)),
            "age": [23, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45],
            "fare": [12.0, 14.5, 16.2, 18.0, 20.3, 22.5, 24.8, 27.1, 29.4, 31.7, 34.0, 36.3],
            "tier": ["bronze", "silver", "bronze", "gold", "silver", "gold", "bronze", "silver", "bronze", "gold", "silver", "gold"],
            "signup_date": pd.date_range("2024-01-01", periods=12, freq="D").strftime("%Y-%m-%d").tolist(),
            "converted": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        }
    )
    frame.to_csv(csv_path, index=False)
    return frame


def _make_run_dir(base_dir: Path) -> Path:
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = base_dir / f"xgboost_smoke_{stamp}_{os.getpid()}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _verify_outputs(run_dir: Path, model_name: str) -> list[Path]:
    results_csv = run_dir / "automl_results.csv"
    if not results_csv.exists():
        raise FileNotFoundError(f"missing automl_results.csv in {run_dir}")

    best_dirs = sorted(
        path for path in run_dir.iterdir()
        if path.is_dir() and path.name.startswith(f"{model_name}_xgboost_")
    )
    if not best_dirs:
        raise FileNotFoundError(f"missing timestamped best-model folder in {run_dir}")

    best_dir = best_dirs[-1]
    required = [
        best_dir / "model.bin",
        best_dir / "model.py",
        best_dir / "pipeline.py",
        best_dir / "requirements.txt",
        best_dir / "metadata" / "results.csv",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing expected output(s): " + ", ".join(str(path) for path in missing))

    return [results_csv, best_dir] + required


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a tiny local CSV fixture and run a bounded automl-gs XGBoost "
            "search with no network access."
        )
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Optional base directory for the smoke run. Default: a fresh temp directory.",
    )
    parser.add_argument(
        "--keep-workdir",
        action="store_true",
        help="Keep the generated work directory even when a temp directory is used.",
    )
    parser.add_argument(
        "--model-name",
        default="grid_smoke",
        help="Prefix for the generated best-model folder. Default: grid_smoke.",
    )
    parser.add_argument(
        "--num-trials",
        type=_positive_int,
        default=1,
        help="Number of sampled hyperparameter trials. Default: 1.",
    )
    parser.add_argument(
        "--num-epochs",
        type=_positive_int,
        default=1,
        help="Epoch / boosting-round budget per trial. Default: 1.",
    )
    parser.add_argument(
        "--split",
        type=_split_ratio,
        default=0.75,
        help="Train fraction for the generated trial script. Default: 0.75.",
    )
    parser.add_argument(
        "--target-metric",
        default=None,
        help="Optional ranking metric override. Use only metrics emitted by the chosen problem type.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    pd = _import_pandas()
    if pd is None:
        return 1

    automl_grid_search = _import_search()
    if automl_grid_search is None:
        return 1

    cleanup_base = False
    if args.workdir is None:
        base_dir = Path(tempfile.mkdtemp(prefix="automl_gs_grid_search_")).resolve()
        cleanup_base = not args.keep_workdir
    else:
        base_dir = args.workdir.expanduser().resolve()
        base_dir.mkdir(parents=True, exist_ok=True)

    run_dir = _make_run_dir(base_dir)
    csv_path = run_dir / "tiny_grid_search_fixture.csv"
    _build_fixture(pd, csv_path)
    random.seed(0)

    print(f"Work directory: {base_dir}")
    print(f"Run directory:   {run_dir}")
    print(f"CSV fixture:     {csv_path}")

    try:
        with pushd(run_dir):
            automl_grid_search(
                str(csv_path),
                "converted",
                target_metric=args.target_metric,
                framework="xgboost",
                model_name=args.model_name,
                num_trials=args.num_trials,
                split=args.split,
                num_epochs=args.num_epochs,
                col_types={"region_code": "numeric"},
                gpu=False,
            )
    except Exception as exc:  # pragma: no cover - runtime smoke only
        print(f"Search failed: {exc}", file=sys.stderr)
        return 1

    try:
        verified = _verify_outputs(run_dir, args.model_name)
    except Exception as exc:  # pragma: no cover - runtime smoke only
        print(f"Output verification failed: {exc}", file=sys.stderr)
        return 1

    results_csv = verified[0]
    best_dir = verified[1]
    trial_rows = pd.read_csv(results_csv)
    print(f"Recorded {len(trial_rows)} row(s) in {results_csv}")
    print(f"Best-model folder: {best_dir}")
    print("Tiny xgboost grid-search smoke passed.")

    if cleanup_base:
        shutil.rmtree(base_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
