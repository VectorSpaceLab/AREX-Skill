#!/usr/bin/env python3
"""Safe no-network smoke checks for direct PyCaret 4.0 engine workflows.

Examples
--------
python scripts/engine_smoke.py --help
python scripts/engine_smoke.py --task classification --list-models
python scripts/engine_smoke.py --task all --indent 2

The script uses sklearn toy data or tiny inline pandas objects. It never calls
pycaret.datasets.get_data and performs no network access by default.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from dataclasses import asdict
from importlib.util import find_spec
from typing import Any, Callable


TASK_ALIASES = {
    "classification": "classification",
    "regression": "regression",
    "clustering": "clustering",
    "anomaly": "anomaly",
    "time-series": "time_series",
    "time_series": "time_series",
    "timeseries": "time_series",
}
ORDERED_TASKS = ["classification", "regression", "clustering", "anomaly", "time_series"]


def _json_default(obj: Any) -> Any:
    """Best-effort JSON conversion for numpy/pandas/sklearn objects."""
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        try:
            return obj.to_dict()
        except TypeError:
            pass
    if hasattr(obj, "tolist"):
        try:
            return obj.tolist()
        except Exception:  # noqa: BLE001
            pass
    try:
        return asdict(obj)
    except Exception:  # noqa: BLE001
        return repr(obj)


def _version() -> str | None:
    try:
        import pycaret

        return getattr(pycaret, "__version__", None)
    except Exception:  # noqa: BLE001
        return None


def _static_models(task: str) -> list[str]:
    try:
        from pycaret.api import list_models

        return [card.id for card in list_models(task)]
    except Exception:
        return []


def _runtime_models(exp: Any) -> list[str]:
    try:
        return [str(x) for x in exp.models().index.tolist()]
    except Exception:
        return []


def _task_result(task: str) -> dict[str, Any]:
    return {"task": task, "pycaret_version": _version(), "status": "ok"}


def smoke_classification(list_models_flag: bool) -> dict[str, Any]:
    import pandas as pd
    from sklearn.datasets import load_breast_cancer

    from pycaret.core import CompareResult, CreateResult, PredictResult, TuneResult
    from pycaret.logging import MemoryLogger
    from pycaret.tasks import ClassificationExperiment

    raw = load_breast_cancer(as_frame=True)
    df = raw.frame.rename(columns={"target": "label"})
    log = MemoryLogger()
    exp = ClassificationExperiment(target="label", session_id=42, fold=2, n_jobs=1, logger=log).fit(
        df
    )
    created = exp.create_model("lr", verbose=False)
    compared = exp.compare_models(include=["lr", "dt"], n_select=2, verbose=False)
    tuned = exp.tune_model(compared.best, n_iter=2, verbose=False)
    predicted = exp.predict_model(tuned.pipeline, data=df.head(8), verbose=False)

    out = _task_result("classification")
    out.update(
        {
            "result_types": {
                "create": type(created).__name__,
                "compare": type(compared).__name__,
                "tune": type(tuned).__name__,
                "predict": type(predicted).__name__,
            },
            "type_checks": {
                "create": isinstance(created, CreateResult),
                "compare": isinstance(compared, CompareResult),
                "tune": isinstance(tuned, TuneResult),
                "predict": isinstance(predicted, PredictResult),
            },
            "leaderboard_rows": int(len(compared.leaderboard)),
            "ranked_ids": compared.ranked_ids,
            "prediction_columns": list(predicted.predictions.columns),
            "prediction_rows": int(len(predicted.predictions)),
            "metrics_columns": list(predicted.metrics.columns) if predicted.metrics is not None else [],
            "event_kinds": [event.kind.value for event in log.events],
            "fitted": bool(exp.__sklearn_is_fitted__()),
        }
    )
    if list_models_flag:
        out["static_model_ids"] = _static_models("classification")
        out["runtime_model_ids"] = _runtime_models(exp)
    assert isinstance(predicted.predictions, pd.DataFrame)
    assert "prediction_label" in predicted.predictions.columns
    return out


def smoke_regression(list_models_flag: bool) -> dict[str, Any]:
    import pandas as pd
    from sklearn.datasets import load_diabetes

    from pycaret.tasks import RegressionExperiment

    raw = load_diabetes(as_frame=True)
    df = raw.frame.rename(columns={"target": "y"})
    exp = RegressionExperiment(target="y", session_id=42, fold=2, n_jobs=1, normalize=True).fit(df)
    created = exp.create_model("lr", verbose=False)
    compared = exp.compare_models(include=["lr", "ridge"], n_select=2, verbose=False)
    predicted = exp.predict_model(compared.best, data=df.head(8), verbose=False)

    out = _task_result("regression")
    out.update(
        {
            "result_types": {
                "create": type(created).__name__,
                "compare": type(compared).__name__,
                "predict": type(predicted).__name__,
            },
            "leaderboard_rows": int(len(compared.leaderboard)),
            "ranked_ids": compared.ranked_ids,
            "prediction_columns": list(predicted.predictions.columns),
            "prediction_rows": int(len(predicted.predictions)),
            "metrics_columns": list(predicted.metrics.columns) if predicted.metrics is not None else [],
            "fitted": bool(exp.__sklearn_is_fitted__()),
        }
    )
    if list_models_flag:
        out["static_model_ids"] = _static_models("regression")
        out["runtime_model_ids"] = _runtime_models(exp)
    assert isinstance(predicted.predictions, pd.DataFrame)
    assert "prediction_label" in predicted.predictions.columns
    return out


def smoke_clustering(list_models_flag: bool) -> dict[str, Any]:
    import pandas as pd
    from sklearn.datasets import make_blobs

    from pycaret.tasks import ClusteringExperiment

    X, _ = make_blobs(n_samples=60, centers=3, n_features=4, random_state=42)
    df = pd.DataFrame(X, columns=["f0", "f1", "f2", "f3"])
    exp = ClusteringExperiment(session_id=42, normalize=True, n_jobs=1).fit(df)
    created = exp.create_model("kmeans", num_clusters=3, verbose=False)
    assigned = exp.assign_model(created.pipeline)
    predicted = exp.predict_model(created.pipeline, data=df.head(6), verbose=False)

    out = _task_result("clustering")
    out.update(
        {
            "result_types": {
                "create": type(created).__name__,
                "predict": type(predicted).__name__,
                "assign": type(assigned).__name__,
            },
            "prediction_columns": list(predicted.predictions.columns),
            "assignment_columns": list(assigned.columns),
            "prediction_rows": int(len(predicted.predictions)),
            "assignment_rows": int(len(assigned)),
            "fitted": bool(exp.__sklearn_is_fitted__()),
        }
    )
    if list_models_flag:
        out["runtime_model_ids"] = _runtime_models(exp)
    assert "Cluster" in assigned.columns
    assert "Cluster" in predicted.predictions.columns
    return out


def smoke_anomaly(list_models_flag: bool) -> dict[str, Any]:
    if find_spec("pyod") is None:
        raise ImportError("Anomaly workflows require pyod. Install with: pip install 'pycaret[anomaly]'.")

    import numpy as np
    import pandas as pd

    from pycaret.tasks import AnomalyExperiment

    rng = np.random.default_rng(42)
    normal = rng.normal(0, 1, size=(64, 3))
    outliers = rng.normal(6, 0.5, size=(4, 3))
    df = pd.DataFrame(np.vstack([normal, outliers]), columns=["x0", "x1", "x2"])

    exp = AnomalyExperiment(session_id=42, normalize=True, n_jobs=1).fit(df)
    created = exp.create_model("iforest", fraction=0.06, verbose=False)
    assigned = exp.assign_model(created.pipeline, score=True)
    predicted = exp.predict_model(created.pipeline, data=df.tail(6), verbose=False)

    out = _task_result("anomaly")
    out.update(
        {
            "result_types": {
                "create": type(created).__name__,
                "predict": type(predicted).__name__,
                "assign": type(assigned).__name__,
            },
            "prediction_columns": list(predicted.predictions.columns),
            "assignment_columns": list(assigned.columns),
            "prediction_rows": int(len(predicted.predictions)),
            "assignment_rows": int(len(assigned)),
            "fitted": bool(exp.__sklearn_is_fitted__()),
        }
    )
    if list_models_flag:
        out["runtime_model_ids"] = _runtime_models(exp)
    assert "Anomaly" in assigned.columns
    assert "Anomaly" in predicted.predictions.columns
    return out


def smoke_time_series(list_models_flag: bool) -> dict[str, Any]:
    missing = [name for name in ("sktime", "statsmodels", "pmdarima") if find_spec(name) is None]
    if missing:
        raise ImportError(
            "Time-series workflows require optional packages "
            f"{missing}. Install with: pip install 'pycaret[timeseries]'."
        )

    import numpy as np
    import pandas as pd

    from pycaret.tasks import TimeSeriesExperiment

    idx = pd.period_range("2020-01", periods=36, freq="M")
    y = pd.Series(
        10 + 0.2 * np.arange(36) + np.sin(np.arange(36) * 2 * np.pi / 12),
        index=idx,
        name="value",
    )

    exp = TimeSeriesExperiment(
        fh=4, seasonal_period=12, fold=2, session_id=42, n_jobs=1
    ).fit(y)
    created = exp.create_model("naive", verbose=False)
    predicted = exp.predict_model(created.pipeline, fh=[1, 2, 3, 4], verbose=False)
    compared = exp.compare_models(include=["naive", "snaive", "polytrend"], verbose=False)

    out = _task_result("time_series")
    out.update(
        {
            "result_types": {
                "create": type(created).__name__,
                "predict": type(predicted).__name__,
                "compare": type(compared).__name__,
            },
            "prediction_columns": list(predicted.predictions.columns),
            "prediction_rows": int(len(predicted.predictions)),
            "metrics_columns": list(predicted.metrics.columns) if predicted.metrics is not None else [],
            "leaderboard_rows": int(len(compared.leaderboard)),
            "ranked_ids": compared.ranked_ids,
            "fitted": bool(exp.__sklearn_is_fitted__()),
        }
    )
    if list_models_flag:
        out["runtime_model_ids"] = _runtime_models(exp)
    assert "y_pred" in predicted.predictions.columns
    return out


SMOKE_FUNCS: dict[str, Callable[[bool], dict[str, Any]]] = {
    "classification": smoke_classification,
    "regression": smoke_regression,
    "clustering": smoke_clustering,
    "anomaly": smoke_anomaly,
    "time_series": smoke_time_series,
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run safe no-network PyCaret 4.0 engine smoke checks."
    )
    parser.add_argument(
        "--task",
        choices=["classification", "regression", "clustering", "anomaly", "time-series", "time_series", "timeseries", "all"],
        default="classification",
        help="Task to smoke-test. Use all for every task family.",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="Include static/runtime model IDs in the JSON output where available.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation. Use 0 for compact output.",
    )
    parser.add_argument(
        "--traceback",
        action="store_true",
        help="Include Python tracebacks in per-task error records.",
    )
    return parser.parse_args(argv)


def selected_tasks(task_arg: str) -> list[str]:
    if task_arg == "all":
        return list(ORDERED_TASKS)
    return [TASK_ALIASES[task_arg]]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    results: list[dict[str, Any]] = []
    ok = True

    for task in selected_tasks(args.task):
        try:
            result = SMOKE_FUNCS[task](args.list_models)
        except Exception as exc:  # noqa: BLE001 - diagnostic script should summarize failures
            ok = False
            result = {
                "task": task,
                "pycaret_version": _version(),
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            if args.traceback:
                result["traceback"] = traceback.format_exc()
        results.append(result)

    payload = {
        "schema": "pycaret.engine-smoke.v1",
        "network": "not-used",
        "selected_tasks": selected_tasks(args.task),
        "results": results,
        "ok": ok,
    }
    indent = None if args.indent == 0 else args.indent
    print(json.dumps(payload, indent=indent, default=_json_default, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
