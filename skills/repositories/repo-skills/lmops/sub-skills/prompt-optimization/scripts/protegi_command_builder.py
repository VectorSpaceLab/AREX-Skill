#!/usr/bin/env python3
"""Build and validate a ProTeGi command without running it.

The script is intentionally self-contained and side-effect free. It imports only
Python standard-library modules, performs lightweight path/prompt checks, and
prints the command that a prepared ProTeGi run directory could execute later.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

TASK_LAYOUTS = {
    "ethos": {
        "class": "EthosBinaryTask",
        "files": ["ethos_ishate_binary_shuf.csv"],
        "description": "semicolon CSV with text in column 0 and numeric score in column 1",
    },
    "jailbreak": {
        "class": "JailbreakBinaryTask",
        "files": ["train.tsv", "test.tsv"],
        "description": "TSV lines: JSON conversation, tab, integer label",
    },
    "liar": {
        "class": "DefaultHFBinaryTask",
        "files": ["train.jsonl", "test.jsonl"],
        "description": "JSONL records with text and integer label",
    },
    "ar_sarcasm": {
        "class": "DefaultHFBinaryTask",
        "files": ["train.jsonl", "test.jsonl"],
        "description": "JSONL records with text and integer label",
    },
}

EVALUATORS = {
    "bf": "BruteForceEvaluator",
    "ucb": "UCBBanditEvaluator",
    "ucb-e": "UCBBanditEvaluator",
    "sr": "SuccessiveRejectsEvaluator",
    "s-sr": "SuccessiveRejectsEvaluator",
    "sh": "SuccessiveHalvingEvaluator",
}

SCORERS = {
    "01": "Cached01Scorer",
    "ll": "CachedLogLikelihoodScorer",
}

PROMPT_PLACEHOLDER = "{{ text }}"


def non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:  # pragma: no cover - argparse displays this
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def positive_int(value: str) -> int:
    parsed = non_negative_int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return parsed


def non_negative_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:  # pragma: no cover - argparse displays this
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def split_prompts(value: str) -> List[str]:
    prompts = [item.strip() for item in value.split(",") if item.strip()]
    if not prompts:
        raise argparse.ArgumentTypeError("provide at least one prompt markdown path")
    return prompts


def add_path_issue(policy: str, message: str, errors: List[str], warnings: List[str]) -> None:
    if policy == "error":
        errors.append(message)
    elif policy == "warn":
        warnings.append(message)


def parse_prompt_headers(text: str) -> set[str]:
    headers: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            parts = stripped[2:].strip().lower().split()
            if not parts:
                continue
            first = parts[0]
            cleaned = "".join(ch for ch in first if ch.isalnum() or ch == "_")
            if cleaned:
                headers.add(cleaned)
    return headers


def validate_prompt_file(path: Path, policy: str, errors: List[str], warnings: List[str]) -> None:
    if not path.exists():
        add_path_issue(policy, f"prompt file does not exist: {path}", errors, warnings)
        return
    if not path.is_file():
        add_path_issue(policy, f"prompt path is not a file: {path}", errors, warnings)
        return
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        add_path_issue(policy, f"prompt file is not UTF-8 text: {path}", errors, warnings)
        return
    headers = parse_prompt_headers(text)
    if "task" not in headers:
        warnings.append(f"prompt file lacks a '# Task' section: {path}")
    if "prediction" not in headers:
        warnings.append(f"prompt file lacks a '# Prediction' section: {path}")
    if PROMPT_PLACEHOLDER not in text:
        warnings.append(f"prompt file lacks the '{PROMPT_PLACEHOLDER}' render placeholder: {path}")


def validate_paths(args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if args.path_policy == "ignore":
        return errors, warnings

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        add_path_issue(args.path_policy, f"data directory does not exist: {data_dir}", errors, warnings)
    elif not data_dir.is_dir():
        add_path_issue(args.path_policy, f"data path is not a directory: {data_dir}", errors, warnings)
    else:
        layout = TASK_LAYOUTS[args.task]
        for rel_name in layout["files"]:
            expected = data_dir / rel_name
            if not expected.exists():
                add_path_issue(
                    args.path_policy,
                    f"missing {args.task} data file: {expected} ({layout['description']})",
                    errors,
                    warnings,
                )

    for prompt in args.prompts:
        validate_prompt_file(Path(prompt), args.path_policy, errors, warnings)

    out_path = Path(args.out)
    parent = out_path.parent
    if str(parent) not in {"", "."} and not parent.exists():
        add_path_issue(args.path_policy, f"output parent directory does not exist: {parent}", errors, warnings)
    if out_path.exists():
        warnings.append(f"output file already exists and the native program would remove it: {out_path}")

    return errors, warnings


def validate_semantics(args: argparse.Namespace) -> List[str]:
    errors: List[str] = []
    if args.knn_t > 1:
        errors.append("--knn-t should normally be between 0 and 1")
    if args.evaluator in {"sr", "s-sr", "sh"} and args.beam_size <= 0:
        errors.append("--beam-size must be positive for rejection/halving evaluators")
    if args.eval_prompts_per_round > args.beam_size and args.evaluator in {"sr", "s-sr", "ucb", "ucb-e"}:
        # Not fatal: the native code clips some values, but users should notice the budget shape.
        pass
    return errors


def build_command(args: argparse.Namespace) -> List[str]:
    command = [
        args.python,
        args.entrypoint,
        "--task",
        args.task,
        "--data_dir",
        args.data_dir,
        "--prompts",
        ",".join(args.prompts),
        "--out",
        args.out,
        "--max_threads",
        str(args.max_threads),
        "--temperature",
        str(args.temperature),
        "--optimizer",
        args.optimizer,
        "--rounds",
        str(args.rounds),
        "--beam_size",
        str(args.beam_size),
        "--n_test_exs",
        str(args.n_test_exs),
        "--minibatch_size",
        str(args.minibatch_size),
        "--n_gradients",
        str(args.n_gradients),
        "--errors_per_gradient",
        str(args.errors_per_gradient),
        "--gradients_per_error",
        str(args.gradients_per_error),
        "--steps_per_gradient",
        str(args.steps_per_gradient),
        "--mc_samples_per_step",
        str(args.mc_samples_per_step),
        "--max_expansion_factor",
        str(args.max_expansion_factor),
        "--engine",
        args.engine,
        "--evaluator",
        args.evaluator,
        "--scorer",
        args.scorer,
        "--eval_rounds",
        str(args.eval_rounds),
        "--eval_prompts_per_round",
        str(args.eval_prompts_per_round),
        "--samples_per_eval",
        str(args.samples_per_eval),
        "--c",
        str(args.c),
        "--knn_k",
        str(args.knn_k),
        "--knn_t",
        str(args.knn_t),
    ]
    if args.reject_on_errors:
        command.append("--reject_on_errors")
    return command


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and validate a ProTeGi command. The command is printed but never run.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--python", default="python", help="Python executable to place in the emitted command")
    parser.add_argument("--entrypoint", default="main.py", help="ProTeGi entrypoint path relative to the run directory")
    parser.add_argument("--task", required=True, choices=sorted(TASK_LAYOUTS), help="Built-in binary task name")
    parser.add_argument("--data-dir", "--data_dir", dest="data_dir", required=True, help="Task data directory")
    parser.add_argument("--prompts", required=True, type=split_prompts, help="Comma-separated prompt markdown file(s)")
    parser.add_argument("--out", required=True, help="Output log file path for the future ProTeGi run")
    parser.add_argument("--path-policy", choices=["warn", "error", "ignore"], default="warn", help="How to handle missing files during planning")

    parser.add_argument("--max-threads", "--max_threads", dest="max_threads", type=positive_int, default=32)
    parser.add_argument("--temperature", type=non_negative_float, default=0.0)
    parser.add_argument("--optimizer", default="nl-gradient")
    parser.add_argument("--rounds", type=non_negative_int, default=6)
    parser.add_argument("--beam-size", "--beam_size", dest="beam_size", type=positive_int, default=4)
    parser.add_argument("--n-test-exs", "--n_test_exs", dest="n_test_exs", type=positive_int, default=400)
    parser.add_argument("--minibatch-size", "--minibatch_size", dest="minibatch_size", type=positive_int, default=64)
    parser.add_argument("--n-gradients", "--n_gradients", dest="n_gradients", type=non_negative_int, default=4)
    parser.add_argument("--errors-per-gradient", "--errors_per_gradient", dest="errors_per_gradient", type=positive_int, default=4)
    parser.add_argument("--gradients-per-error", "--gradients_per_error", dest="gradients_per_error", type=positive_int, default=1)
    parser.add_argument("--steps-per-gradient", "--steps_per_gradient", dest="steps_per_gradient", type=positive_int, default=1)
    parser.add_argument("--mc-samples-per-step", "--mc_samples_per_step", dest="mc_samples_per_step", type=non_negative_int, default=2)
    parser.add_argument("--max-expansion-factor", "--max_expansion_factor", dest="max_expansion_factor", type=positive_int, default=8)
    parser.add_argument("--engine", default="chatgpt")
    parser.add_argument("--evaluator", choices=sorted(EVALUATORS), default="bf")
    parser.add_argument("--scorer", choices=sorted(SCORERS), default="01")
    parser.add_argument("--eval-rounds", "--eval_rounds", dest="eval_rounds", type=positive_int, default=8)
    parser.add_argument("--eval-prompts-per-round", "--eval_prompts_per_round", dest="eval_prompts_per_round", type=positive_int, default=8)
    parser.add_argument("--samples-per-eval", "--samples_per_eval", dest="samples_per_eval", type=positive_int, default=32)
    parser.add_argument("--c", type=non_negative_float, default=1.0, help="UCB exploration parameter")
    parser.add_argument("--knn-k", "--knn_k", dest="knn_k", type=positive_int, default=2)
    parser.add_argument("--knn-t", "--knn_t", dest="knn_t", type=non_negative_float, default=0.993)
    parser.add_argument("--reject-on-errors", "--reject_on_errors", dest="reject_on_errors", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print JSON with command and validation messages instead of a shell command")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    semantic_errors = validate_semantics(args)
    path_errors, warnings = validate_paths(args)
    errors = semantic_errors + path_errors
    command = build_command(args)
    eval_budget = args.samples_per_eval * args.eval_rounds * args.eval_prompts_per_round

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    payload = {
        "safe": True,
        "runs_command": False,
        "imports_repo_code": False,
        "downloads_models": False,
        "command": command,
        "shell_command": shlex.join(command),
        "eval_budget": eval_budget,
        "warnings": warnings,
        "task": args.task,
        "task_class": TASK_LAYOUTS[args.task]["class"],
        "task_layout": TASK_LAYOUTS[args.task],
        "evaluator_class": EVALUATORS[args.evaluator],
        "scorer_class": SCORERS[args.scorer],
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        print("# This script only prints the command; it does not run ProTeGi.", file=sys.stderr)
        print(f"# Computed eval_budget={eval_budget}.", file=sys.stderr)
        print(shlex.join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
