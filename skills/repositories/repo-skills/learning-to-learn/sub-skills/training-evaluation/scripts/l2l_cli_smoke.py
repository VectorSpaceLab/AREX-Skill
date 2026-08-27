#!/usr/bin/env python3
"""Generate or run tiny Learning-to-Learn CLI smoke commands.

This helper prints safe CPU-only training/evaluation commands by default.
Use --run to execute them after validating the local repo checkout and the
legacy TensorFlow/Sonnet dependencies.

The helper intentionally keeps the default smoke commands tiny:
- train: simple problem, one epoch, two steps, one-step unroll
- evaluate: simple problem, one epoch, two steps

Data-backed problems (mnist, cifar, cifar-multi) are blocked from execution
unless --allow-data is set explicitly.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

SAFE_PROBLEMS = ("simple", "simple-multi", "quadratic", "mnist", "cifar", "cifar-multi")
DATA_PROBLEMS = {"mnist", "cifar", "cifar-multi"}


def _quote(parts):
    return " ".join(shlex.quote(str(part)) for part in parts)


def _build_train_command(repo_root, problem, num_epochs, num_steps, unroll_length,
                         save_path=None):
    command = [
        "python",
        "train.py",
        f"--problem={problem}",
        f"--num_epochs={num_epochs}",
        f"--num_steps={num_steps}",
        f"--unroll_length={unroll_length}",
        "--log_period=1",
    ]
    if save_path:
        command.append(f"--save_path={save_path}")
        command.extend(["--evaluation_period=1", "--evaluation_epochs=1"])
    else:
        command.append("--evaluation_period=999999")
    return f"cd {shlex.quote(str(repo_root))} && {_quote(command)}"


def _build_evaluate_command(repo_root, problem, optimizer, num_epochs, num_steps,
                            path=None):
    command = [
        "python",
        "evaluate.py",
        f"--problem={problem}",
        f"--optimizer={optimizer}",
        f"--num_epochs={num_epochs}",
        f"--num_steps={num_steps}",
    ]
    if path:
        command.append(f"--path={path}")
    return f"cd {shlex.quote(str(repo_root))} && {_quote(command)}"


def _validate_positive(name, value):
    if value < 1:
        raise SystemExit(f"{name} must be >= 1")


def _validate_repo_root(repo_root):
    if not repo_root.exists():
        raise SystemExit(f"repo root not found: {repo_root}")
    if not repo_root.is_dir():
        raise SystemExit(f"repo root is not a directory: {repo_root}")
    for filename in ("train.py", "evaluate.py"):
        if not (repo_root / filename).is_file():
            raise SystemExit(f"missing {filename} under {repo_root}")


def _expected_l2l_files(problem):
    if problem == "cifar-multi":
        return ("conv.l2l", "fc.l2l")
    return ("cw.l2l",)


def _validate_environment():
    try:
        import tensorflow as tf  # noqa: F401
        from tensorflow.contrib.learn.python.learn import monitored_session  # noqa: F401
        import sonnet  # noqa: F401
        import dill  # noqa: F401
        import mock  # noqa: F401
    except Exception as exc:
        raise SystemExit(
            "missing TensorFlow 1.x / Sonnet 1.x dependencies needed to run the "
            f"source CLIs: {exc}"
        )


def _warn(message):
    print(f"[l2l_cli_smoke] {message}", file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate or run tiny Learning-to-Learn CLI smoke commands."
    )
    parser.add_argument("--mode", choices=("train", "evaluate"), default="train")
    parser.add_argument("--repo-root", default=".", help="Path to the repo checkout.")
    parser.add_argument("--problem", choices=SAFE_PROBLEMS, default="simple")
    parser.add_argument("--optimizer", choices=("Adam", "L2L"), default="L2L")
    parser.add_argument("--save-path", default=None, help="Training save directory.")
    parser.add_argument("--path", default=None, help="Evaluation save directory for L2L.")
    parser.add_argument("--num-epochs", type=int, default=1)
    parser.add_argument("--num-steps", type=int, default=2)
    parser.add_argument("--unroll-length", type=int, default=1)
    parser.add_argument("--print-command", dest="print_command", action="store_true")
    parser.add_argument("--no-print-command", dest="print_command", action="store_false")
    parser.set_defaults(print_command=True)
    parser.add_argument("--run", action="store_true")
    parser.add_argument(
        "--allow-data",
        action="store_true",
        help="Allow mnist/cifar problems to run even though they may download data.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).expanduser()
    _validate_repo_root(repo_root)

    _validate_positive("num_epochs", args.num_epochs)
    _validate_positive("num_steps", args.num_steps)
    _validate_positive("unroll_length", args.unroll_length)

    if args.mode == "train" and args.num_steps < args.unroll_length:
        raise SystemExit("num_steps must be >= unroll_length for training")
    if args.mode == "train" and args.num_steps % args.unroll_length != 0:
        _warn("num_steps is not divisible by unroll_length; train.py will truncate the remainder")

    if args.mode == "train" and args.save_path and args.path:
        _warn("--path is ignored in train mode; only --save-path affects the generated train command")
    if args.mode == "evaluate" and args.save_path:
        _warn("--save-path is ignored in evaluate mode; use --path for L2L reloads")
    if args.mode == "evaluate" and args.unroll_length != 1:
        _warn("--unroll-length is ignored in evaluate mode; evaluate.py always uses a one-step unroll")

    if args.mode == "train":
        command = _build_train_command(
            repo_root=repo_root,
            problem=args.problem,
            num_epochs=args.num_epochs,
            num_steps=args.num_steps,
            unroll_length=args.unroll_length,
            save_path=args.save_path,
        )
    else:
        command = _build_evaluate_command(
            repo_root=repo_root,
            problem=args.problem,
            optimizer=args.optimizer,
            num_epochs=args.num_epochs,
            num_steps=args.num_steps,
            path=args.path,
        )
        if args.optimizer == "Adam" and args.path:
            _warn("Adam does not load optimizer weights from --path; it only affects MNIST/CIFAR mode selection")
        if args.optimizer == "L2L" and not args.path:
            _warn("L2L evaluation without --path uses an untrained optimizer")

    if args.problem in DATA_PROBLEMS and not args.allow_data:
        if args.run:
            raise SystemExit(
                f"{args.problem} may download data or start queues; pass --allow-data to run it intentionally"
            )
        _warn(
            f"{args.problem} may download data or start queues; the printed command is for manual use only unless --allow-data is set"
        )

    if args.print_command or not args.run:
        print(command, flush=True)

    if args.run:
        _validate_environment()
        if args.mode == "train" and args.save_path:
            save_dir = Path(args.save_path).expanduser()
            if save_dir.exists():
                raise SystemExit(f"save_path already exists: {save_dir}")
            save_dir.parent.mkdir(parents=True, exist_ok=True)
        if args.mode == "evaluate" and args.optimizer == "L2L" and args.path:
            path_dir = Path(args.path).expanduser()
            if not path_dir.exists():
                raise SystemExit(f"L2L path does not exist: {path_dir}")
            missing = [name for name in _expected_l2l_files(args.problem) if not (path_dir / name).is_file()]
            if missing:
                raise SystemExit(
                    f"L2L path is missing expected file(s): {', '.join(missing)} in {path_dir}"
                )
        run_argv = [
            sys.executable,
            "train.py" if args.mode == "train" else "evaluate.py",
            f"--problem={args.problem}",
            f"--num_epochs={args.num_epochs}",
            f"--num_steps={args.num_steps}",
        ]
        if args.mode == "train":
            run_argv.append(f"--unroll_length={args.unroll_length}")
            run_argv.append("--log_period=1")
            if args.save_path:
                run_argv.append(f"--save_path={args.save_path}")
                run_argv.append("--evaluation_period=1")
                run_argv.append("--evaluation_epochs=1")
            else:
                run_argv.append("--evaluation_period=999999")
        else:
            run_argv.append(f"--optimizer={args.optimizer}")
            if args.path:
                run_argv.append(f"--path={args.path}")
        subprocess.run(run_argv, cwd=str(repo_root), check=True)


if __name__ == "__main__":
    main()
