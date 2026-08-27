#!/usr/bin/env python3
"""Safe smoke checks for cleanlab.experimental guidance.

Default behavior is deterministic and side-effect light:
  * exercises experimental.span_classification on a tiny two-sentence fixture;
  * exercises experimental.label_issues_batched on tiny in-memory and temporary
    file-backed .npy arrays.

The optional deep-learning probe only imports packages/modules. It does not
train models, download datasets, or write outside a temporary directory.
"""

from __future__ import annotations

import argparse
import importlib
import json
import pathlib
import sys
import tempfile
from typing import Any, Dict, List, Tuple

import numpy as np


EXPECTED_BATCHED_ISSUES = np.array([4, 7], dtype=int)


def _as_float_list(values: Any) -> List[float]:
    return [float(x) for x in np.asarray(values, dtype=float).ravel()]


def _assert_equal(name: str, observed: Any, expected: Any) -> None:
    if observed != expected:
        raise AssertionError(f"{name}: observed {observed!r}, expected {expected!r}")


def _assert_array_equal(name: str, observed: Any, expected: Any) -> None:
    observed_arr = np.asarray(observed)
    expected_arr = np.asarray(expected)
    if not np.array_equal(observed_arr, expected_arr):
        raise AssertionError(
            f"{name}: observed {observed_arr.tolist()!r}, expected {expected_arr.tolist()!r}"
        )


def _assert_allclose(name: str, observed: Any, expected: Any) -> None:
    observed_arr = np.asarray(observed, dtype=float)
    expected_arr = np.asarray(expected, dtype=float)
    if not np.allclose(observed_arr, expected_arr):
        raise AssertionError(
            f"{name}: observed {observed_arr.tolist()!r}, expected {expected_arr.tolist()!r}"
        )


def run_span_smoke() -> Dict[str, Any]:
    from cleanlab.experimental.span_classification import (
        find_label_issues,
        get_label_quality_scores,
    )

    labels = [[0, 0, 1, 1], [0, 0, 1]]
    pred_probs = [
        np.array([0.3, 0.2, 0.9, 0.1]),
        np.array([0.1, 0.1, 0.9]),
    ]

    issues = find_label_issues(labels, pred_probs)
    _assert_equal("span issues", issues, [(0, 3)])

    sentence_scores, token_info = get_label_quality_scores(labels, pred_probs)
    _assert_allclose("span sentence scores", sentence_scores, [0.1, 0.9])
    _assert_allclose("span first sentence token scores", token_info[0], [0.7, 0.8, 0.9, 0.1])

    return {
        "issues": [list(item) for item in issues],
        "sentence_scores": _as_float_list(sentence_scores),
        "first_sentence_token_scores": _as_float_list(token_info[0]),
    }


def _toy_classification_arrays() -> Tuple[np.ndarray, np.ndarray]:
    labels = np.array([0, 1, 0, 1, 0, 1, 0, 1], dtype=int)
    pred_probs = np.array(
        [
            [0.95, 0.05],
            [0.10, 0.90],
            [0.85, 0.15],
            [0.20, 0.80],
            [0.05, 0.95],
            [0.15, 0.85],
            [0.90, 0.10],
            [0.80, 0.20],
        ],
        dtype=float,
    )
    return labels, pred_probs


def run_batched_smoke(batch_size: int = 3) -> Dict[str, Any]:
    from cleanlab.experimental.label_issues_batched import find_label_issues_batched

    labels, pred_probs = _toy_classification_arrays()

    in_memory_issues = find_label_issues_batched(
        labels=labels,
        pred_probs=pred_probs,
        batch_size=batch_size,
        n_jobs=1,
        verbose=False,
    )
    _assert_array_equal("batched in-memory issues", in_memory_issues, EXPECTED_BATCHED_ISSUES)

    mask = find_label_issues_batched(
        labels=labels,
        pred_probs=pred_probs,
        batch_size=batch_size,
        n_jobs=1,
        verbose=False,
        return_mask=True,
    )
    _assert_array_equal("batched mask true indices", np.where(mask)[0], EXPECTED_BATCHED_ISSUES)

    with tempfile.TemporaryDirectory(prefix="cleanlab-experimental-smoke-") as tmpdir:
        tmp_path = pathlib.Path(tmpdir)
        labels_file = tmp_path / "labels.npy"
        pred_probs_file = tmp_path / "pred_probs.npy"
        np.save(labels_file, labels)
        np.save(pred_probs_file, pred_probs)
        file_backed_issues = find_label_issues_batched(
            labels_file=str(labels_file),
            pred_probs_file=str(pred_probs_file),
            batch_size=batch_size,
            n_jobs=1,
            verbose=False,
        )
    _assert_array_equal("batched file-backed issues", file_backed_issues, EXPECTED_BATCHED_ISSUES)

    return {
        "batch_size": int(batch_size),
        "in_memory_issue_indices": [int(x) for x in in_memory_issues],
        "mask_true_indices": [int(x) for x in np.where(mask)[0]],
        "file_backed_issue_indices": [int(x) for x in file_backed_issues],
    }


def _probe_import(import_name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(import_name)
    except Exception as exc:  # ImportError plus runtime errors from mismatched optional stacks.
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    return {
        "ok": True,
        "version": str(getattr(module, "__version__", "unknown")),
    }


def run_deep_learning_import_probe() -> Dict[str, Any]:
    package_imports = {
        name: _probe_import(name) for name in ["torch", "torchvision", "skorch"]
    }
    experimental_module_imports = {
        name: _probe_import(name)
        for name in [
            "cleanlab.experimental.mnist_pytorch",
            "cleanlab.experimental.cifar_cnn",
            "cleanlab.experimental.coteaching",
        ]
    }
    return {
        "packages": package_imports,
        "experimental_modules": experimental_module_imports,
        "trained_models": False,
        "downloaded_datasets": False,
    }


def _print_human(report: Dict[str, Any], errors: List[str]) -> None:
    print("cleanlab.experimental smoke report")
    print("==================================")
    core = report.get("core", {})
    if core.get("ok"):
        print("core: ok")
        print(f"  span issues: {core['span']['issues']}")
        print(f"  batched issue indices: {core['label_issues_batched']['in_memory_issue_indices']}")
        print(f"  file-backed issue indices: {core['label_issues_batched']['file_backed_issue_indices']}")
    else:
        print("core: failed")
        if "error" in core:
            print(f"  {core['error_type']}: {core['error']}")

    if "deep_learning_imports" in report:
        print("deep-learning import probe:")
        deep = report["deep_learning_imports"]
        for group_name in ["packages", "experimental_modules"]:
            print(f"  {group_name}:")
            for name, status in deep[group_name].items():
                if status["ok"]:
                    print(f"    {name}: ok ({status['version']})")
                else:
                    print(f"    {name}: missing/unusable ({status['error_type']}: {status['error']})")
        print("  trained_models: false")
        print("  downloaded_datasets: false")

    if errors:
        print("errors:")
        for error in errors:
            print(f"  - {error}")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch-size",
        type=int,
        default=3,
        help="Mini-batch size for the tiny label_issues_batched fixture (default: 3).",
    )
    parser.add_argument(
        "--check-deep-learning-imports",
        action="store_true",
        help="Probe torch/torchvision/skorch and experimental deep-learning modules without training.",
    )
    parser.add_argument(
        "--require-deep-learning-imports",
        action="store_true",
        help="Treat missing/unusable deep-learning imports as a failure. Implies --check-deep-learning-imports.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    report: Dict[str, Any] = {"core": {}}
    errors: List[str] = []

    try:
        report["core"] = {
            "ok": True,
            "span": run_span_smoke(),
            "label_issues_batched": run_batched_smoke(batch_size=args.batch_size),
        }
    except Exception as exc:
        report["core"] = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        errors.append(
            "core experimental smoke failed; verify base cleanlab dependencies and installed version"
        )

    if args.check_deep_learning_imports or args.require_deep_learning_imports:
        deep_report = run_deep_learning_import_probe()
        report["deep_learning_imports"] = deep_report
        if args.require_deep_learning_imports:
            failed = []
            for group in ["packages", "experimental_modules"]:
                failed.extend(
                    name for name, status in deep_report[group].items() if not status.get("ok")
                )
            if failed:
                errors.append("required deep-learning imports failed: " + ", ".join(failed))

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report, errors)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
