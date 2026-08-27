#!/usr/bin/env python3
"""Probe whether the current Python runtime can use DeepCTR Estimators.

This script is intentionally safe by default: it imports TensorFlow and DeepCTR,
checks legacy Estimator symbols, imports DeepCTR Estimator constructors and input
helpers, and optionally constructs a tiny DeepFMEstimator. It does not require
CSV or TFRecord files and does not launch source-repository examples.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
import tempfile
from typing import Any, Dict, Iterable, List, Optional, Tuple


ESTIMATOR_CONSTRUCTORS = [
    "AFMEstimator",
    "AutoIntEstimator",
    "CCPMEstimator",
    "DCNEstimator",
    "DeepFEFMEstimator",
    "DeepFMEstimator",
    "FiBiNETEstimator",
    "FNNEstimator",
    "FwFMEstimator",
    "NFMEstimator",
    "PNNEstimator",
    "WDLEstimator",
    "xDeepFMEstimator",
]


def _version_tuple(version_text: str) -> Tuple[int, int, int]:
    parts = [int(x) for x in re.findall(r"\d+", version_text or "")[:3]]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])  # type: ignore[return-value]


def _deepctr_native_estimator_gate(tf_version: str) -> bool:
    version = _version_tuple(tf_version)
    return version < (2, 0, 0) or (2, 2, 0) <= version < (2, 6, 0)


def _clean_error(exc: BaseException) -> str:
    """Return an exception summary without stack frames or installation paths."""
    text = str(exc).replace("\n", " ").strip()
    if len(text) > 500:
        text = text[:497] + "..."
    return f"{exc.__class__.__name__}: {text}" if text else exc.__class__.__name__


def _import_module(name: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # pragma: no cover - depends on local runtime
        return None, _clean_error(exc)


def _has_nested_attr(obj: Any, attrs: Iterable[str]) -> bool:
    cur = obj
    for attr in attrs:
        if not hasattr(cur, attr):
            return False
        cur = getattr(cur, attr)
    return True


def _inspect_tensorflow(tf: Any) -> Dict[str, Any]:
    tf_version = getattr(tf, "__version__", "unknown")
    estimator = getattr(tf, "estimator", None)
    compat_v1_estimator = getattr(getattr(getattr(tf, "compat", None), "v1", None), "estimator", None)
    feature_column = getattr(tf, "feature_column", None)

    required_estimator_symbols = {
        "tf.estimator": estimator is not None,
        "tf.estimator.Estimator": hasattr(estimator, "Estimator") if estimator is not None else False,
        "tf.estimator.RunConfig": hasattr(estimator, "RunConfig") if estimator is not None else False,
        "tf.estimator.ModeKeys": hasattr(estimator, "ModeKeys") if estimator is not None else False,
        "tf.estimator.EstimatorSpec": hasattr(estimator, "EstimatorSpec") if estimator is not None else False,
        "tf.estimator.export.PredictOutput": _has_nested_attr(estimator, ["export", "PredictOutput"])
        if estimator is not None
        else False,
    }

    feature_column_symbols = {
        "tf.feature_column": feature_column is not None,
        "categorical_column_with_identity": hasattr(feature_column, "categorical_column_with_identity")
        if feature_column is not None
        else False,
        "categorical_column_with_hash_bucket": hasattr(feature_column, "categorical_column_with_hash_bucket")
        if feature_column is not None
        else False,
        "embedding_column": hasattr(feature_column, "embedding_column") if feature_column is not None else False,
        "numeric_column": hasattr(feature_column, "numeric_column") if feature_column is not None else False,
    }

    pandas_input_fn_available = False
    numpy_input_fn_available = False
    if estimator is not None and hasattr(estimator, "inputs"):
        pandas_input_fn_available = hasattr(estimator.inputs, "pandas_input_fn")
        numpy_input_fn_available = hasattr(estimator.inputs, "numpy_input_fn")
    if compat_v1_estimator is not None and hasattr(compat_v1_estimator, "inputs"):
        pandas_input_fn_available = pandas_input_fn_available or hasattr(compat_v1_estimator.inputs, "pandas_input_fn")
        numpy_input_fn_available = numpy_input_fn_available or hasattr(compat_v1_estimator.inputs, "numpy_input_fn")

    return {
        "tensorflow_version": tf_version,
        "native_test_gate": _deepctr_native_estimator_gate(tf_version),
        "required_estimator_symbols": required_estimator_symbols,
        "tf_estimator_available": all(required_estimator_symbols.values()),
        "compat_v1_estimator_available": compat_v1_estimator is not None,
        "feature_column_symbols": feature_column_symbols,
        "feature_column_available": all(feature_column_symbols.values()),
        "pandas_input_fn_available": pandas_input_fn_available,
        "numpy_input_fn_available": numpy_input_fn_available,
    }


def _inspect_deepctr() -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "deepctr_imported": False,
        "deepctr_version": None,
        "deepctr_estimator_imported": False,
        "input_helpers": {},
        "constructors": {},
    }

    deepctr, err = _import_module("deepctr")
    if deepctr is None:
        report["deepctr_error"] = err
        return report

    report["deepctr_imported"] = True
    report["deepctr_version"] = getattr(deepctr, "__version__", "unknown")

    estimator_module, err = _import_module("deepctr.estimator")
    if estimator_module is None:
        report["deepctr_estimator_error"] = err
    else:
        report["deepctr_estimator_imported"] = True

    inputs_module, err = _import_module("deepctr.estimator.inputs")
    if inputs_module is None:
        report["input_helpers_error"] = err
    else:
        for name in ["input_fn_tfrecord", "input_fn_pandas"]:
            report["input_helpers"][name] = callable(getattr(inputs_module, name, None))

    models_module, err = _import_module("deepctr.estimator.models")
    if models_module is None:
        report["constructors_error"] = err
    else:
        for name in ESTIMATOR_CONSTRUCTORS:
            report["constructors"][name] = callable(getattr(models_module, name, None))

    return report


def _check_input_helper_construction(tf: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {"ok": False}
    inputs_module, err = _import_module("deepctr.estimator.inputs")
    if inputs_module is None:
        result["error"] = err
        return result

    feature_description = {
        "C1": tf.io.FixedLenFeature(shape=(1,), dtype=tf.int64),
        "I1": tf.io.FixedLenFeature(shape=(1,), dtype=tf.float32),
        "label": tf.io.FixedLenFeature(shape=(1,), dtype=tf.float32),
    }
    try:
        tfrecord_input_fn = inputs_module.input_fn_tfrecord(
            filenames=["synthetic-placeholder.tfrecords"],
            feature_description=feature_description,
            label="label",
            batch_size=2,
            num_epochs=1,
            shuffle_factor=0,
        )
        result["tfrecord_input_fn_callable"] = callable(tfrecord_input_fn)
    except Exception as exc:  # pragma: no cover - depends on local runtime
        result["tfrecord_input_fn_error"] = _clean_error(exc)

    result["ok"] = bool(result.get("tfrecord_input_fn_callable"))
    return result


def _construct_tiny_deepfm(tf: Any, tensorflow_report: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {"ok": False}

    if not tensorflow_report.get("tf_estimator_available"):
        result["unsupported_reason"] = (
            "DeepCTR Estimator constructors may import, but this TensorFlow build does not expose the "
            "top-level tf.estimator symbols that DeepCTR calls. Use Keras-style DeepCTR workflows or "
            "install a TensorFlow release that includes tf.estimator."
        )
        return result

    if not tensorflow_report.get("feature_column_available"):
        result["unsupported_reason"] = "TensorFlow feature_column APIs required by DeepCTR Estimators are missing."
        return result

    models_module, err = _import_module("deepctr.estimator.models")
    if models_module is None:
        result["error"] = err
        return result
    estimator_ctor = getattr(models_module, "DeepFMEstimator", None)
    if not callable(estimator_ctor):
        result["error"] = "DeepFMEstimator constructor is not callable."
        return result

    try:
        cat = tf.feature_column.categorical_column_with_identity("C1", num_buckets=4)
        dense = tf.feature_column.numeric_column("I1", shape=(1,))
        linear_feature_columns = [cat, dense]
        dnn_feature_columns = [tf.feature_column.embedding_column(cat, dimension=2), dense]
        with tempfile.TemporaryDirectory(prefix="deepctr-estimator-probe-") as model_dir:
            model = estimator_ctor(
                linear_feature_columns,
                dnn_feature_columns,
                dnn_hidden_units=(4,),
                task="binary",
                model_dir=model_dir,
                config=tf.estimator.RunConfig(tf_random_seed=2021),
            )
            result["constructed_class"] = model.__class__.__name__
            result["ok"] = True
    except Exception as exc:  # pragma: no cover - depends on local runtime
        result["error"] = _clean_error(exc)
    return result


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "status": "unsupported",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }

    tf, tf_err = _import_module("tensorflow")
    if tf is None:
        report["tensorflow_imported"] = False
        report["tensorflow_error"] = tf_err
        report["recommendation"] = "Install a TensorFlow build before using DeepCTR Estimator workflows."
        return report

    report["tensorflow_imported"] = True
    tensorflow_report = _inspect_tensorflow(tf)
    report.update(tensorflow_report)

    deepctr_report = _inspect_deepctr()
    report.update(deepctr_report)

    if args.check_input_helpers:
        report["input_helper_construction"] = _check_input_helper_construction(tf)

    if args.construct_estimator:
        report["tiny_deepfm_constructor"] = _construct_tiny_deepfm(tf, tensorflow_report)

    deepctr_ok = bool(report.get("deepctr_imported") and report.get("deepctr_estimator_imported"))
    constructors = report.get("constructors") or {}
    deepfm_imported = bool(constructors.get("DeepFMEstimator"))
    required_ok = bool(report.get("tf_estimator_available") and report.get("feature_column_available"))

    if deepctr_ok and deepfm_imported and required_ok:
        if args.construct_estimator and not report.get("tiny_deepfm_constructor", {}).get("ok"):
            report["status"] = "unsupported"
            report["recommendation"] = "DeepCTR imports, but the tiny Estimator constructor failed; inspect the constructor error."
        else:
            report["status"] = "supported"
            report["recommendation"] = "This runtime exposes the core APIs needed for DeepCTR Estimator workflows."
    elif not report.get("tf_estimator_available"):
        report["status"] = "unsupported"
        if not report.get("deepctr_imported"):
            report["recommendation"] = (
                "DeepCTR is not importable and this TensorFlow build does not expose top-level "
                "tf.estimator. Install deepctr only after choosing a TensorFlow release with Estimator "
                "support, or use Keras-style DeepCTR workflows in this environment."
            )
        else:
            report["recommendation"] = (
                "This TensorFlow build does not expose the top-level tf.estimator symbols that DeepCTR "
                "Estimator constructors call. DeepCTR may still import partially, but Estimator workflows "
                "are not supported here. Use Keras-style DeepCTR workflows or install a TensorFlow release "
                "with Estimator support."
            )
    elif not report.get("deepctr_imported"):
        report["status"] = "unsupported"
        report["recommendation"] = "Install deepctr after installing a compatible TensorFlow build."
    else:
        report["status"] = "unsupported"
        report["recommendation"] = "One or more required DeepCTR Estimator or TensorFlow feature-column APIs are unavailable."

    return report


def print_text_report(report: Dict[str, Any]) -> None:
    print(f"DeepCTR Estimator runtime status: {report['status']}")
    print(f"Python: {report.get('python_version')}")
    print(f"TensorFlow imported: {report.get('tensorflow_imported')}")
    if report.get("tensorflow_imported"):
        print(f"TensorFlow version: {report.get('tensorflow_version')}")
        print(f"tf.estimator available: {report.get('tf_estimator_available')}")
        print(f"tf.feature_column available: {report.get('feature_column_available')}")
        print(f"DeepCTR native Estimator test gate: {report.get('native_test_gate')}")
    else:
        print(f"TensorFlow error: {report.get('tensorflow_error')}")
    print(f"DeepCTR imported: {report.get('deepctr_imported')}")
    if report.get("deepctr_imported"):
        print(f"DeepCTR version: {report.get('deepctr_version')}")
        print(f"deepctr.estimator imported: {report.get('deepctr_estimator_imported')}")
        constructors = report.get("constructors") or {}
        available = [name for name in ESTIMATOR_CONSTRUCTORS if constructors.get(name)]
        print("Estimator constructors available: " + (", ".join(available) if available else "none"))
    elif report.get("deepctr_error"):
        print(f"DeepCTR error: {report.get('deepctr_error')}")

    if "input_helper_construction" in report:
        print(f"Input helper construction: {report['input_helper_construction']}")
    if "tiny_deepfm_constructor" in report:
        constructor = report["tiny_deepfm_constructor"]
        if constructor.get("ok"):
            print("Tiny DeepFMEstimator constructor: ok")
        else:
            print("Tiny DeepFMEstimator constructor: not supported")
            print(f"Reason: {constructor.get('unsupported_reason') or constructor.get('error')}")
    print(f"Recommendation: {report.get('recommendation')}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print a JSON report instead of text.")
    parser.add_argument(
        "--construct-estimator",
        action="store_true",
        help="Also construct a tiny DeepFMEstimator with synthetic feature columns and a temporary model_dir.",
    )
    parser.add_argument(
        "--check-input-helpers",
        action="store_true",
        help="Also construct a synthetic TFRecord input_fn wrapper without reading any files.",
    )
    args = parser.parse_args(argv)

    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    return 0 if report.get("status") == "supported" else 2


if __name__ == "__main__":
    raise SystemExit(main())
