#!/usr/bin/env python3
"""Safe NannyML installation smoke checks for this repo skill.

The script verifies public package facts only. It does not read source-repo files,
run native tests, touch network services, use credentials, or require GPUs.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple


def _ok(name: str, details: Any = None) -> Dict[str, Any]:
    return {"name": name, "status": "PASS", "details": details}


def _warn(name: str, details: Any = None) -> Dict[str, Any]:
    return {"name": name, "status": "WARN", "details": details}


def _fail(name: str, details: Any = None) -> Dict[str, Any]:
    return {"name": name, "status": "FAIL", "details": details}


def check_imports() -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    try:
        import nannyml as nml
    except Exception as exc:  # pragma: no cover - diagnostic path
        return [_fail("import nannyml", repr(exc))]

    checks.append(_ok("import nannyml", {"version": getattr(nml, "__version__", "unknown")}))
    for name in [
        "CBPE",
        "DLE",
        "PerformanceCalculator",
        "UnivariateDriftCalculator",
        "DataReconstructionDriftCalculator",
        "DomainClassifierCalculator",
        "MissingValuesCalculator",
        "UnseenValuesCalculator",
        "NumericalRangeCalculator",
        "RawFilesWriter",
        "PickleFileWriter",
    ]:
        checks.append(_ok(f"top-level export {name}") if hasattr(nml, name) else _fail(f"top-level export {name}"))
    return checks


def check_signatures() -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    import nannyml as nml

    targets: List[Tuple[str, Callable[..., Any], List[str]]] = [
        ("CBPE", nml.CBPE, ["metrics", "y_pred_proba", "y_true", "problem_type"]),
        ("DLE", nml.DLE, ["feature_column_names", "y_pred", "y_true"]),
        ("PerformanceCalculator", nml.PerformanceCalculator, ["metrics", "y_true", "problem_type"]),
        ("UnivariateDriftCalculator", nml.UnivariateDriftCalculator, ["column_names"]),
        ("DataReconstructionDriftCalculator", nml.DataReconstructionDriftCalculator, ["column_names"]),
        ("DomainClassifierCalculator", nml.DomainClassifierCalculator, ["feature_column_names"]),
        ("MissingValuesCalculator", nml.MissingValuesCalculator, ["column_names"]),
        ("UnseenValuesCalculator", nml.UnseenValuesCalculator, ["column_names"]),
        ("NumericalRangeCalculator", nml.NumericalRangeCalculator, ["column_names"]),
    ]
    for display_name, obj, required_params in targets:
        sig = inspect.signature(obj)
        missing = [p for p in required_params if p not in sig.parameters]
        if missing:
            checks.append(_fail(f"signature {display_name}", {"missing": missing, "signature": str(sig)}))
        else:
            checks.append(_ok(f"signature {display_name}", str(sig)))
    return checks


def check_datasets() -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    import nannyml as nml

    loaders = [
        nml.load_synthetic_binary_classification_dataset,
        nml.load_synthetic_car_loan_dataset,
        nml.load_synthetic_multiclass_classification_dataset,
        nml.load_synthetic_car_price_dataset,
        nml.load_synthetic_car_loan_data_quality_dataset,
    ]
    for loader in loaders:
        try:
            reference, analysis, analysis_targets = loader()
            details = {
                "reference_shape": list(reference.shape),
                "analysis_shape": list(analysis.shape),
                "analysis_targets_shape": list(analysis_targets.shape),
            }
            if reference.empty or analysis.empty or analysis_targets.empty:
                checks.append(_fail(f"dataset {loader.__name__}", {**details, "reason": "empty dataframe"}))
            else:
                checks.append(_ok(f"dataset {loader.__name__}", details))
        except Exception as exc:  # pragma: no cover - diagnostic path
            checks.append(_fail(f"dataset {loader.__name__}", repr(exc)))
    return checks


def check_cli() -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    try:
        from click.testing import CliRunner
        from nannyml.cli import cli
    except Exception as exc:  # pragma: no cover - diagnostic path
        return [_fail("import CLI", repr(exc))]

    runner = CliRunner()
    root = runner.invoke(cli, ["--help"])
    checks.append(_ok("nml --help") if root.exit_code == 0 and "run" in root.output else _fail("nml --help", root.output))

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "nannyml.yaml"
        cfg.write_text(
            "calculators:\n"
            "  - type: missing_values\n"
            "    params:\n"
            "      column_names: [feature]\n",
            encoding="utf-8",
        )
        run_help = runner.invoke(cli, ["-c", str(cfg), "run", "--help"])
        if run_help.exit_code == 0 and "--ignore-errors" in run_help.output:
            checks.append(_ok("nml -c <config> run --help"))
        else:
            details = {"exit_code": run_help.exit_code, "output_tail": run_help.output[-1000:]}
            if run_help.exception:
                details["exception"] = repr(run_help.exception)
            checks.append(_fail("nml -c <config> run --help", details))
    return checks


def check_database_optional(require_db: bool = False) -> List[Dict[str, Any]]:
    try:
        import nannyml as nml
        _ = nml.DatabaseWriter
        return [_ok("optional DatabaseWriter import")]
    except Exception as exc:
        result = _fail if require_db else _warn
        return [result("optional DatabaseWriter import", f"Install nannyml[db] to enable database output: {exc}")]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe NannyML package smoke checks.")
    parser.add_argument(
        "--check",
        choices=["all", "imports", "signatures", "datasets", "cli", "db"],
        default="all",
        help="Which check group to run. 'all' runs non-optional checks plus optional DB warning.",
    )
    parser.add_argument("--require-db", action="store_true", help="Treat missing DatabaseWriter dependencies as failure.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    args = parser.parse_args()

    checks: List[Dict[str, Any]] = []
    if args.check in {"all", "imports"}:
        checks.extend(check_imports())
    if args.check in {"all", "signatures"}:
        checks.extend(check_signatures())
    if args.check in {"all", "datasets"}:
        checks.extend(check_datasets())
    if args.check in {"all", "cli"}:
        checks.extend(check_cli())
    if args.check in {"all", "db"}:
        checks.extend(check_database_optional(require_db=args.require_db or args.check == "db"))

    failed = [c for c in checks if c["status"] == "FAIL"]
    if args.json:
        print(json.dumps({"schema": "nannyml.skill-check.v1", "checks": checks}, indent=2, sort_keys=True))
    else:
        for check in checks:
            details = "" if check.get("details") is None else f" - {check['details']}"
            print(f"[{check['status']}] {check['name']}{details}")
        print(f"Summary: {len(checks) - len(failed)}/{len(checks)} non-failing checks")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
