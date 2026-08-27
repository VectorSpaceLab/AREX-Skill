#!/usr/bin/env python3
"""Plan Chemprop uncertainty, hpopt, and conversion arguments without importing Chemprop.

This helper prints shell-safe command fragments and catches common compatibility
mistakes. It is intentionally self-contained so it can run before Chemprop or
optional hpopt dependencies are installed.
"""

from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


REGRESSION_ESTIMATORS = {
    "none",
    "mve",
    "ensemble",
    "evidential-total",
    "evidential-epistemic",
    "evidential-aleatoric",
    "dropout",
    "quantile-regression",
}
CLASSIFICATION_ESTIMATORS = {"none", "ensemble", "classification", "dropout", "classification-dirichlet"}
MULTICLASS_ESTIMATORS = {"none", "ensemble", "dropout", "multiclass-dirichlet"}

ESTIMATOR_TASKS = {
    "none": {"any"},
    "mve": {"regression-mve"},
    "ensemble": {"any"},
    "classification": {"classification"},
    "evidential-total": {"regression-evidential"},
    "evidential-epistemic": {"regression-evidential"},
    "evidential-aleatoric": {"regression-evidential"},
    "dropout": {"any"},
    "classification-dirichlet": {"classification-dirichlet"},
    "multiclass-dirichlet": {"multiclass-dirichlet"},
    "quantile-regression": {"regression-quantile"},
}

CALIBRATOR_FAMILIES = {
    "zscaling": "regression",
    "zelikman-interval": "regression",
    "mve-weighting": "regression-mve-ensemble",
    "conformal-regression": "regression",
    "platt": "classification",
    "isotonic": "classification",
    "conformal-multilabel": "classification",
    "conformal-multiclass": "multiclass",
    "conformal-adaptive": "multiclass",
    "isotonic-multiclass": "multiclass",
}

EVALUATOR_FAMILIES = {
    "nll-regression": "regression",
    "miscalibration_area": "regression",
    "ence": "regression",
    "spearman": "regression",
    "conformal-coverage-regression": "regression",
    "nll-classification": "classification",
    "conformal-coverage-classification": "classification",
    "nll-multiclass": "multiclass",
    "conformal-coverage-multiclass": "multiclass",
}

HPARAM_KEYWORDS = {
    "basic",
    "learning_rate",
    "all",
    "activation",
    "dropout",
    "message_hidden_dim",
    "depth",
    "aggregation",
    "aggregation_norm",
    "ffn_hidden_dim",
    "ffn_num_layers",
    "atom_ffn_hidden_dim",
    "atom_ffn_num_layers",
    "atom_constrainer_ffn_hidden_dim",
    "atom_constrainer_ffn_num_layers",
    "bond_ffn_hidden_dim",
    "bond_ffn_num_layers",
    "bond_constrainer_ffn_hidden_dim",
    "bond_constrainer_ffn_num_layers",
    "batch_size",
    "init_lr_ratio",
    "max_lr",
    "final_lr_ratio",
    "warmup_epochs",
}

TASK_FAMILY = {
    "regression": "regression",
    "regression-mve": "regression",
    "regression-evidential": "regression",
    "regression-quantile": "regression",
    "classification": "classification",
    "classification-dirichlet": "classification",
    "multiclass": "multiclass",
    "multiclass-dirichlet": "multiclass",
}


@dataclass
class Plan:
    command: list[str]
    warnings: list[str]
    notes: list[str]

    def shell(self) -> str:
        return " ".join(shlex.quote(part) for part in self.command)


def add_common_output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")


def task_family(task_type: str) -> str:
    return TASK_FAMILY.get(task_type, "other")


def compatible_estimator(task_type: str, estimator: str) -> bool:
    allowed = ESTIMATOR_TASKS[estimator]
    return "any" in allowed or task_type in allowed


def warn_if_path_suffix(path: str | None, suffixes: Iterable[str], label: str, warnings: list[str]) -> None:
    if path is None:
        return
    if Path(path).suffix and Path(path).suffix not in suffixes:
        warnings.append(f"{label} usually expects suffix {sorted(suffixes)}; got {Path(path).suffix!r}.")


def build_uncertainty(args: argparse.Namespace) -> Plan:
    warnings: list[str] = []
    notes: list[str] = []

    warn_if_path_suffix(args.test_path, {".csv"}, "--test-path", warnings)
    warn_if_path_suffix(args.output, {".csv", ".pkl"}, "--output", warnings)

    if not compatible_estimator(args.task_type, args.uncertainty_method):
        warnings.append(
            f"Estimator {args.uncertainty_method!r} is usually incompatible with task "
            f"{args.task_type!r}; expected {sorted(ESTIMATOR_TASKS[args.uncertainty_method])}."
        )

    if args.uncertainty_method == "ensemble" and len(args.model_paths) < 2:
        warnings.append("The ensemble estimator requires at least two compatible model paths.")

    if args.calibration_method and not args.cal_path:
        warnings.append("Calibration method was provided without --cal-path.")

    family = task_family(args.task_type)
    if args.calibration_method:
        calibrator_family = CALIBRATOR_FAMILIES[args.calibration_method]
        if calibrator_family == "regression-mve-ensemble":
            if args.uncertainty_method != "mve" or len(args.model_paths) < 2:
                warnings.append("mve-weighting expects MVE uncertainty from multiple model artifacts.")
        elif calibrator_family != family:
            warnings.append(
                f"Calibrator {args.calibration_method!r} is for {calibrator_family}, "
                f"but task {args.task_type!r} is {family}."
            )

    if args.evaluation_methods and not args.test_has_targets:
        warnings.append("Evaluation methods require target labels in --test-path; pass --test-has-targets only when labels are present.")

    for evaluator in args.evaluation_methods or []:
        evaluator_family = EVALUATOR_FAMILIES[evaluator]
        if evaluator_family != family:
            warnings.append(
                f"Evaluator {evaluator!r} is for {evaluator_family}, but task {args.task_type!r} is {family}."
            )

    if not 0 < args.conformal_alpha < 1:
        warnings.append("--conformal-alpha should be in the open interval (0, 1) for practical conformal prediction.")
    if not 1 < args.calibration_interval_percentile < 100:
        warnings.append("--calibration-interval-percentile should be in the open interval (1, 100).")
    if args.uncertainty_method == "dropout" and args.dropout_sampling_size < 2:
        warnings.append("Dropout uncertainty should use at least two samples; larger values are more stable.")

    if args.converted_v1:
        notes.append("Converted v1 models should be predicted with --multi-hot-atom-featurizer-mode v1.")

    command = [
        "chemprop",
        "predict",
        "--test-path",
        args.test_path,
        "--model-paths",
        *args.model_paths,
        "--output",
        args.output,
        "--uncertainty-method",
        args.uncertainty_method,
    ]
    if args.cal_path:
        command.extend(["--cal-path", args.cal_path])
    if args.calibration_method:
        command.extend(["--calibration-method", args.calibration_method])
    if args.evaluation_methods:
        command.extend(["--evaluation-methods", *args.evaluation_methods])
    if args.uncertainty_method == "dropout":
        command.extend([
            "--uncertainty-dropout-p",
            str(args.uncertainty_dropout_p),
            "--dropout-sampling-size",
            str(args.dropout_sampling_size),
        ])
    if args.calibration_method in {"conformal-regression", "conformal-multilabel", "conformal-multiclass", "conformal-adaptive"}:
        command.extend(["--conformal-alpha", str(args.conformal_alpha)])
    if args.calibration_method == "zelikman-interval":
        command.extend(["--calibration-interval-percentile", str(args.calibration_interval_percentile)])
    if args.converted_v1:
        command.extend(["--multi-hot-atom-featurizer-mode", "v1"])

    if args.cal_path:
        notes.append("Mirror descriptor, atom/bond feature, constraint, SMILES, reaction, and featurizer flags for calibration data.")
    if args.evaluation_methods:
        notes.append("Evaluation logs scores and requires labels in the test CSV.")

    return Plan(command=command, warnings=warnings, notes=notes)


def build_hpopt(args: argparse.Namespace) -> Plan:
    warnings: list[str] = []
    notes: list[str] = []

    unknown = [keyword for keyword in args.search_parameter_keywords if keyword not in HPARAM_KEYWORDS]
    if unknown:
        warnings.append(f"Unknown search parameter keyword(s): {unknown}.")
    searches_warmup = any(
        keyword in {"warmup_epochs", "learning_rate", "all"}
        for keyword in args.search_parameter_keywords
    )
    if searches_warmup and args.epochs < 6:
        warnings.append("Searching warmup_epochs requires --epochs at least 6.")
    if args.raytune_search_algorithm == "hyperopt":
        notes.append("The default hyperopt search algorithm requires HyperOpt search support from optional hpopt dependencies.")
    if args.raytune_search_algorithm == "optuna":
        notes.append("Optuna search requires optional Optuna search support.")
    if args.from_foundation:
        notes.append("Foundation initialization prunes message-passing architecture parameters from the effective hpopt search space.")
    if args.num_replicates and args.num_replicates > 1:
        notes.append("Hpopt uses only the first split when --num-replicates is greater than one.")

    command = [
        "chemprop",
        "hpopt",
        "--data-path",
        args.data_path,
        "--task-type",
        args.task_type,
        "--search-parameter-keywords",
        *args.search_parameter_keywords,
        "--raytune-num-samples",
        str(args.raytune_num_samples),
        "--raytune-search-algorithm",
        args.raytune_search_algorithm,
        "--raytune-trial-scheduler",
        args.raytune_trial_scheduler,
        "--hpopt-save-dir",
        args.hpopt_save_dir,
        "--epochs",
        str(args.epochs),
    ]
    if args.tracking_metric:
        command.extend(["--tracking-metric", args.tracking_metric])
    if args.from_foundation:
        command.extend(["--from-foundation", args.from_foundation])
    if args.raytune_max_concurrent_trials:
        command.extend(["--raytune-max-concurrent-trials", str(args.raytune_max_concurrent_trials)])
    if args.raytune_num_cpus:
        command.extend(["--raytune-num-cpus", str(args.raytune_num_cpus)])
    if args.raytune_num_gpus:
        command.extend(["--raytune-num-gpus", str(args.raytune_num_gpus)])

    notes.append("After hpopt, use best_config.toml with chemprop train --config-path for the final model.")
    return Plan(command=command, warnings=warnings, notes=notes)


def build_convert(args: argparse.Namespace) -> Plan:
    warnings: list[str] = []
    notes: list[str] = []

    warn_if_path_suffix(args.input_path, {".pt"}, "--input-path", warnings)
    if args.output_path:
        warn_if_path_suffix(args.output_path, {".pt"}, "--output-path", warnings)

    command = ["chemprop", "convert", "--conversion", args.conversion, "--input-path", args.input_path]
    if args.output_path:
        command.extend(["--output-path", args.output_path])
    if args.conversion == "v1_to_v2":
        notes.append("Predict with converted v1 models using --multi-hot-atom-featurizer-mode v1.")
    return Plan(command=command, warnings=warnings, notes=notes)


def emit(plan: Plan, as_json: bool) -> None:
    if as_json:
        payload = asdict(plan)
        payload["shell"] = plan.shell()
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print(plan.shell())
    if plan.warnings:
        print("\nWarnings:")
        for warning in plan.warnings:
            print(f"- {warning}")
    if plan.notes:
        print("\nNotes:")
        for note in plan.notes:
            print(f"- {note}")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    uncertainty = subparsers.add_parser("predict", help="Plan a chemprop predict uncertainty command.")
    uncertainty.add_argument("--test-path", required=True)
    uncertainty.add_argument("--model-paths", nargs="+", required=True)
    uncertainty.add_argument("--output", required=True)
    uncertainty.add_argument("--task-type", required=True, choices=sorted(TASK_FAMILY))
    uncertainty.add_argument("--uncertainty-method", default="none", choices=sorted(ESTIMATOR_TASKS))
    uncertainty.add_argument("--cal-path")
    uncertainty.add_argument("--calibration-method", choices=sorted(CALIBRATOR_FAMILIES))
    uncertainty.add_argument("--evaluation-methods", nargs="+", choices=sorted(EVALUATOR_FAMILIES))
    uncertainty.add_argument("--test-has-targets", action="store_true")
    uncertainty.add_argument("--uncertainty-dropout-p", type=float, default=0.1)
    uncertainty.add_argument("--dropout-sampling-size", type=int, default=10)
    uncertainty.add_argument("--calibration-interval-percentile", type=float, default=95.0)
    uncertainty.add_argument("--conformal-alpha", type=float, default=0.1)
    uncertainty.add_argument("--converted-v1", action="store_true")
    add_common_output(uncertainty)

    hpopt = subparsers.add_parser("hpopt", help="Plan a chemprop hpopt command.")
    hpopt.add_argument("--data-path", required=True)
    hpopt.add_argument("--task-type", required=True)
    hpopt.add_argument("--search-parameter-keywords", nargs="+", default=["basic"])
    hpopt.add_argument("--raytune-num-samples", type=int, default=10)
    hpopt.add_argument("--raytune-search-algorithm", choices=["random", "hyperopt", "optuna"], default="hyperopt")
    hpopt.add_argument("--raytune-trial-scheduler", choices=["FIFO", "AsyncHyperBand"], default="FIFO")
    hpopt.add_argument("--raytune-max-concurrent-trials", type=int)
    hpopt.add_argument("--raytune-num-cpus", type=int)
    hpopt.add_argument("--raytune-num-gpus", type=int)
    hpopt.add_argument("--hpopt-save-dir", required=True)
    hpopt.add_argument("--epochs", type=int, default=20)
    hpopt.add_argument("--tracking-metric")
    hpopt.add_argument("--from-foundation")
    hpopt.add_argument("--num-replicates", type=int)
    add_common_output(hpopt)

    convert = subparsers.add_parser("convert", help="Plan a chemprop convert command.")
    convert.add_argument("--conversion", choices=["v1_to_v2", "v2_0_to_v2_1"], default="v1_to_v2")
    convert.add_argument("--input-path", required=True)
    convert.add_argument("--output-path")
    add_common_output(convert)

    return parser


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()
    if args.mode == "predict":
        plan = build_uncertainty(args)
    elif args.mode == "hpopt":
        plan = build_hpopt(args)
    elif args.mode == "convert":
        plan = build_convert(args)
    else:
        raise SystemExit(f"Unsupported mode: {args.mode}")
    emit(plan, args.json)


if __name__ == "__main__":
    main()
