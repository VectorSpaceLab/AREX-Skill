#!/usr/bin/env python3
"""Dry-run-first helper for classic Igel tabular workflows.

This script adapts Igel's tiny example pattern (`Igel(**params)`) into a
parameterized helper that can validate configs, print the resolved payloads, and
optionally execute fit/evaluate/predict/export steps. It does not depend on the
original source checkout.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

MODEL_CATALOG: Dict[str, List[str]] = {
    "regression": [
        "LinearRegression",
        "SGDRegressor",
        "Lasso",
        "LassoLars",
        "BayesianRegression",
        "HuberRegression",
        "Ridge",
        "PoissonRegression",
        "ARDRegression",
        "TweedieRegression",
        "TheilSenRegression",
        "GammaRegression",
        "RANSACRegression",
        "DecisionTree",
        "ExtraTree",
        "RandomForest",
        "ExtraTrees",
        "SVM",
        "LinearSVM",
        "NuSVM",
        "NearestNeighbor",
        "NeuralNetwork",
        "ElasticNet",
        "BernoulliRBM",
        "BoltzmannMachine",
        "Adaboost",
        "Bagging",
        "GradientBoosting",
    ],
    "classification": [
        "LogisticRegression",
        "SGDClassifier",
        "Ridge",
        "DecisionTree",
        "ExtraTree",
        "RandomForest",
        "ExtraTrees",
        "SVM",
        "LinearSVM",
        "NuSVM",
        "NearestNeighbor",
        "NeuralNetwork",
        "PassiveAgressiveClassifier",
        "Perceptron",
        "BernoulliRBM",
        "BoltzmannMachine",
        "CalibratedClassifier",
        "Adaboost",
        "Bagging",
        "GradientBoosting",
        "BernoulliNaiveBayes",
        "CategoricalNaiveBayes",
        "ComplementNaiveBayes",
        "GaussianNaiveBayes",
        "MultinomialNaiveBayes",
    ],
    "clustering": [
        "KMeans",
        "KMedoids",
        "KMedians",
        "AffinityPropagation",
        "Birch",
        "AgglomerativeClustering",
        "FeatureAgglomeration",
        "DBSCAN",
        "MiniBatchKMeans",
        "SpectralBiclustering",
        "SpectralCoclustering",
        "SpectralClustering",
        "MeanShift",
        "OPTICS",
    ],
}

VALID_MISSING = {"drop", "mean", "median", "most_frequent", "constant"}
VALID_ENCODING = {"onehotencoding", "labelencoding"}
VALID_SCALERS = {"standard", "minmax"}
VALID_SCALE_TARGETS = {"inputs", "outputs", "all"}
VALID_SEARCH_METHODS = {"grid_search", "random_search"}


def _path(value: Optional[str]) -> Optional[Path]:
    if value is None:
        return None
    return Path(value).expanduser().resolve()


def _jsonable_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {k: str(v) if isinstance(v, Path) else v for k, v in payload.items()}


def load_config(path: Path) -> Dict[str, Any]:
    suffix = path.suffix.lower()
    with path.open("r", encoding="utf-8") as handle:
        if suffix in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore
            except Exception as exc:  # pragma: no cover - env-dependent
                raise RuntimeError(f"PyYAML is required to read {suffix} configs: {exc}") from exc
            data = yaml.safe_load(handle)
        elif suffix == ".json":
            data = json.load(handle)
        else:
            raise ValueError("Config extension must be .yaml or .json for Igel runs")
    return data or {}


def _read_csv_columns(data_path: Path, read_options: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    if data_path.suffix.lower() not in {".csv", ".txt"}:
        warnings.append(
            f"Column check skipped for {data_path.suffix or 'unknown extension'}; "
            "only CSV/TXT headers are checked by this helper."
        )
        return [], warnings
    try:
        import pandas as pd  # type: ignore
    except Exception as exc:  # pragma: no cover - env-dependent
        warnings.append(f"Column check skipped because pandas import failed: {exc}")
        return [], warnings
    options = dict(read_options)
    options.pop("nrows", None)
    options["nrows"] = 0
    frame = pd.read_csv(data_path, **options)
    return [str(col) for col in frame.columns], warnings


def validate_config(config_path: Path, data_path: Optional[Path] = None) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    summary: Dict[str, Any] = {"config_path": str(config_path)}

    if not config_path.exists():
        return {
            "ok": False,
            "errors": [f"Config file does not exist: {config_path}"],
            "warnings": warnings,
            "summary": summary,
        }

    if config_path.suffix.lower() == ".yml":
        warnings.append(
            "This helper can parse .yml, but Igel 0.7.0 routes non-.yaml configs to JSON; rename to .yaml before running fit."
        )

    try:
        config = load_config(config_path)
    except Exception as exc:
        return {
            "ok": False,
            "errors": [f"Failed to parse config: {exc}"],
            "warnings": warnings,
            "summary": summary,
        }

    if not isinstance(config, dict):
        errors.append("Config root must be a mapping/object.")
        config = {}

    dataset = config.get("dataset") or {}
    model = config.get("model") or {}
    target = config.get("target")
    summary["model"] = model
    summary["target"] = target

    if not isinstance(dataset, dict):
        errors.append("dataset must be a mapping when provided.")
        dataset = {}
    if not isinstance(model, dict):
        errors.append("model must be a mapping with type and algorithm.")
        model = {}

    model_type = model.get("type")
    algorithm = model.get("algorithm")
    if model_type not in MODEL_CATALOG:
        errors.append("model.type must be one of: classification, regression, clustering.")
    elif algorithm not in MODEL_CATALOG[model_type]:
        errors.append(
            f"Unsupported algorithm {algorithm!r} for model.type {model_type!r}. "
            "Use an exact name from the Igel model catalog."
        )

    args = model.get("arguments")
    if args is not None and not isinstance(args, dict) and str(args).lower() != "default":
        errors.append("model.arguments must be a mapping, omitted, or the string 'default'.")

    read_options = dataset.get("read_data_options", {})
    if read_options is None:
        read_options = {}
    if not isinstance(read_options, dict):
        errors.append("dataset.read_data_options must be a mapping; omit it instead of using a scalar default.")
        read_options = {}

    split = dataset.get("split")
    if split is not None and not isinstance(split, dict):
        errors.append("dataset.split must be a mapping when provided.")

    preprocess = dataset.get("preprocess") or {}
    if preprocess and not isinstance(preprocess, dict):
        errors.append("dataset.preprocess must be a mapping when provided.")
        preprocess = {}

    missing = preprocess.get("missing_values") if isinstance(preprocess, dict) else None
    if missing and str(missing).lower() not in VALID_MISSING:
        errors.append(f"Unsupported missing_values strategy {missing!r}.")

    encoding = preprocess.get("encoding") if isinstance(preprocess, dict) else None
    if encoding is not None:
        if not isinstance(encoding, dict):
            errors.append("preprocess.encoding must be a mapping.")
        else:
            enc_type = str(encoding.get("type", "")).lower()
            if enc_type and enc_type not in VALID_ENCODING:
                errors.append(f"Unsupported encoding type {encoding.get('type')!r}.")
            if enc_type == "labelencoding" and not encoding.get("column"):
                errors.append("labelEncoding requires preprocess.encoding.column.")

    scale = preprocess.get("scale") if isinstance(preprocess, dict) else None
    if scale is not None:
        if not isinstance(scale, dict):
            errors.append("preprocess.scale must be a mapping.")
        else:
            method = scale.get("method")
            target_scope = scale.get("target")
            if method and str(method).lower() not in VALID_SCALERS:
                errors.append(f"Unsupported scale.method {method!r}.")
            if target_scope and str(target_scope).lower() not in VALID_SCALE_TARGETS:
                errors.append(f"Unsupported scale.target {target_scope!r}.")

    cross_validate = model.get("cross_validate")
    if cross_validate is not None and not isinstance(cross_validate, dict):
        errors.append("model.cross_validate must be a mapping when provided.")

    hp = model.get("hyperparameter_search")
    if hp is not None:
        if not isinstance(hp, dict):
            errors.append("model.hyperparameter_search must be a mapping.")
        else:
            method = hp.get("method")
            if method not in VALID_SEARCH_METHODS:
                errors.append("hyperparameter_search.method must be grid_search or random_search.")
            if not isinstance(hp.get("parameter_grid"), dict):
                errors.append("hyperparameter_search.parameter_grid must be a mapping.")
            if hp.get("arguments") is not None and not isinstance(hp.get("arguments"), dict):
                errors.append("hyperparameter_search.arguments must be a mapping when provided.")

    if model_type != "clustering":
        if not isinstance(target, list):
            errors.append("Non-clustering configs must set target as a YAML/JSON list, e.g. target: [label].")
        elif len(target) == 0:
            errors.append("Non-clustering configs must include at least one target column.")
    elif target:
        warnings.append("Clustering ignores target columns; omit target or leave it empty.")

    if data_path is not None:
        summary["data_path"] = str(data_path)
        if not data_path.exists():
            errors.append(f"Data file does not exist: {data_path}")
        else:
            try:
                columns, col_warnings = _read_csv_columns(data_path, read_options)
                warnings.extend(col_warnings)
                if columns:
                    summary["columns"] = columns
                    if isinstance(target, list) and model_type != "clustering":
                        missing_targets = [str(t) for t in target if str(t) not in columns]
                        if missing_targets:
                            errors.append(f"Target columns missing from data: {missing_targets}")
            except Exception as exc:
                warnings.append(f"Column check failed; Igel may still read the file: {exc}")

    return {"ok": not errors, "errors": errors, "warnings": warnings, "summary": summary}


def _payload(command: str, **values: Any) -> Dict[str, Any]:
    payload = {"cmd": command}
    payload.update({k: str(v) for k, v in values.items() if v is not None})
    return payload


def build_payloads(args: argparse.Namespace) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    validations: List[Dict[str, Any]] = []
    command = args.command

    if command == "check-config":
        config_path = _path(args.yaml_path)
        data_path = _path(args.data_path)
        assert config_path is not None
        validations.append(validate_config(config_path, data_path))
        return [], validations

    if command == "fit":
        data_path = _path(args.data_path)
        config_path = _path(args.yaml_path)
        assert data_path is not None and config_path is not None
        validations.append(validate_config(config_path, data_path))
        return [_payload("fit", data_path=data_path, yaml_path=config_path)], validations

    if command == "evaluate":
        data_path = _path(args.data_path)
        assert data_path is not None
        model_path = _path(args.model_path)
        description_file = _path(args.description_file)
        if model_path is not None and not model_path.exists():
            validations.append(
                {"ok": False, "errors": [f"Model file does not exist: {model_path}"], "warnings": [], "summary": {"model_path": str(model_path)}}
            )
        if description_file is not None and not description_file.exists():
            validations.append(
                {"ok": False, "errors": [f"Description file does not exist: {description_file}"], "warnings": [], "summary": {"description_file": str(description_file)}}
            )
        return [
            _payload(
                "evaluate",
                data_path=data_path,
                model_path=model_path,
                description_file=description_file,
            )
        ], validations

    if command == "predict":
        data_path = _path(args.data_path)
        assert data_path is not None
        model_path = _path(args.model_path)
        description_file = _path(args.description_file)
        prediction_file = _path(args.prediction_file)
        if model_path is not None and not model_path.exists():
            validations.append(
                {"ok": False, "errors": [f"Model file does not exist: {model_path}"], "warnings": [], "summary": {"model_path": str(model_path)}}
            )
        if description_file is not None and not description_file.exists():
            validations.append(
                {"ok": False, "errors": [f"Description file does not exist: {description_file}"], "warnings": [], "summary": {"description_file": str(description_file)}}
            )
        return [
            _payload(
                "predict",
                data_path=data_path,
                model_path=model_path,
                description_file=description_file,
                prediction_file=prediction_file,
            )
        ], validations

    if command == "export":
        model_path = _path(args.model_path)
        assert model_path is not None
        if not model_path.exists():
            validations.append(
                {
                    "ok": False,
                    "errors": [f"Model file does not exist: {model_path}"],
                    "warnings": [],
                    "summary": {"model_path": str(model_path)},
                }
            )
        return [_payload("export", model_path=model_path)], validations

    if command == "experiment":
        train_path = _path(args.train_data_path)
        eval_path = _path(args.eval_data_path)
        pred_path = _path(args.predict_data_path)
        config_path = _path(args.yaml_path)
        assert train_path and eval_path and pred_path and config_path
        validations.append(validate_config(config_path, train_path))
        return [
            _payload("fit", data_path=train_path, yaml_path=config_path),
            _payload("evaluate", data_path=eval_path),
            _payload("predict", data_path=pred_path),
        ], validations

    if command == "demo-fit-export":
        demo_dir, data_path, config_path = create_demo_files(_path(args.workdir))
        args.workdir = str(demo_dir)
        validations.append(validate_config(config_path, data_path))
        return [
            _payload("fit", data_path=data_path, yaml_path=config_path),
            _payload("export", model_path=demo_dir / "model_results" / "model.joblib"),
        ], validations

    raise ValueError(f"Unhandled command: {command}")


def create_demo_files(base_dir: Optional[Path]) -> Tuple[Path, Path, Path]:
    if base_dir is not None:
        base_dir.mkdir(parents=True, exist_ok=True)
        demo_dir = Path(tempfile.mkdtemp(prefix="igel-tabular-demo-", dir=str(base_dir)))
    else:
        demo_dir = Path(tempfile.mkdtemp(prefix="igel-tabular-demo-"))

    try:
        import pandas as pd  # type: ignore
        from sklearn.datasets import load_iris  # type: ignore
    except Exception as exc:  # pragma: no cover - env-dependent
        raise RuntimeError(f"The demo requires pandas and scikit-learn: {exc}") from exc

    iris = load_iris(as_frame=True)
    frame = iris.frame.rename(columns={"target": "Species"})
    data_path = demo_dir / "iris_demo.csv"
    config_path = demo_dir / "igel_demo.json"
    frame.to_csv(data_path, index=False)
    config = {
        "dataset": {
            "split": {"test_size": 0.2, "shuffle": True},
            "preprocess": {"missing_values": "mean"},
        },
        "model": {"type": "classification", "algorithm": "DecisionTree"},
        "target": ["Species"],
    }
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return demo_dir, data_path, config_path


def import_igel_class() -> Any:
    try:
        from igel import Igel  # type: ignore
    except Exception as exc:  # pragma: no cover - env-dependent
        message = (
            "Failed to import igel. For Igel 0.7.0, use a legacy-compatible "
            "NumPy/SciPy/scikit-learn/skl2onnx stack. Common incompatible-stack "
            "signals include np.float removal, scipy.linalg.pinv2 removal, and "
            "modern pip rejecting old dependency metadata."
        )
        raise RuntimeError(f"{message}\nOriginal import error: {exc}") from exc
    return Igel


def execute_payloads(payloads: Iterable[Dict[str, Any]], workdir: Path) -> None:
    workdir.mkdir(parents=True, exist_ok=True)
    old_cwd = Path.cwd()
    os.chdir(workdir)
    try:
        Igel = import_igel_class()
        for payload in payloads:
            Igel(**payload)
    finally:
        os.chdir(old_cwd)


def print_report(report: Dict[str, Any]) -> None:
    print("Igel tabular helper")
    print(f"Command: {report['command']}")
    print(f"Workdir: {report['workdir']}")
    print(f"Mode: {'execute' if report['run'] else 'dry-run'}")

    validations = report.get("validations", [])
    if validations:
        print("\nValidation:")
        for idx, validation in enumerate(validations, 1):
            status = "ok" if validation.get("ok") else "fail"
            print(f"  [{idx}] {status}")
            for warning in validation.get("warnings", []):
                print(f"      warning: {warning}")
            for error in validation.get("errors", []):
                print(f"      error: {error}")

    payloads = report.get("payloads", [])
    if payloads:
        print("\nPayloads:")
        for payload in payloads:
            print("  " + json.dumps(payload, sort_keys=True))

    if report.get("execution_error"):
        print("\nExecution error:")
        print(report["execution_error"])
    elif report["run"] and payloads:
        print("\nExecuted payloads successfully.")
    elif payloads:
        print("\nDry-run only. Pass --run to execute these payloads.")


def add_common_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--run",
        action="store_true",
        help="Actually import igel and execute the resolved payloads. Without this flag, only validate and print payloads.",
    )
    parser.add_argument(
        "--workdir",
        help="Working directory where Igel should create/read model_results; defaults to the current directory.",
    )


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and optionally run classic Igel tabular fit/evaluate/predict/export payloads."
    )
    parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check-config", help="Validate an Igel YAML/JSON config without importing igel.")
    check.add_argument("--yaml-path", required=True, help="Path to .yaml or .json config.")
    check.add_argument("--data-path", help="Optional CSV/TXT data file whose header should contain target columns.")

    fit = sub.add_parser("fit", help="Validate and optionally run Igel fit.")
    fit.add_argument("--data-path", required=True)
    fit.add_argument("--yaml-path", required=True)
    add_common_run_args(fit)

    evaluate = sub.add_parser("evaluate", help="Optionally run Igel evaluate.")
    evaluate.add_argument("--data-path", required=True)
    evaluate.add_argument("--model-path")
    evaluate.add_argument("--description-file")
    add_common_run_args(evaluate)

    predict = sub.add_parser("predict", help="Optionally run Igel predict.")
    predict.add_argument("--data-path", required=True)
    predict.add_argument("--model-path")
    predict.add_argument("--description-file")
    predict.add_argument("--prediction-file")
    add_common_run_args(predict)

    export = sub.add_parser("export", help="Optionally run Igel export.")
    export.add_argument("--model-path", required=True)
    add_common_run_args(export)

    experiment = sub.add_parser("experiment", help="Validate and optionally run fit, evaluate, then predict.")
    experiment.add_argument("--train-data-path", required=True)
    experiment.add_argument("--eval-data-path", required=True)
    experiment.add_argument("--predict-data-path", required=True)
    experiment.add_argument("--yaml-path", required=True)
    add_common_run_args(experiment)

    demo = sub.add_parser("demo-fit-export", help="Create a tiny iris fixture and optionally run fit then export.")
    add_common_run_args(demo)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    run = bool(getattr(args, "run", False))
    workdir_arg = getattr(args, "workdir", None)
    workdir = _path(workdir_arg) or Path.cwd()

    try:
        payloads, validations = build_payloads(args)
        if getattr(args, "workdir", None):
            workdir = _path(args.workdir) or workdir
    except Exception as exc:
        report = {
            "command": args.command,
            "workdir": str(workdir),
            "run": run,
            "payloads": [],
            "validations": [],
            "execution_error": str(exc),
        }
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_report(report)
        return 2

    validation_failed = any(not validation.get("ok") for validation in validations)
    execution_error: Optional[str] = None
    if run and payloads and not validation_failed:
        try:
            execute_payloads(payloads, workdir)
        except Exception as exc:  # pragma: no cover - depends on caller env and data
            execution_error = str(exc)

    report = {
        "command": args.command,
        "workdir": str(workdir),
        "run": run,
        "payloads": [_jsonable_payload(p) for p in payloads],
        "validations": validations,
        "execution_error": execution_error,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_report(report)

    if validation_failed:
        return 2
    if execution_error:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
