#!/usr/bin/env python3
"""Build safe RL Baselines3 Zoo plotting and benchmark commands.

The helper is deterministic and non-executing: it prints a shell command plus
warnings/errors, but it never imports rl_zoo3, never starts training/evaluation,
never opens a display, never contacts the network, and never writes plot or
benchmark output files. Optional input checks inspect local paths only.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import pickle
import shlex
import sys
from pathlib import Path
from typing import Any


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def command_shell(env: dict[str, str], argv: list[str]) -> str:
    env_prefix = [f"{key}={shlex.quote(value)}" for key, value in sorted(env.items())]
    return " ".join([*env_prefix, *(shlex.quote(part) for part in argv)])


def plot_entry(entry: str, module_name: str) -> list[str]:
    if entry == "module":
        return ["python", "-m", f"rl_zoo3.plots.{module_name}"]
    return ["rl_zoo3", module_name]


def add_option(argv: list[str], flag: str, value: Any | None) -> None:
    if value is not None:
        argv.extend([flag, str(value)])


def add_multi(argv: list[str], flag: str, values: list[str] | None) -> None:
    if values:
        argv.append(flag)
        argv.extend(str(value) for value in values)


def add_bool(argv: list[str], flag: str, enabled: bool) -> None:
    if enabled:
        argv.append(flag)


def normalize_all_plots_output(output: str | None, warnings: list[str]) -> str | None:
    if output is None:
        return None
    if output.endswith(".pkl"):
        fixed = output[:-4]
        warnings.append(
            "all_plots appends '.pkl' itself; using output stem "
            f"{fixed!r} to avoid a '.pkl.pkl' file."
        )
        return fixed
    return output


def monitor_header(path: Path) -> list[str]:
    with path.open(newline="") as handle:
        for row in csv.reader(handle):
            if not row:
                continue
            if row[0].startswith("#"):
                continue
            return [cell.strip() for cell in row]
    return []


def check_plot_train(args: argparse.Namespace, warnings: list[str], errors: list[str]) -> None:
    exp_folder = Path(args.exp_folder)
    if not exp_folder.exists():
        errors.append(f"exp folder does not exist: {exp_folder}")
        return
    algo_dir = exp_folder / args.algo
    if not algo_dir.is_dir():
        warnings.append(f"algorithm folder not found: {algo_dir}")
        return

    wanted_column = {"reward": "r", "length": "l", "success": "is_success"}[args.y_axis]
    for env in args.envs:
        matches = [path for path in algo_dir.iterdir() if path.is_dir() and env in path.name]
        if not matches:
            warnings.append(f"no run directories under {algo_dir} contain env substring {env!r}")
            continue
        monitor_files: list[Path] = []
        for folder in matches:
            monitor_files.extend(Path(match) for match in glob.glob(str(folder / "**" / "*monitor.csv"), recursive=True))
        if not monitor_files:
            warnings.append(f"no '*monitor.csv' files found for env substring {env!r}")
            continue
        first_header = monitor_header(monitor_files[0])
        if wanted_column not in first_header:
            warnings.append(
                f"first monitor file for {env!r} lacks column {wanted_column!r}; "
                f"available columns: {first_header or 'unknown'}"
            )


def check_all_plots(args: argparse.Namespace, warnings: list[str], errors: list[str]) -> None:
    if args.labels and len(args.labels) != len(args.exp_folders):
        errors.append("all_plots requires exactly one --labels value per --exp-folders value")

    try:
        np = None
        if args.inspect_arrays:
            import numpy as np  # type: ignore[no-redef]
    except Exception as exc:  # pragma: no cover - depends on runtime extras
        np = None
        warnings.append(f"could not import numpy for --inspect-arrays: {exc}")

    for exp_folder_value in args.exp_folders:
        exp_folder = Path(exp_folder_value)
        if not exp_folder.exists():
            errors.append(f"experiment folder does not exist: {exp_folder}")
            continue
        for algo in args.algos:
            algo_dir = exp_folder / algo.lower()
            if not algo_dir.is_dir():
                warnings.append(f"algorithm folder not found: {algo_dir}")
                continue
            for env in args.envs:
                matches = [path for path in algo_dir.iterdir() if path.is_dir() and env in path.name]
                if not matches:
                    warnings.append(f"no run directories under {algo_dir} contain env substring {env!r}")
                    continue
                for folder in matches:
                    npz_path = folder / "evaluations.npz"
                    if not npz_path.is_file():
                        warnings.append(f"missing evaluations.npz: {npz_path}")
                        continue
                    if np is not None:
                        try:
                            with np.load(npz_path, allow_pickle=False) as data:
                                keys = set(data.files)
                                if "timesteps" not in keys:
                                    errors.append(f"{npz_path} lacks required 'timesteps' array")
                                    continue
                                if args.key not in keys:
                                    errors.append(f"{npz_path} lacks selected key {args.key!r}; keys={sorted(keys)}")
                                    continue
                                timesteps = data["timesteps"]
                                values = data[args.key]
                                if timesteps.shape[0] == 0:
                                    warnings.append(f"{npz_path} has zero evaluation timesteps")
                                if values.shape[0] != timesteps.shape[0]:
                                    errors.append(
                                        f"{npz_path} key {args.key!r} first dimension {values.shape[0]} "
                                        f"does not match timesteps length {timesteps.shape[0]}"
                                    )
                        except Exception as exc:
                            errors.append(f"failed to inspect {npz_path}: {exc}")


def resolve_plot_file(input_value: str) -> Path:
    path = Path(input_value)
    if path.suffix != ".pkl":
        path = Path(f"{input_value}.pkl")
    return path


def check_plot_from_file(args: argparse.Namespace, warnings: list[str], errors: list[str]) -> None:
    input_path = resolve_plot_file(args.input)
    if not input_path.is_file():
        errors.append(f"input pickle does not exist: {input_path}")
        return
    if args.inspect_pickle:
        warnings.append("--inspect-pickle loads a trusted local pickle; do not use it on untrusted files.")
        try:
            with input_path.open("rb") as handle:
                payload = pickle.load(handle)
        except Exception as exc:
            errors.append(f"failed to load pickle {input_path}: {exc}")
            return
        if not isinstance(payload, dict):
            errors.append("pickle top-level object is not a dictionary")
            return
        table = payload.get("results_table")
        if not isinstance(table, dict):
            errors.append("pickle lacks results_table dictionary")
        elif not isinstance(table.get("headers"), list) or not isinstance(table.get("value_matrix"), list):
            errors.append("results_table must contain list-valued headers and value_matrix")
        env_keys = [key for key in payload.keys() if key != "results_table"]
        if not env_keys:
            warnings.append("pickle contains no environment result keys")
        retained_keys: set[str] = set()
        for env in env_keys:
            methods = payload.get(env)
            if not isinstance(methods, dict):
                errors.append(f"environment key {env!r} does not map to a dictionary")
                continue
            for method, result in methods.items():
                retained_keys.add(str(method))
                if not isinstance(result, dict):
                    errors.append(f"{env}/{method} result is not a dictionary")
                    continue
                for required in ["timesteps", "mean", "std_error", "last_evals", "std_error_last_eval"]:
                    if required not in result:
                        errors.append(f"{env}/{method} lacks {required!r}")
                if args.iqm and "mean_per_eval" not in result:
                    warnings.append(f"{env}/{method} lacks 'mean_per_eval'; --iqm may fail")
        if args.labels and len(args.labels) != len(retained_keys):
            warnings.append(
                f"provided {len(args.labels)} labels for {len(retained_keys)} retained method keys before filtering; "
                "confirm --keep-keys/--skip-keys behavior"
            )
    elif args.iqm:
        warnings.append("--iqm requires result pickles with 'mean_per_eval'; use --inspect-pickle on trusted files to preflight.")


def check_benchmark(args: argparse.Namespace, warnings: list[str], errors: list[str]) -> None:
    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        errors.append(f"log dir does not exist: {log_dir}")
    else:
        args_files = list(log_dir.glob("*/*/*/args.yml"))
        if not args_files:
            warnings.append(
                "no discoverable trained-agent args.yml files found under "
                f"{log_dir}; benchmark may produce an empty table or require Hub candidates"
            )
    benchmark_dir = Path(args.benchmark_dir)
    if not benchmark_dir.exists() and not benchmark_dir.parent.exists():
        errors.append(f"parent of benchmark dir does not exist: {benchmark_dir.parent}")


def build_plot_train(args: argparse.Namespace, warnings: list[str]) -> tuple[dict[str, str], list[str]]:
    env: dict[str, str] = {}
    if not args.display:
        env["MPLBACKEND"] = "Agg"
        warnings.append("plot_train has no --no-display or save flag; MPLBACKEND=Agg avoids GUI display but does not save a figure.")
    argv = plot_entry(args.entry, "plot_train")
    argv.extend(["--algo", args.algo, "--env", *args.envs, "--exp-folder", args.exp_folder])
    add_option(argv, "--x-axis", args.x_axis)
    add_option(argv, "--y-axis", args.y_axis)
    add_option(argv, "--episode-window", args.episode_window)
    add_option(argv, "--max-timesteps", args.max_timesteps)
    add_multi(argv, "--figsize", [str(v) for v in args.figsize] if args.figsize else None)
    add_option(argv, "--fontsize", args.fontsize)
    return env, argv


def build_all_plots(args: argparse.Namespace, warnings: list[str]) -> tuple[dict[str, str], list[str]]:
    env: dict[str, str] = {}
    argv = plot_entry(args.entry, "all_plots")
    add_multi(argv, "--algos", args.algos)
    add_multi(argv, "--env", args.envs)
    add_multi(argv, "--exp-folders", args.exp_folders)
    add_multi(argv, "--labels", args.labels)
    add_option(argv, "--key", args.key)
    add_option(argv, "--max-timesteps", args.max_timesteps)
    add_option(argv, "--min-timesteps", args.min_timesteps)
    add_option(argv, "--output", normalize_all_plots_output(args.output, warnings))
    add_bool(argv, "--median", args.median)
    add_bool(argv, "--no-million", args.no_million)
    if not args.display:
        argv.append("--no-display")
    else:
        warnings.append("all_plots will call plt.show(); omit --display for headless-safe export.")
    add_bool(argv, "--print-n-trials", args.print_n_trials)
    return env, argv


def build_plot_from_file(args: argparse.Namespace, warnings: list[str]) -> tuple[dict[str, str], list[str]]:
    env: dict[str, str] = {}
    if not args.display:
        env["MPLBACKEND"] = "Agg"
    else:
        warnings.append("plot_from_file calls plt.show(); omit --display for headless-safe rendering.")
    if args.rliable:
        warnings.append("--rliable can be slow and requires optional rliable dependencies plus valid score normalization.")
    argv = plot_entry(args.entry, "plot_from_file")
    add_option(argv, "--input", args.input)
    add_multi(argv, "--skip-envs", args.skip_envs)
    add_multi(argv, "--keep-envs", args.keep_envs)
    add_multi(argv, "--skip-keys", args.skip_keys)
    add_multi(argv, "--keep-keys", args.keep_keys)
    add_bool(argv, "--no-million", args.no_million)
    add_bool(argv, "--skip-timesteps", args.skip_timesteps)
    add_option(argv, "--output", args.output)
    add_option(argv, "--format", args.format)
    add_option(argv, "--legend-loc", args.legend_loc)
    add_multi(argv, "--figsize", [str(v) for v in args.figsize] if args.figsize else None)
    add_option(argv, "--fontsize", args.fontsize)
    add_multi(argv, "--labels", args.labels)
    add_bool(argv, "--boxplot", args.boxplot)
    add_bool(argv, "--rliable", args.rliable)
    add_bool(argv, "--versus", args.versus)
    add_bool(argv, "--iqm", args.iqm)
    add_option(argv, "--ci-size", args.ci_size)
    add_bool(argv, "--latex", args.latex)
    add_multi(argv, "--merge", args.merge)
    return env, argv


def build_benchmark(args: argparse.Namespace, warnings: list[str]) -> tuple[dict[str, str], list[str]]:
    env: dict[str, str] = {}
    argv = ["python", "-m", "rl_zoo3.benchmark"]
    add_option(argv, "--log-dir", args.log_dir)
    add_option(argv, "--benchmark-dir", args.benchmark_dir)
    add_option(argv, "--n-timesteps", args.n_timesteps)
    add_option(argv, "--n-envs", args.n_envs)
    add_option(argv, "--verbose", args.verbose)
    add_option(argv, "--seed", args.seed)
    add_bool(argv, "--with-mujoco", args.with_mujoco)
    if not args.full:
        argv.append("--test-mode")
    else:
        warnings.append("full benchmark can evaluate many agents and copy benchmark.md in the current directory.")
    if not args.allow_hub:
        argv.append("--no-hub")
    else:
        warnings.append("Hub access allowed: benchmark may contact Hugging Face and download/list remote models.")
    add_option(argv, "--num-threads", args.num_threads)
    warnings.append("benchmark module may require a local enjoy.py shim; use python -m rl_zoo3.enjoy loops in package-only workspaces.")
    return env, argv


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON with argv, environment, warnings, and errors.")
    parser.add_argument("--check-inputs", action="store_true", help="Check local input paths required by the selected command.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when checks produce warnings as well as errors.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    def add_plot_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--entry", choices=["console", "module"], default="console", help="Use rl_zoo3 console or python -m module form.")
        subparser.add_argument("--display", action="store_true", help="Do not add headless safeguards; command may open a GUI window.")

    plot_train = subparsers.add_parser("plot-train", help="Build a plot_train command for Monitor CSV logs.")
    add_plot_common(plot_train)
    plot_train.add_argument("--algo", required=True, help="Algorithm id, e.g. ppo.")
    plot_train.add_argument("--env", "--envs", dest="envs", nargs="+", required=True, help="Environment substring(s) to include.")
    plot_train.add_argument("--exp-folder", required=True, help="Root experiment/log folder.")
    plot_train.add_argument("--x-axis", choices=["steps", "episodes", "time"], default="steps")
    plot_train.add_argument("--y-axis", choices=["success", "reward", "length"], default="reward")
    plot_train.add_argument("--episode-window", type=positive_int, default=100)
    plot_train.add_argument("--max-timesteps", type=positive_int)
    plot_train.add_argument("--figsize", nargs=2, type=positive_int)
    plot_train.add_argument("--fontsize", type=positive_int)

    all_plots = subparsers.add_parser("all-plots", help="Build an all_plots command for evaluations.npz files.")
    add_plot_common(all_plots)
    all_plots.add_argument("--algos", nargs="+", required=True, help="Algorithm ids to include.")
    all_plots.add_argument("--env", "--envs", dest="envs", nargs="+", required=True, help="Environment substring keys to include.")
    all_plots.add_argument("--exp-folders", nargs="+", required=True, help="Experiment/log root folders.")
    all_plots.add_argument("--labels", nargs="+", help="One label per experiment folder.")
    all_plots.add_argument("--key", default="results", help="Array key from evaluations.npz to aggregate.")
    all_plots.add_argument("--max-timesteps", type=positive_int)
    all_plots.add_argument("--min-timesteps", type=int)
    all_plots.add_argument("--output", help="Output pickle stem; all_plots appends .pkl.")
    all_plots.add_argument("--median", action="store_true")
    all_plots.add_argument("--no-million", action="store_true")
    all_plots.add_argument("--print-n-trials", action="store_true")
    all_plots.add_argument("--inspect-arrays", action="store_true", help="With --check-inputs, inspect npz array keys/shapes using numpy.")

    plot_from_file = subparsers.add_parser("plot-from-file", help="Build a plot_from_file command for postprocessed .pkl files.")
    add_plot_common(plot_from_file)
    plot_from_file.add_argument("--input", required=True, help="Input pickle path or stem.")
    plot_from_file.add_argument("--skip-envs", nargs="+", default=[])
    plot_from_file.add_argument("--keep-envs", nargs="+", default=[])
    plot_from_file.add_argument("--skip-keys", nargs="+", default=[])
    plot_from_file.add_argument("--keep-keys", nargs="+", default=[])
    plot_from_file.add_argument("--no-million", action="store_true")
    plot_from_file.add_argument("--skip-timesteps", action="store_true")
    plot_from_file.add_argument("--output", help="Output image filename.")
    plot_from_file.add_argument("--format", help="Output image format, e.g. svg or png.")
    plot_from_file.add_argument("--legend-loc")
    plot_from_file.add_argument("--figsize", nargs=2, type=positive_int)
    plot_from_file.add_argument("--fontsize", type=positive_int)
    plot_from_file.add_argument("--labels", nargs="+")
    plot_from_file.add_argument("--boxplot", action="store_true")
    plot_from_file.add_argument("--rliable", action="store_true")
    plot_from_file.add_argument("--versus", action="store_true")
    plot_from_file.add_argument("--iqm", action="store_true")
    plot_from_file.add_argument("--ci-size", type=float)
    plot_from_file.add_argument("--latex", action="store_true")
    plot_from_file.add_argument("--merge", nargs="+", default=[])
    plot_from_file.add_argument("--inspect-pickle", action="store_true", help="With --check-inputs, load a trusted local pickle and validate its schema.")

    benchmark = subparsers.add_parser("benchmark", help="Build a safe rl_zoo3.benchmark command.")
    benchmark.add_argument("--log-dir", default="rl-trained-agents", help="Root trained-agent log folder.")
    benchmark.add_argument("--benchmark-dir", default="logs/benchmark", help="Benchmark output folder.")
    benchmark.add_argument("--n-timesteps", type=positive_int, default=100)
    benchmark.add_argument("--n-envs", type=positive_int, default=1)
    benchmark.add_argument("--verbose", type=non_negative_int, default=1)
    benchmark.add_argument("--seed", type=non_negative_int, default=0)
    benchmark.add_argument("--with-mujoco", action="store_true")
    benchmark.add_argument("--num-threads", type=positive_int, default=1)
    benchmark.add_argument("--full", action="store_true", help="Omit --test-mode; may run many evaluations and update benchmark.md.")
    benchmark.add_argument("--allow-hub", action="store_true", help="Omit --no-hub and allow live Hub catalog/download behavior.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    warnings: list[str] = []
    errors: list[str] = []

    if args.mode == "plot-train":
        env, command = build_plot_train(args, warnings)
        if args.check_inputs:
            check_plot_train(args, warnings, errors)
    elif args.mode == "all-plots":
        env, command = build_all_plots(args, warnings)
        if args.check_inputs:
            check_all_plots(args, warnings, errors)
    elif args.mode == "plot-from-file":
        env, command = build_plot_from_file(args, warnings)
        if args.check_inputs:
            check_plot_from_file(args, warnings, errors)
    elif args.mode == "benchmark":
        env, command = build_benchmark(args, warnings)
        if args.check_inputs:
            check_benchmark(args, warnings, errors)
    else:  # pragma: no cover - argparse enforces choices
        parser.error(f"unknown mode: {args.mode}")

    shell = command_shell(env, command)
    payload = {
        "mode": args.mode,
        "command": shell,
        "env": env,
        "argv": command,
        "warnings": warnings,
        "errors": errors,
        "executes": False,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(shell)
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
        for error in errors:
            print(f"error: {error}", file=sys.stderr)

    if errors or (args.strict and warnings):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
