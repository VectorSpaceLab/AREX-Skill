#!/usr/bin/env python3
"""Build a bounded RL Zoo Optuna HPO command without executing it.

The builder emits an installed-package command string for either a new Optuna
optimization run or a stored-trial replay. It validates high-risk HPO
combinations, but it never imports RL Zoo training code, starts environments,
runs optimization, contacts the network, or reads credentials.
"""

from __future__ import annotations

import argparse
import importlib.util
import shlex
import sys
from collections.abc import Sequence

SUPPORTED_HPO_ALGOS = (
    "a2c",
    "ars",
    "ddpg",
    "dqn",
    "ppo",
    "ppo_lstm",
    "qrdqn",
    "sac",
    "td3",
    "tqc",
    "trpo",
)

DEFAULT_SAMPLER = "tpe"
DEFAULT_PRUNER = "median"
DEFAULT_N_JOBS = 1
DEFAULT_N_TRIALS = 500
DEFAULT_N_STARTUP_TRIALS = 0
DEFAULT_N_EVALUATIONS = 1

MANAGED_FLAG_TOKENS = {"-optimize", "--optimize-hyperparameters", "--no-optim-plots"}


def positive_int(text: str) -> int:
    """Parse a strictly positive integer for budget/job counts."""
    try:
        value = int(text)
    except ValueError as exc:  # pragma: no cover - argparse formats this path
        raise argparse.ArgumentTypeError(f"{text!r} is not an integer") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return value


def nonnegative_int(text: str) -> int:
    """Parse a non-negative integer for trial ids and startup counts."""
    try:
        value = int(text)
    except ValueError as exc:  # pragma: no cover - argparse formats this path
        raise argparse.ArgumentTypeError(f"{text!r} is not an integer") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("value must be zero or greater")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print an RL Zoo Optuna HPO command without running it.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Unknown options are forwarded to the generated rl_zoo3.train command, "
            "so base training flags from the training-cli sub-skill can be appended.\n\n"
            "Examples:\n"
            "  %(prog)s --algo ppo --env CartPole-v1 -n 1000 --n-trials 2\n"
            "  %(prog)s --algo a2c --env Pendulum-v1 --storage sqlite:///runs/optuna.db "
            "--study-name demo --max-total-trials 3 -n 100\n"
            "  %(prog)s --algo ppo --env CartPole-v1 --storage sqlite:///runs/optuna.db "
            "--study-name demo --trial-id 1 -n 1000\n"
        ),
    )
    parser.add_argument(
        "--launcher",
        choices=("module", "console"),
        default="module",
        help="Command launcher: module prints 'python -m rl_zoo3.train'; console prints 'rl_zoo3 train'.",
    )
    parser.add_argument(
        "--algo",
        required=True,
        choices=SUPPORTED_HPO_ALGOS,
        help="RL Zoo algorithm id with a defined Optuna HPO search space.",
    )
    parser.add_argument("--env", required=True, help="Gymnasium environment id for the generated command.")
    parser.add_argument(
        "--n-trials",
        type=positive_int,
        default=None,
        help=f"Per-runner trial count. If omitted and no --max-total-trials is set, {DEFAULT_N_TRIALS} is emitted.",
    )
    parser.add_argument(
        "--max-total-trials",
        type=positive_int,
        default=None,
        help="Global Optuna trial cap across complete, running, and pruned trials.",
    )
    parser.add_argument("--n-jobs", type=positive_int, default=DEFAULT_N_JOBS, help="Optuna parallel jobs.")
    parser.add_argument(
        "--sampler",
        choices=("random", "tpe", "auto"),
        default=DEFAULT_SAMPLER,
        help="Optuna sampler.",
    )
    parser.add_argument(
        "--pruner",
        choices=("halving", "median", "none"),
        default=DEFAULT_PRUNER,
        help="Optuna pruner.",
    )
    parser.add_argument(
        "--n-startup-trials",
        type=nonnegative_int,
        default=DEFAULT_N_STARTUP_TRIALS,
        help="Warmup trials before sampler/pruner decisions.",
    )
    parser.add_argument(
        "--n-evaluations",
        type=positive_int,
        default=DEFAULT_N_EVALUATIONS,
        help="Intermediate evaluations per trial.",
    )
    parser.add_argument("--storage", help="Optuna storage URI or journal .log path.")
    parser.add_argument("--study-name", help="Reusable Optuna study name.")
    parser.add_argument(
        "--trial-id",
        type=nonnegative_int,
        help="Stored trial number/index to replay as an ordinary training command.",
    )
    parser.add_argument(
        "--optimization-log-path",
        help="Directory for per-trial evaluation logs during a new optimization run.",
    )
    parser.add_argument(
        "--show-optim-plots",
        action="store_true",
        help="Do not add RL Zoo's --no-optim-plots flag. Default output suppresses optional plot display.",
    )
    return parser


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def has_timestep_budget(tokens: Sequence[str]) -> bool:
    """Detect whether passthrough training args include -n/--n-timesteps."""
    for token in tokens:
        if token in {"-n", "--n-timesteps"}:
            return True
        if token.startswith("--n-timesteps="):
            return True
        if token.startswith("-n") and not token.startswith("--") and len(token) > 2:
            return True
    return False


def clean_passthrough(tokens: Sequence[str], warnings: list[str]) -> list[str]:
    cleaned: list[str] = []
    for token in tokens:
        if token in MANAGED_FLAG_TOKENS:
            warnings.append(f"ignored passthrough token {token!r}; this builder manages that HPO flag")
            continue
        cleaned.append(token)
    return cleaned


def validate(args: argparse.Namespace, passthrough: Sequence[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    replay_mode = args.trial_id is not None

    if replay_mode:
        if not args.storage or not args.study_name:
            errors.append("--trial-id requires both --storage and --study-name")
        optimization_options = []
        if args.n_trials is not None:
            optimization_options.append("--n-trials")
        if args.max_total_trials is not None:
            optimization_options.append("--max-total-trials")
        if args.n_jobs != DEFAULT_N_JOBS:
            optimization_options.append("--n-jobs")
        if args.sampler != DEFAULT_SAMPLER:
            optimization_options.append("--sampler")
        if args.pruner != DEFAULT_PRUNER:
            optimization_options.append("--pruner")
        if args.n_startup_trials != DEFAULT_N_STARTUP_TRIALS:
            optimization_options.append("--n-startup-trials")
        if args.n_evaluations != DEFAULT_N_EVALUATIONS:
            optimization_options.append("--n-evaluations")
        if args.optimization_log_path:
            optimization_options.append("--optimization-log-path")
        if args.show_optim_plots:
            optimization_options.append("--show-optim-plots")
        if optimization_options:
            warnings.append(
                "trial replay omits optimization-only options: " + ", ".join(optimization_options)
            )
    else:
        if args.pruner == "halving" and args.n_jobs <= 1:
            errors.append("--pruner halving requires --n-jobs greater than 1")
        if args.sampler == "auto" and not module_available("optunahub"):
            errors.append("--sampler auto requires the optional optunahub package")
        if args.storage and not args.study_name:
            warnings.append("--storage without --study-name makes distributed reuse and trial replay ambiguous")
        if args.max_total_trials is not None:
            if args.n_trials is not None:
                warnings.append("--max-total-trials takes precedence over --n-trials in RL Zoo HPO")
            if not (args.storage and args.study_name):
                warnings.append(
                    "--max-total-trials is local unless every worker uses the same --storage and --study-name"
                )
            else:
                warnings.append(
                    "--max-total-trials counts COMPLETE, RUNNING, and PRUNED trials across the shared study"
                )

    if not has_timestep_budget(passthrough):
        warnings.append("no explicit -n/--n-timesteps training budget found in forwarded training args")

    if args.launcher == "console" and not (module_available("seaborn") and module_available("rliable")):
        warnings.append(
            "console launcher may fail without RL Zoo plotting extras; module launcher avoids the console import path"
        )

    if args.show_optim_plots and not (module_available("seaborn") and module_available("rliable")):
        warnings.append("requested optimization plots, but plotting optional dependencies may be incomplete")

    return errors, warnings


def launcher_tokens(launcher: str) -> list[str]:
    if launcher == "module":
        return ["python", "-m", "rl_zoo3.train"]
    return ["rl_zoo3", "train"]


def add_optional(tokens: list[str], flag: str, value: object | None) -> None:
    if value is not None:
        tokens.extend([flag, str(value)])


def build_command(args: argparse.Namespace, passthrough: Sequence[str]) -> list[str]:
    cmd = launcher_tokens(args.launcher)
    cmd.extend(["--algo", args.algo, "--env", args.env])
    cmd.extend(passthrough)

    if args.trial_id is not None:
        add_optional(cmd, "--storage", args.storage)
        add_optional(cmd, "--study-name", args.study_name)
        add_optional(cmd, "--trial-id", args.trial_id)
        return cmd

    cmd.append("--optimize-hyperparameters")
    n_trials = args.n_trials
    if args.max_total_trials is None and n_trials is None:
        n_trials = DEFAULT_N_TRIALS
    add_optional(cmd, "--n-trials", n_trials)
    add_optional(cmd, "--max-total-trials", args.max_total_trials)
    add_optional(cmd, "--n-jobs", args.n_jobs)
    add_optional(cmd, "--sampler", args.sampler)
    add_optional(cmd, "--pruner", args.pruner)
    add_optional(cmd, "--n-startup-trials", args.n_startup_trials)
    add_optional(cmd, "--n-evaluations", args.n_evaluations)
    add_optional(cmd, "--storage", args.storage)
    add_optional(cmd, "--study-name", args.study_name)
    add_optional(cmd, "--optimization-log-path", args.optimization_log_path)
    if not args.show_optim_plots:
        cmd.append("--no-optim-plots")
    return cmd


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)
    warnings: list[str] = []
    passthrough = clean_passthrough(unknown, warnings)
    errors, validation_warnings = validate(args, passthrough)
    warnings.extend(validation_warnings)

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if errors:
        parser.exit(2, "error: " + "\nerror: ".join(errors) + "\n")

    print(shlex.join(build_command(args, passthrough)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
