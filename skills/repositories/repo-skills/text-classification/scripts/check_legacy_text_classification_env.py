#!/usr/bin/env python3
"""Safe environment smoke check for brightmart/text_classification.

This script intentionally does not import model modules, create TensorFlow sessions,
inspect devices, read datasets/checkpoints, use the network, or run training.
"""

from __future__ import print_function

import argparse
import ast
import contextlib
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import sys
import warnings


REPRESENTATIVE_SOURCES = (
    ("data-helper", "a02_TextCNN/data_util.py", True),
    ("fasttext-classifier", "a01_FastText/p6_fastTextB_model_multilabel.py", False),
    ("textcnn-classifier", "a02_TextCNN/p7_TextCNN_model.py", False),
    ("seq2seq-attention", "a06_Seq2seqWithAttention/a1_seq2seq_attention_model.py", False),
    ("transformer", "a07_Transformer/a2_transformer.py", False),
    ("entity-network", "a08_EntityNetwork/a3_entity_network.py", False),
    ("dynamic-memory-network", "a09_DynamicMemoryNet/a8_dynamic_memory_network.py", False),
    ("two-cnn-relation", "aa6_TwoCNNTextRelation/p9_twoCNNTextRelation_model.py", False),
    ("ensemble-workflow", "a08_predict_ensemble.py", False),
)


def _parser():
    parser = argparse.ArgumentParser(
        description=(
            "Safely report the Python 3.7/TensorFlow 1.x legacy capabilities "
            "needed by brightmart/text_classification."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit deterministic, sorted JSON instead of human-readable text",
    )
    parser.add_argument(
        "--repo-root",
        metavar="PATH",
        help=(
            "repository root to inspect (default: inferred from this script's "
            "skills/disco/text-classification/scripts location)"
        ),
    )
    return parser


def _default_repo_root():
    return Path(__file__).resolve().parents[4]


def _quiet_import(module_name):
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with contextlib.redirect_stdout(captured_stdout):
                with contextlib.redirect_stderr(captured_stderr):
                    module = importlib.import_module(module_name)
        return module, None
    except BaseException as exc:  # Imports can raise non-Exception legacy errors.
        return None, type(exc).__name__


def _package_record(module_name):
    try:
        discoverable = importlib.util.find_spec(module_name) is not None
        discovery_error = None
    except BaseException as exc:
        discoverable = False
        discovery_error = type(exc).__name__

    module = None
    import_error = None
    if discoverable:
        module, import_error = _quiet_import(module_name)

    version = None
    if module is not None:
        raw_version = getattr(module, "__version__", None)
        if raw_version is not None:
            version = str(raw_version)

    return {
        "discoverable": discoverable,
        "discovery_error": discovery_error,
        "import_error": import_error,
        "importable": module is not None,
        "version": version,
    }, module


def _has_path(obj, dotted_path):
    current = obj
    for part in dotted_path.split("."):
        if current is None or not hasattr(current, part):
            return False
        current = getattr(current, part)
    return True


def _tensorflow_record(tensorflow_package, tf):
    record = dict(tensorflow_package)
    indicators = {
        "app_flags": False,
        "compat_v1": False,
        "compat_v1_disable_eager_execution": False,
        "compat_v1_placeholder": False,
        "compat_v1_session": False,
        "contrib": False,
        "contrib_layers_batch_norm": False,
        "contrib_layers_optimize_loss": False,
        "eager_execution": None,
        "placeholder": False,
        "session": False,
        "tf1_version": False,
    }

    if tf is not None:
        indicators["session"] = _has_path(tf, "Session")
        indicators["placeholder"] = _has_path(tf, "placeholder")
        indicators["app_flags"] = _has_path(tf, "app.flags")
        indicators["contrib"] = _has_path(tf, "contrib")
        indicators["contrib_layers_optimize_loss"] = _has_path(
            tf, "contrib.layers.optimize_loss"
        )
        indicators["contrib_layers_batch_norm"] = _has_path(
            tf, "contrib.layers.batch_norm"
        )
        indicators["compat_v1"] = _has_path(tf, "compat.v1")
        indicators["compat_v1_session"] = _has_path(tf, "compat.v1.Session")
        indicators["compat_v1_placeholder"] = _has_path(tf, "compat.v1.placeholder")
        indicators["compat_v1_disable_eager_execution"] = _has_path(
            tf, "compat.v1.disable_eager_execution"
        )
        version = record.get("version") or ""
        indicators["tf1_version"] = version.split(".", 1)[0] == "1"
        executing_eagerly = getattr(tf, "executing_eagerly", None)
        if callable(executing_eagerly):
            try:
                indicators["eager_execution"] = bool(executing_eagerly())
            except BaseException:
                indicators["eager_execution"] = None

    record["indicators"] = indicators
    record["legacy_source_compatible"] = bool(
        record["importable"]
        and indicators["tf1_version"]
        and indicators["session"]
        and indicators["placeholder"]
        and indicators["app_flags"]
        and indicators["contrib"]
        and indicators["contrib_layers_optimize_loss"]
        and indicators["contrib_layers_batch_norm"]
        and indicators["eager_execution"] is False
    )
    return record


def _tflearn_record(tflearn_package, tflearn):
    record = dict(tflearn_package)
    data_utils = None
    data_utils_error = None
    if tflearn is not None:
        data_utils, data_utils_error = _quiet_import("tflearn.data_utils")
    record["data_utils_importable"] = data_utils is not None
    record["data_utils_import_error"] = data_utils_error
    record["pad_sequences"] = _has_path(data_utils, "pad_sequences")
    record["to_categorical"] = _has_path(data_utils, "to_categorical")
    record["legacy_helper_compatible"] = bool(
        record["importable"]
        and record["data_utils_importable"]
        and record["pad_sequences"]
    )
    return record


def _top_level_imports(tree):
    names = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
    return sorted(names)


def _source_records(repo_root):
    records = []
    for name, relative_path, safe_helper in REPRESENTATIVE_SOURCES:
        path = repo_root / relative_path
        record = {
            "ast_parseable": False,
            "error": None,
            "exists": path.is_file(),
            "name": name,
            "path": relative_path,
            "safe_helper": safe_helper,
            "top_level_imports": [],
        }
        if record["exists"]:
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=relative_path)
                record["ast_parseable"] = True
                record["top_level_imports"] = _top_level_imports(tree)
            except BaseException as exc:
                record["error"] = type(exc).__name__
        records.append(record)
    return records


def _import_safe_helper(repo_root, source_records):
    relative_path = "a02_TextCNN/data_util.py"
    path = repo_root / relative_path
    source_record = next(
        (item for item in source_records if item["path"] == relative_path), None
    )
    result = {
        "attempted": False,
        "error": None,
        "importable": False,
        "path": relative_path,
        "policy": "Only this lightweight data helper is imported; model modules are never imported.",
    }
    if source_record is None or not source_record["exists"]:
        result["error"] = "FileNotFoundError"
        return result
    if not source_record["ast_parseable"]:
        result["error"] = source_record["error"] or "SyntaxError"
        return result

    result["attempted"] = True
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    try:
        spec = importlib.util.spec_from_file_location(
            "_text_classification_smoke_data_util", str(path)
        )
        if spec is None or spec.loader is None:
            result["error"] = "ImportSpecUnavailable"
            return result
        module = importlib.util.module_from_spec(spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with contextlib.redirect_stdout(captured_stdout):
                with contextlib.redirect_stderr(captured_stderr):
                    spec.loader.exec_module(module)
        result["importable"] = True
    except BaseException as exc:
        result["error"] = type(exc).__name__
    return result


def _add_failure(failures, failure_id, condition):
    if not condition:
        failures.append(failure_id)


def _build_report(repo_root):
    # Suppress GPU visibility before TensorFlow or TFLearn can be imported. The
    # check never asks TensorFlow to enumerate devices or create a session.
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

    numpy_record, numpy_module = _package_record("numpy")
    h5py_record, h5py_module = _package_record("h5py")
    tensorflow_package, tf_module = _package_record("tensorflow")
    tensorflow_record = _tensorflow_record(tensorflow_package, tf_module)
    tflearn_package, tflearn_module = _package_record("tflearn")
    tflearn_record = _tflearn_record(tflearn_package, tflearn_module)

    python_target = sys.version_info[:2] == (3, 7)
    python_record = {
        "implementation": platform.python_implementation(),
        "target": "CPython/Python 3.7-era legacy environment",
        "target_compatible": python_target,
        "version": "{}.{}.{}".format(
            sys.version_info.major, sys.version_info.minor, sys.version_info.micro
        ),
    }

    source_records = _source_records(repo_root)
    helper_import = _import_safe_helper(repo_root, source_records)
    missing_sources = sorted(
        item["path"] for item in source_records if not item["exists"]
    )
    unparsable_sources = sorted(
        item["path"]
        for item in source_records
        if item["exists"] and not item["ast_parseable"]
    )

    failures = []
    _add_failure(failures, "python-3.7", python_target)
    _add_failure(failures, "numpy-import", numpy_module is not None)
    _add_failure(failures, "h5py-import", h5py_module is not None)
    _add_failure(
        failures,
        "tensorflow-1.x-direct-apis",
        tensorflow_record["legacy_source_compatible"],
    )
    _add_failure(
        failures,
        "tflearn-data-utils",
        tflearn_record["legacy_helper_compatible"],
    )
    _add_failure(failures, "representative-source-discovery", not missing_sources)
    _add_failure(failures, "safe-helper-import", helper_import["importable"])

    advice = []
    if not python_target:
        advice.append(
            "Use an isolated Python 3.7 environment; the checked-in scripts mix "
            "Python 2-era code with TensorFlow packages whose legacy wheels do not "
            "support current Python releases."
        )
    if numpy_module is None:
        advice.append("Install a NumPy version compatible with the selected TensorFlow 1.x wheel.")
    if h5py_module is None:
        advice.append("Install a legacy-compatible h5py build before reading repository HDF5 caches.")
    if tf_module is None:
        advice.append(
            "Install TensorFlow 1.x in the isolated legacy environment; no model, "
            "network, GPU, or training operation was attempted."
        )
    elif not tensorflow_record["legacy_source_compatible"]:
        indicators = tensorflow_record["indicators"]
        if not indicators["tf1_version"]:
            advice.append(
                "The repository imports TensorFlow 1.x APIs directly. tf.compat.v1 "
                "is only an adaptation clue and does not restore tf.contrib."
            )
        if not (indicators["session"] and indicators["placeholder"] and indicators["app_flags"]):
            advice.append(
                "Use a runtime exposing top-level tf.Session, tf.placeholder, and "
                "tf.app.flags, or perform a deliberate source migration."
            )
        if not (
            indicators["contrib"]
            and indicators["contrib_layers_optimize_loss"]
            and indicators["contrib_layers_batch_norm"]
        ):
            advice.append(
                "Use genuine TensorFlow 1.x or replace every required tf.contrib "
                "call; compat.v1 alone is insufficient for this checkout."
            )
        if indicators["eager_execution"] is True:
            advice.append(
                "Run in a fresh static-graph process with eager execution disabled "
                "before constructing any repository graph."
            )
    if not tflearn_record["legacy_helper_compatible"]:
        advice.append(
            "Install a TFLearn release matched to TensorFlow 1.x and confirm "
            "tflearn.data_utils.pad_sequences is importable."
        )
    if missing_sources:
        advice.append(
            "Point --repo-root at the brightmart/text_classification checkout; "
            "missing representative paths: {}.".format(", ".join(missing_sources))
        )
    if unparsable_sources:
        advice.append(
            "These representative files need Python-3 syntax review before import: {}.".format(
                ", ".join(unparsable_sources)
            )
        )
    if not helper_import["importable"]:
        advice.append(
            "Resolve the lightweight a02_TextCNN/data_util.py imports before using "
            "repository data helpers; model modules were intentionally not imported."
        )
    if not advice:
        advice.append(
            "Required legacy indicators are present. Validate data, label maps, and "
            "checkpoint compatibility separately before any model run."
        )

    return {
        "advice": advice,
        "checks": {
            "h5py": h5py_record,
            "numpy": numpy_record,
            "python": python_record,
            "safe_helper_import": helper_import,
            "sources": source_records,
            "tensorflow": tensorflow_record,
            "tflearn": tflearn_record,
        },
        "failed_requirements": failures,
        "policy": {
            "gpu_visibility_disabled": True,
            "model_modules_imported": False,
            "network_used": False,
            "sessions_created": False,
            "training_run": False,
        },
        "repo_root": str(repo_root),
        "status": "pass" if not failures else "fail",
    }


def _yes_no(value):
    if value is None:
        return "unknown"
    return "yes" if value else "no"


def _package_line(name, record):
    version = record.get("version") or "unknown"
    error = record.get("import_error") or "none"
    return "{}: importable={} version={} import_error={}".format(
        name, _yes_no(record.get("importable")), version, error
    )


def _render_text(report):
    checks = report["checks"]
    tf_record = checks["tensorflow"]
    indicators = tf_record["indicators"]
    lines = [
        "legacy text classification environment smoke check",
        "status: {}".format(report["status"].upper()),
        "repo_root: {}".format(report["repo_root"]),
        "python: version={} target_compatible={}".format(
            checks["python"]["version"],
            _yes_no(checks["python"]["target_compatible"]),
        ),
        _package_line("tensorflow", tf_record),
        "tensorflow indicators: tf1_version={} session={} placeholder={} app_flags={} contrib={} contrib_optimize_loss={} contrib_batch_norm={} eager={} compat_v1={}".format(
            _yes_no(indicators["tf1_version"]),
            _yes_no(indicators["session"]),
            _yes_no(indicators["placeholder"]),
            _yes_no(indicators["app_flags"]),
            _yes_no(indicators["contrib"]),
            _yes_no(indicators["contrib_layers_optimize_loss"]),
            _yes_no(indicators["contrib_layers_batch_norm"]),
            _yes_no(indicators["eager_execution"]),
            _yes_no(indicators["compat_v1"]),
        ),
        "tensorflow compat.v1 indicators: session={} placeholder={} disable_eager_execution={}".format(
            _yes_no(indicators["compat_v1_session"]),
            _yes_no(indicators["compat_v1_placeholder"]),
            _yes_no(indicators["compat_v1_disable_eager_execution"]),
        ),
        _package_line("tflearn", checks["tflearn"]),
        "tflearn data_utils: importable={} pad_sequences={} to_categorical={}".format(
            _yes_no(checks["tflearn"]["data_utils_importable"]),
            _yes_no(checks["tflearn"]["pad_sequences"]),
            _yes_no(checks["tflearn"]["to_categorical"]),
        ),
        _package_line("numpy", checks["numpy"]),
        _package_line("h5py", checks["h5py"]),
        "representative sources:",
    ]
    for item in checks["sources"]:
        lines.append(
            "- {}: exists={} ast_parseable={} safe_helper={}".format(
                item["path"],
                _yes_no(item["exists"]),
                _yes_no(item["ast_parseable"]),
                _yes_no(item["safe_helper"]),
            )
        )
    helper = checks["safe_helper_import"]
    lines.append(
        "safe helper import: path={} attempted={} importable={} error={}".format(
            helper["path"],
            _yes_no(helper["attempted"]),
            _yes_no(helper["importable"]),
            helper["error"] or "none",
        )
    )
    lines.append("failed requirements: {}".format(
        ", ".join(report["failed_requirements"]) or "none"
    ))
    lines.append("advice:")
    for item in report["advice"]:
        lines.append("- {}".format(item))
    return "\n".join(lines)


def main(argv=None):
    args = _parser().parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else _default_repo_root()
    report = _build_report(repo_root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_text(report))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
