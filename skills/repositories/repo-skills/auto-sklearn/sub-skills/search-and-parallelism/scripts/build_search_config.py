#!/usr/bin/env python3
"""Generate safe auto-sklearn search configuration snippets.

This helper intentionally does not import or run auto-sklearn. It only validates
simple CLI input and emits JSON or Python snippets for future runs.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


VALID_STEPS = {
    "classifier",
    "regressor",
    "feature_preprocessor",
    "data_preprocessor",
    "balancing",
}

CLASSIFIER_IDS = {
    "adaboost",
    "bernoulli_nb",
    "decision_tree",
    "extra_trees",
    "gaussian_nb",
    "gradient_boosting",
    "k_nearest_neighbors",
    "lda",
    "liblinear_svc",
    "libsvm_svc",
    "mlp",
    "multinomial_nb",
    "passive_aggressive",
    "qda",
    "random_forest",
    "sgd",
}

REGRESSOR_IDS = {
    "adaboost",
    "ard_regression",
    "decision_tree",
    "extra_trees",
    "gaussian_process",
    "gradient_boosting",
    "k_nearest_neighbors",
    "liblinear_svr",
    "libsvm_svr",
    "mlp",
    "random_forest",
    "sgd",
}

FEATURE_PREPROCESSOR_IDS = {
    "densifier",
    "extra_trees_preproc_for_classification",
    "extra_trees_preproc_for_regression",
    "fast_ica",
    "feature_agglomeration",
    "kernel_pca",
    "kitchen_sinks",
    "liblinear_svc_preprocessor",
    "no_preprocessing",
    "nystroem_sampler",
    "pca",
    "polynomial",
    "random_trees_embedding",
    "select_percentile_classification",
    "select_percentile_regression",
    "select_rates_classification",
    "select_rates_regression",
    "truncatedSVD",
}

KNOWN_IDS_BY_STEP = {
    "classifier": CLASSIFIER_IDS,
    "regressor": REGRESSOR_IDS,
    "feature_preprocessor": FEATURE_PREPROCESSOR_IDS,
    "balancing": {"balancing"},
}


class ComponentSpecAction(argparse.Action):
    """Parse repeated STEP=id1,id2 component specifications."""

    def __call__(self, parser, namespace, values, option_string=None):  # type: ignore[override]
        current = getattr(namespace, self.dest, None) or {}
        for value in values:
            if "=" not in value:
                parser.error(f"{option_string} expects STEP=id1,id2, got {value!r}")
            step, raw_ids = value.split("=", 1)
            step = step.strip()
            if step not in VALID_STEPS:
                parser.error(
                    f"Unknown step {step!r}; expected one of {sorted(VALID_STEPS)}"
                )
            ids = [item.strip() for item in raw_ids.split(",") if item.strip()]
            if not ids:
                parser.error(f"{option_string} for {step!r} must list at least one id")
            current[step] = ids
        setattr(namespace, self.dest, current)


def parse_key_value(text: str) -> tuple[str, Any]:
    if "=" not in text:
        raise argparse.ArgumentTypeError("expected KEY=VALUE")
    key, value = text.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        raise argparse.ArgumentTypeError("empty key is not allowed")
    # Keep values JSON-friendly while still allowing simple strings.
    try:
        parsed: Any = json.loads(value)
    except json.JSONDecodeError:
        parsed = value
    return key, parsed


def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return value


def positive_or_none_int(text: str) -> int | None:
    if text.lower() == "none":
        return None
    return positive_int(text)


def nonnegative_int(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Emit safe JSON/Python snippets for auto-sklearn search configuration "
            "without importing or running auto-sklearn."
        )
    )
    parser.add_argument(
        "--mode",
        choices=["sequential", "parallel", "random", "successive-halving"],
        default="sequential",
        help="Search workflow strategy to sketch (default: sequential).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "python"],
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "--task",
        choices=["classification", "regression"],
        default="classification",
        help="Estimator family for the Python snippet (default: classification).",
    )
    parser.add_argument(
        "--time-left",
        type=positive_int,
        default=3600,
        help="time_left_for_this_task in seconds (default: 3600).",
    )
    parser.add_argument(
        "--per-run-time-limit",
        type=positive_or_none_int,
        default=None,
        help="per_run_time_limit in seconds or 'none' (default: omitted).",
    )
    parser.add_argument(
        "--memory-limit",
        type=positive_or_none_int,
        default=3072,
        help="memory_limit in MB or 'none' (default: 3072).",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=None,
        help="Constructor n_jobs. Use -1 for all CPUs. Defaults from --mode.",
    )
    parser.add_argument(
        "--dask-client-name",
        default=None,
        help="Name of an existing Python variable holding a Dask Client for snippet output.",
    )
    parser.add_argument(
        "--include",
        nargs="+",
        action=ComponentSpecAction,
        default=None,
        metavar="STEP=id1,id2",
        help="Restrict search space. Repeatable groups such as classifier=random_forest,extra_trees.",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        action=ComponentSpecAction,
        default=None,
        metavar="STEP=id1,id2",
        help="Exclude components from search. Incompatible with --include.",
    )
    parser.add_argument(
        "--allow-unknown-components",
        action="store_true",
        help="Allow custom component IDs without validating against bundled known IDs.",
    )
    parser.add_argument(
        "--ensemble-class",
        choices=["default", "none", "EnsembleSelection", "SingleBest"],
        default="default",
        help="Ensemble class sketch (default: default).",
    )
    parser.add_argument(
        "--ensemble-size",
        type=nonnegative_int,
        default=None,
        help="Set ensemble_kwargs={'ensemble_size': N}. Use 0 to disable selection size.",
    )
    parser.add_argument(
        "--ensemble-nbest",
        default=50,
        help="ensemble_nbest value as int or float string (default: 50).",
    )
    parser.add_argument(
        "--max-models-on-disc",
        default="50",
        help="max_models_on_disc value: int, float MB budget, or none (default: 50).",
    )
    parser.add_argument(
        "--disable-evaluator-output",
        choices=["false", "true", "model", "cv_model", "y_optimization", "y_test"],
        nargs="*",
        default=["false"],
        help=(
            "Output suppression. Use no value or 'false' to keep outputs; 'true' disables all; "
            "otherwise list artifact names."
        ),
    )
    parser.add_argument(
        "--load-models",
        choices=["true", "false"],
        default="true",
        help="Whether fit should load models after completion (default: true).",
    )
    parser.add_argument(
        "--tmp-folder",
        default=None,
        help="Optional tmp_folder value for emitted snippets.",
    )
    parser.add_argument(
        "--delete-tmp-folder-after-terminate",
        choices=["true", "false"],
        default="true",
        help="tmp folder cleanup flag (default: true).",
    )
    parser.add_argument(
        "--scenario-arg",
        action="append",
        type=parse_key_value,
        default=[],
        metavar="KEY=VALUE",
        help="Add smac_scenario_args entry. VALUE may be JSON or a string.",
    )
    parser.add_argument(
        "--budget-type",
        choices=["iterations", "subsample", "mixed"],
        default="iterations",
        help="Budget type comment for successive-halving snippets (default: iterations).",
    )
    return parser


def validate_components(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.allow_unknown_components:
        return
    for option_name in ("include", "exclude"):
        spec = getattr(args, option_name) or {}
        for step, ids in spec.items():
            known = KNOWN_IDS_BY_STEP.get(step)
            if known is None:
                continue
            unknown = sorted(set(ids) - known)
            if unknown:
                parser.error(
                    f"--{option_name} has unknown component id(s) for {step}: {unknown}. "
                    "Pass --allow-unknown-components for registered custom components."
                )


def parse_auto_number(value: str) -> Any:
    if str(value).lower() == "none":
        return None
    try:
        if "." in str(value):
            return float(value)
        return int(value)
    except ValueError:
        return value


def disable_value(values: list[str]) -> bool | list[str]:
    if not values or values == ["false"]:
        return False
    if "true" in values:
        if len(values) > 1:
            raise SystemExit("--disable-evaluator-output true cannot be combined with artifact names")
        return True
    return values


def choose_n_jobs(args: argparse.Namespace) -> int:
    if args.n_jobs is not None:
        return args.n_jobs
    if args.mode == "parallel":
        return 2
    return 1


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    if args.include and args.exclude:
        raise SystemExit("--include and --exclude are mutually exclusive")

    n_jobs = choose_n_jobs(args)
    config: dict[str, Any] = {
        "mode": args.mode,
        "estimator": "AutoSklearnClassifier" if args.task == "classification" else "AutoSklearnRegressor",
        "constructor_kwargs": {
            "time_left_for_this_task": args.time_left,
            "memory_limit": args.memory_limit,
            "n_jobs": n_jobs,
            "ensemble_nbest": parse_auto_number(args.ensemble_nbest),
            "max_models_on_disc": parse_auto_number(args.max_models_on_disc),
            "disable_evaluator_output": disable_value(args.disable_evaluator_output),
            "load_models": args.load_models == "true",
            "delete_tmp_folder_after_terminate": args.delete_tmp_folder_after_terminate == "true",
        },
        "notes": [],
    }

    kwargs = config["constructor_kwargs"]
    if args.per_run_time_limit is not None:
        kwargs["per_run_time_limit"] = args.per_run_time_limit
    if args.tmp_folder:
        kwargs["tmp_folder"] = args.tmp_folder
    if args.dask_client_name:
        kwargs["dask_client"] = f"<python variable: {args.dask_client_name}>"
        config["notes"].append("When dask_client is supplied, auto-sklearn treats it as user-owned and will not close it.")
    if args.include:
        kwargs["include"] = args.include
    if args.exclude:
        kwargs["exclude"] = args.exclude

    if args.ensemble_class == "none":
        kwargs["ensemble_class"] = None
        config["notes"].append("No ensemble is built during fit; call fit_ensemble later if prediction should use an ensemble.")
    elif args.ensemble_class != "default":
        kwargs["ensemble_class"] = args.ensemble_class

    if args.ensemble_size is not None:
        kwargs["ensemble_kwargs"] = {"ensemble_size": args.ensemble_size}

    scenario_args = dict(args.scenario_arg)
    if scenario_args:
        kwargs["smac_scenario_args"] = scenario_args
        config["notes"].append("Protected SMAC scenario keys are ignored by auto-sklearn; prefer estimator-level budgets.")

    if args.mode == "parallel":
        config["notes"].extend(
            [
                "Guard scripts with if __name__ == '__main__'.",
                "Memory budget is per job; plan for n_jobs * memory_limit plus overhead.",
                "Set OPENBLAS_NUM_THREADS=1, MKL_NUM_THREADS=1, and OMP_NUM_THREADS=1 before Python starts.",
            ]
        )
    elif args.mode == "random":
        kwargs["get_smac_object_callback"] = "get_random_search_object_callback"
        kwargs.setdefault("initial_configurations_via_metalearning", 0)
        config["notes"].append("Define get_random_search_object_callback before running; it should return a SMAC ROAR facade.")
    elif args.mode == "successive-halving":
        kwargs["get_smac_object_callback"] = f"successive_halving_callback({args.budget_type!r})"
        config["notes"].append("Define successive_halving_callback before running; it must set ta_kwargs['budget_type'] and return SMAC4AC with SuccessiveHalving.")
    else:
        config["notes"].append("Sequential mode is easiest to debug; use ensemble_class=None for search-then-fit_ensemble workflows.")

    if config["constructor_kwargs"]["disable_evaluator_output"] is not False:
        config["notes"].append("Disabling evaluator output can make predict(), ensembles, or model inspection unavailable.")

    return config


def python_literal(value: Any) -> str:
    if isinstance(value, str) and value.startswith("<python variable:"):
        return value.removeprefix("<python variable: ").removesuffix(">")
    return repr(value)


def emit_python(config: dict[str, Any]) -> str:
    kwargs = config["constructor_kwargs"]
    estimator = config["estimator"]
    module = "classification" if estimator == "AutoSklearnClassifier" else "regression"
    class_name = estimator
    lines = [
        "# Safe snippet generated by build_search_config.py; review before running.",
        "import autosklearn.%s" % module,
    ]
    if kwargs.get("ensemble_class") == "EnsembleSelection":
        lines.append("from autosklearn.ensembles.ensemble_selection import EnsembleSelection")
    elif kwargs.get("ensemble_class") == "SingleBest":
        lines.append("from autosklearn.ensembles.singlebest_ensemble import SingleBest")
    lines.append("")
    if config["mode"] in {"parallel", "random", "successive-halving"}:
        lines.extend([
            "if __name__ == \"__main__\":",
            f"    automl = autosklearn.{module}.{class_name}(",
        ])
        indent = "        "
        close = "    )"
    else:
        lines.append(f"automl = autosklearn.{module}.{class_name}(")
        indent = "    "
        close = ")"

    for key, value in kwargs.items():
        if key == "get_smac_object_callback" and isinstance(value, str):
            rendered = value
        elif key == "ensemble_class" and value in {"EnsembleSelection", "SingleBest"}:
            rendered = value
        else:
            rendered = python_literal(value)
        lines.append(f"{indent}{key}={rendered},")
    lines.append(close)
    lines.append("")
    if config["notes"]:
        lines.append("# Notes:")
        for note in config["notes"]:
            lines.append("# - " + note)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    validate_components(args, parser)

    config = build_config(args)
    if args.format == "json":
        print(json.dumps(config, indent=2, sort_keys=True))
    else:
        print(emit_python(config), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
