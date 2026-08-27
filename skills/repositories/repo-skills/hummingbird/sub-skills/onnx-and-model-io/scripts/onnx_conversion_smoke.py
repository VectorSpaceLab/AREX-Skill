#!/usr/bin/env python3
"""Deterministic Hummingbird ONNX conversion smoke test.

The default path trains a tiny sklearn classifier, converts it to Hummingbird's
ONNX backend, and checks label/probability parity. It writes no artifact unless
--output is provided. Use --onnxml to additionally exercise an ONNX-ML source
model produced by skl2onnx or onnxmltools.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple


class MissingDependency(RuntimeError):
    """Raised when a selected smoke path needs an unavailable dependency."""

    def __init__(self, missing: Dict[str, Dict[str, Any]], hint: str):
        super().__init__(hint)
        self.missing = missing
        self.hint = hint


def import_status(module_name: str) -> Dict[str, Any]:
    """Return importability/version information without raising ImportError."""

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            module = importlib.import_module(module_name)
    except Exception as exc:  # dependency import hooks can raise more than ImportError
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    status = {"ok": True, "version": getattr(module, "__version__", None)}
    if caught:
        status["warnings"] = [str(w.message) for w in caught]
    return status


def collect_dependency_status() -> Dict[str, Dict[str, Any]]:
    modules = [
        "numpy",
        "sklearn",
        "torch",
        "onnx",
        "onnxruntime",
        "hummingbird.ml",
        "skl2onnx",
        "onnxmltools",
        "onnxconverter_common",
    ]
    return {name: import_status(name) for name in modules}


def require_modules(status: Dict[str, Dict[str, Any]], names: Iterable[str], hint: str) -> None:
    missing = {name: status[name] for name in names if not status.get(name, {}).get("ok")}
    if missing:
        raise MissingDependency(missing, hint)


def build_dataset() -> Tuple[Any, Any]:
    import numpy as np

    X = np.array(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [2.0, 0.0],
            [2.0, 1.0],
        ],
        dtype=np.float32,
    )
    y = np.array([0, 0, 1, 1, 1, 0], dtype=np.int64)
    return X, y


def build_model(model_kind: str, X: Any, y: Any) -> Any:
    if model_kind == "decision-tree":
        from sklearn.tree import DecisionTreeClassifier

        model = DecisionTreeClassifier(max_depth=2, random_state=0)
    elif model_kind == "logistic-regression":
        from sklearn.linear_model import LogisticRegression

        model = LogisticRegression(solver="liblinear", random_state=0)
    else:  # argparse should prevent this
        raise ValueError(f"Unsupported model kind: {model_kind}")
    return model.fit(X, y)


def assert_classifier_parity(source_model: Any, hb_model: Any, X: Any, rtol: float, atol: float) -> Dict[str, Any]:
    import numpy as np

    expected_labels = source_model.predict(X)
    actual_labels = hb_model.predict(X)
    expected_proba = source_model.predict_proba(X)
    actual_proba = hb_model.predict_proba(X)

    if actual_labels.shape != expected_labels.shape:
        raise AssertionError(f"label shape mismatch: {actual_labels.shape} != {expected_labels.shape}")
    if actual_proba.shape != expected_proba.shape:
        raise AssertionError(f"probability shape mismatch: {actual_proba.shape} != {expected_proba.shape}")

    np.testing.assert_array_equal(actual_labels, expected_labels)
    np.testing.assert_allclose(actual_proba, expected_proba, rtol=rtol, atol=atol)

    return {
        "labels": actual_labels.tolist(),
        "label_shape": list(actual_labels.shape),
        "proba_shape": list(actual_proba.shape),
        "max_abs_proba_diff": float(np.max(np.abs(actual_proba - expected_proba))),
    }


def convert_direct_to_onnx(source_model: Any, X: Any) -> Any:
    import hummingbird.ml

    return hummingbird.ml.convert(source_model, "onnx", X)


def build_onnxml_model(source_model: Any, X: Any, tool: str) -> Any:
    if tool == "skl2onnx":
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType

        return convert_sklearn(source_model, initial_types=[("input", FloatTensorType([None, X.shape[1]]))])
    if tool == "onnxmltools":
        from onnxmltools import convert_sklearn
        from onnxmltools.convert.common.data_types import FloatTensorType

        return convert_sklearn(
            source_model,
            initial_types=[("input", FloatTensorType([None, X.shape[1]]))],
            target_opset=11,
        )
    raise ValueError(f"Unsupported ONNX-ML tool: {tool}")


def convert_onnxml_to_hummingbird_onnx(source_model: Any, X: Any, tool: str) -> Any:
    import hummingbird.ml

    onnx_ml_model = build_onnxml_model(source_model, X, tool)
    return hummingbird.ml.convert(onnx_ml_model, "onnx", X)


def output_paths(output: str) -> Tuple[Path, Path]:
    requested = Path(output)
    requested_str = str(requested)
    if requested_str.endswith(".zip"):
        base = Path(requested_str[:-4])
    else:
        base = requested
    zip_path = Path(str(base) + ".zip")
    return base, zip_path


def save_and_verify(hb_model: Any, X: Any, output: str) -> Dict[str, Any]:
    import hummingbird.ml

    base, zip_path = output_paths(output)
    base.parent.mkdir(parents=True, exist_ok=True)
    if base.exists():
        raise RuntimeError(f"Refusing to save: unzipped output path already exists: {base}")
    if zip_path.exists():
        raise RuntimeError(f"Refusing to overwrite existing archive: {zip_path}")

    import contextlib
    import io

    # Hummingbird's save() prints the digest; suppress it so --json remains valid JSON.
    with contextlib.redirect_stdout(io.StringIO()):
        digest = hb_model.save(output)
    loaded_specific = hummingbird.ml.ONNXContainer.load(output, digest=digest)
    loaded_generic = hummingbird.ml.load(output, digest=digest)

    original_labels = hb_model.predict(X)
    specific_labels = loaded_specific.predict(X)
    generic_labels = loaded_generic.predict(X)

    if list(specific_labels) != list(original_labels):
        raise AssertionError("ONNXContainer.load predictions differ from saved model predictions")
    if list(generic_labels) != list(original_labels):
        raise AssertionError("hummingbird.ml.load predictions differ from saved model predictions")

    return {
        "zip_path": str(zip_path),
        "digest": digest,
        "specific_load_class": type(loaded_specific).__name__,
        "generic_load_class": type(loaded_generic).__name__,
    }


def run(args: argparse.Namespace) -> Dict[str, Any]:
    status = collect_dependency_status()
    require_modules(
        status,
        ["numpy", "sklearn", "torch", "onnx", "onnxruntime", "hummingbird.ml"],
        "The default ONNX smoke requires Hummingbird, sklearn, torch, onnx, and onnxruntime in the same environment.",
    )

    X, y = build_dataset()
    model = build_model(args.model, X, y)

    direct_hb = convert_direct_to_onnx(model, X)
    direct_check = assert_classifier_parity(model, direct_hb, X, args.rtol, args.atol)

    result: Dict[str, Any] = {
        "status": "ok",
        "model": args.model,
        "backend": "onnx",
        "container_class": type(direct_hb).__name__,
        "dependency_status": status,
        "direct_sklearn_to_onnx": direct_check,
    }

    if hasattr(direct_hb, "model") and getattr(direct_hb.model, "opset_import", None):
        result["onnx_opsets"] = [entry.version for entry in direct_hb.model.opset_import]
        result["onnx_graph_name"] = direct_hb.model.graph.name

    if args.onnxml:
        require_modules(
            status,
            [args.onnxml_tool],
            f"The --onnxml path needs an importable {args.onnxml_tool} package.",
        )
        onnxml_hb = convert_onnxml_to_hummingbird_onnx(model, X, args.onnxml_tool)
        result["onnxml_to_onnx"] = {
            "tool": args.onnxml_tool,
            **assert_classifier_parity(model, onnxml_hb, X, args.rtol, args.atol),
            "container_class": type(onnxml_hb).__name__,
        }

    if args.output:
        result["saved_artifact"] = save_and_verify(direct_hb, X, args.output)

    return result


def emit(result: Dict[str, Any], json_mode: bool, stream: Any = sys.stdout) -> None:
    if json_mode:
        print(json.dumps(result, indent=2, sort_keys=True), file=stream)
    else:
        status = result.get("status", "unknown")
        if status == "ok":
            labels = result.get("direct_sklearn_to_onnx", {}).get("labels")
            print(f"onnx_conversion_smoke ok: labels={labels}", file=stream)
            if "saved_artifact" in result:
                saved = result["saved_artifact"]
                print(f"saved {saved['zip_path']} digest={saved['digest']}", file=stream)
        else:
            print(f"onnx_conversion_smoke {status}: {result.get('message', '')}", file=stream)


def parse_args(argv: Any = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        choices=["decision-tree", "logistic-regression"],
        default="logistic-regression",
        help="Tiny deterministic sklearn classifier to train before conversion; logistic-regression is the default because it is stable for ONNX-ML smoke mode.",
    )
    parser.add_argument(
        "--onnxml",
        action="store_true",
        help="Also build an ONNX-ML source model and convert that model to Hummingbird ONNX.",
    )
    parser.add_argument(
        "--onnxml-tool",
        choices=["skl2onnx", "onnxmltools"],
        default="skl2onnx",
        help="Tool used to create the ONNX-ML source model when --onnxml is set.",
    )
    parser.add_argument(
        "--output",
        help="Optional artifact base name or .zip path. No model artifact is written unless this is provided.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--rtol", type=float, default=1e-6, help="Relative tolerance for probability parity.")
    parser.add_argument("--atol", type=float, default=1e-6, help="Absolute tolerance for probability parity.")
    return parser.parse_args(argv)


def main(argv: Any = None) -> int:
    args = parse_args(argv)
    try:
        result = run(args)
    except MissingDependency as exc:
        result = {
            "status": "missing_dependency",
            "message": exc.hint,
            "missing": exc.missing,
            "hint": "Install the missing package(s) in the same environment, then rerun the smoke.",
        }
        emit(result, args.json, stream=sys.stderr if not args.json else sys.stdout)
        return 2
    except Exception as exc:
        result = {"status": "error", "message": f"{type(exc).__name__}: {exc}"}
        emit(result, args.json, stream=sys.stderr if not args.json else sys.stdout)
        return 1

    emit(result, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
