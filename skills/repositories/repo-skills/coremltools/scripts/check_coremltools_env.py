#!/usr/bin/env python3
"""Report coremltools version, optional dependency gates, and safe smoke status.

This diagnostic imports the package installed in the current Python environment.
It does not run prediction, download models, train, or require the original repo.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict


def _json_default(value: Any) -> str:
    return str(value)


def _import_report() -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "ok": False,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
    }
    try:
        import coremltools as ct  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller env
        report.update(
            {
                "error": "failed to import coremltools",
                "details": f"{type(exc).__name__}: {exc}",
            }
        )
        return report

    report.update(
        {
            "ok": True,
            "coremltools_version": getattr(ct, "__version__", "unknown"),
            "compute_units": [unit.name for unit in getattr(ct, "ComputeUnit")],
            "macos_runtime_expected_for_prediction": sys.platform == "darwin",
        }
    )

    try:
        from coremltools import _deps  # type: ignore

        report["optional_dependencies"] = {
            "torch": bool(getattr(_deps, "_HAS_TORCH", False)),
            "tensorflow": bool(getattr(_deps, "_HAS_TF", False)),
            "sklearn": bool(getattr(_deps, "_HAS_SKLEARN", False)),
            "xgboost": bool(getattr(_deps, "_HAS_XGBOOST", False)),
            "lightgbm": bool(getattr(_deps, "_HAS_LIGHTGBM", False)),
            "libsvm": bool(getattr(_deps, "_HAS_LIBSVM", False)),
            "executorch": bool(getattr(_deps, "_HAS_EXECUTORCH", False)),
            "torchao": bool(getattr(_deps, "_HAS_TORCHAO", False)),
        }
    except Exception as exc:  # pragma: no cover
        report["optional_dependency_error"] = f"{type(exc).__name__}: {exc}"

    try:
        import coremltools.optimize.coreml as cto  # noqa: F401

        report["optimize_coreml_import"] = True
    except Exception as exc:  # pragma: no cover
        report["optimize_coreml_import"] = False
        report["optimize_coreml_error"] = f"{type(exc).__name__}: {exc}"

    try:
        import coremltools.optimize.torch as cto_torch  # noqa: F401

        report["optimize_torch_import"] = True
    except Exception as exc:  # pragma: no cover
        report["optimize_torch_import"] = False
        report["optimize_torch_error"] = f"{type(exc).__name__}: {exc}"

    return report


def _run_mil_smoke() -> Dict[str, Any]:
    try:
        import numpy as np
        import coremltools as ct
        from coremltools.converters.mil import Builder as mb
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "stage": "import", "error": f"{type(exc).__name__}: {exc}"}

    try:
        @mb.program(input_specs=[mb.TensorSpec(shape=(1, 2))])
        def prog(x):
            return mb.add(x=x, y=np.array([1.0, 2.0], dtype=np.float32), name="plus")

        mlmodel = ct.convert(prog, convert_to="mlprogram", skip_model_load=True)
        spec = mlmodel.get_spec()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "coremltools_env_smoke.mlpackage"
            mlmodel.save(str(path))
            saved = path.is_dir()
        return {
            "ok": True,
            "spec_type": spec.WhichOneof("Type"),
            "specification_version": int(spec.specificationVersion),
            "saved_mlpackage": saved,
        }
    except Exception as exc:  # noqa: BLE001 - diagnostic should report broad failures.
        hint = None
        text = str(exc)
        if "BlobWriter" in text or "libmilstorage" in text:
            hint = "Install a coremltools wheel/build with libmilstoragepython for ML Program package writing."
        elif "CoreML.framework" in text or "MLModelProxy" in text:
            hint = "Prediction/runtime loading needs a compatible macOS Core ML runtime."
        return {"ok": False, "stage": "mil_smoke", "error": f"{type(exc).__name__}: {exc}", "hint": hint}


def _print_text(report: Dict[str, Any]) -> None:
    print(f"Python: {report.get('python')} on {report.get('platform')} ({report.get('machine')})")
    if not report.get("ok"):
        print(f"coremltools import: FAILED - {report.get('details') or report.get('error')}")
        return
    print(f"coremltools: {report.get('coremltools_version')}")
    print(f"Compute units enum: {', '.join(report.get('compute_units', []))}")
    optional = report.get("optional_dependencies", {})
    if optional:
        print("Optional dependency gates:")
        for name in sorted(optional):
            print(f"  {name}: {'available' if optional[name] else 'missing'}")
    print(f"optimize.coreml import: {report.get('optimize_coreml_import')}")
    print(f"optimize.torch import: {report.get('optimize_torch_import')}")
    if not report.get("macos_runtime_expected_for_prediction"):
        print("Prediction/runtime note: MLModel.predict, compiled models, and device/plan APIs normally require macOS Core ML runtime.")
    if "mil_smoke" in report:
        smoke = report["mil_smoke"]
        print(f"MIL conversion smoke: {'passed' if smoke.get('ok') else 'failed'}")
        if not smoke.get("ok"):
            print(f"  {smoke.get('error')}")
            if smoke.get("hint"):
                print(f"  Hint: {smoke['hint']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check coremltools import, optional dependency gates, and an optional MIL conversion smoke.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    parser.add_argument("--smoke", action="store_true", help="Run a tiny MIL-to-MLProgram conversion/save smoke. Does not run prediction.")
    args = parser.parse_args()

    report = _import_report()
    if args.smoke and report.get("ok"):
        report["mil_smoke"] = _run_mil_smoke()

    if args.json:
        print(json.dumps(report, indent=2, default=_json_default))
    else:
        _print_text(report)
    return 0 if report.get("ok") and (not args.smoke or report.get("mil_smoke", {}).get("ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
