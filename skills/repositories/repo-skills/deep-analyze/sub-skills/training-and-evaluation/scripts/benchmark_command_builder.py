#!/usr/bin/env python3
"""Render safe DeepAnalyze benchmark command plans.

The script validates arguments and prints command plans for bundled benchmark
playgrounds. It does not execute inference, evaluation, downloads, or scoring.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import sys
from typing import Dict, Iterable, List, Sequence, Tuple


SUPPORTED_TABLEQA_TASKS = [
    "ottqa",
    "tatqa",
    "finqa",
    "hybridqa",
    "multihiertt",
    "tablebench",
    "hitab",
    "wikitq",
    "fetaqa",
    "aitqa",
    "feverous",
    "totto",
    "wikisql",
    "tabfact",
]

PLACEHOLDER_MARKERS = [
    "path_to",
    "path-to",
    "path to",
    "PATH_TO",
    "YOUR_API_KEY",
    "xxxxx",
    "<",
    ">",
]


def q(value: object) -> str:
    return shlex.quote(str(value))


def has_placeholder(value: str) -> bool:
    low = value.lower()
    return any(marker.lower() in low for marker in PLACEHOLDER_MARKERS)


def require_value(name: str, value: str | None, errors: List[str], allow_placeholders: bool) -> None:
    if value is None or not str(value).strip():
        errors.append(f"missing required argument: {name}")
        return
    if has_placeholder(str(value)) and not allow_placeholders:
        errors.append(f"{name} still looks like a placeholder: {value!r}")


def check_paths(paths: Iterable[Path], errors: List[str]) -> None:
    for path in paths:
        if not path.exists():
            errors.append(f"required path does not exist: {path}")


def looks_like_local_path(value: str) -> bool:
    if value.startswith(("http://", "https://")):
        return False
    if Path(value).exists():
        return True
    if value.startswith(("./", "../", "/", "~")):
        return True
    return False


def shell_command(argv: Sequence[str]) -> str:
    if len(argv) <= 2:
        return " ".join(q(part) for part in argv)
    return " \\\n  ".join(q(part) for part in argv)


def parse_tasks(raw: str) -> List[str]:
    tasks = [part.strip() for part in raw.split(",") if part.strip()]
    if not tasks:
        raise ValueError("--tasks must contain at least one TableQA task")
    unknown = [task for task in tasks if task not in SUPPORTED_TABLEQA_TASKS]
    if unknown:
        raise ValueError(f"unsupported TableQA task(s): {', '.join(unknown)}")
    return tasks


def build_dabstep(args: argparse.Namespace, errors: List[str], warnings: List[str]) -> Dict[str, object]:
    require_value("--model-id", args.model_id, errors, args.allow_placeholders)
    require_value("--api-url", args.api_url, errors, args.allow_placeholders)
    if args.check_files:
        root = Path(args.repo_root) / "playground" / "DABStep-Research"
        check_paths([root / args.task_jsonl, root / args.context_dir], errors)
    notes = [
        "The official runner uses constants for model id, API URL, context path, output path, and process count; put the values below in a local wrapper or edited working copy before execution.",
        "Completed task ids are skipped when their JSONL outputs already exist in the output directory.",
        "Run evaluator only after configuring a real OpenAI-compatible evaluator key/base URL/model.",
    ]
    commands = [
        ["cd", "playground/DABStep-Research"],
        ["python", "run_deepanalyze.py"],
    ]
    return {
        "playground": "dabstep",
        "working_directory": "playground/DABStep-Research",
        "settings": {
            "model_id": args.model_id,
            "api_url": args.api_url,
            "task_jsonl": args.task_jsonl,
            "context_dir": args.context_dir,
            "output_dir": args.output_dir,
            "num_processes": args.num_processes,
        },
        "commands": commands,
        "notes": notes,
        "dry_run_only": True,
    }


def build_ds1000(args: argparse.Namespace, errors: List[str], warnings: List[str]) -> Dict[str, object]:
    require_value("--model-path", args.model_path, errors, args.allow_placeholders)
    require_value("--model-slug", args.model_slug, errors, args.allow_placeholders)
    if args.check_files:
        root = Path(args.repo_root) / "playground" / "DS-1000"
        check_paths([root / "data" / "ds1000.jsonl.gz", root / "run_deepanalyze.py", root / "test_ds1000.py"], errors)
        if args.model_path and looks_like_local_path(args.model_path):
            check_paths([Path(args.model_path)], errors)
    if args.model_slug and ("/" in args.model_slug or "\\" in args.model_slug):
        errors.append("--model-slug must be a filesystem-safe slug, not a path")
    infer_cmd = ["python", "run_deepanalyze.py", "--model", args.model_path or "", "--model_name", args.model_slug or ""]
    if args.resume:
        infer_cmd.append("--resume")
    eval_cmd = ["python", "test_ds1000.py", "--model", args.model_slug or ""]
    return {
        "playground": "ds1000",
        "working_directory": "playground/DS-1000",
        "commands": [["cd", "playground/DS-1000"], infer_cmd, eval_cmd],
        "outputs": [
            f"data/{args.model_slug}-answers.jsonl",
            f"results/{args.model_slug}-result.txt",
            f"results/{args.model_slug}-log.json",
        ],
        "notes": [
            "Use the same model slug for inference --model_name and evaluation --model.",
            "The tester executes generated code; run in an isolated benchmark environment.",
        ],
        "dry_run_only": True,
    }


def build_dsbench_analysis(args: argparse.Namespace, errors: List[str], warnings: List[str]) -> Dict[str, object]:
    require_value("--model-slug", args.model_slug, errors, args.allow_placeholders)
    require_value("--api-base", args.api_base, errors, args.allow_placeholders)
    if args.check_files:
        root = Path(args.repo_root) / "playground" / "DSBench" / "data_analysis"
        check_paths([root / "data.json", root / "run_deepanalyze.py", root / "compute_answer.py", root / "show_result.py"], errors)
    return {
        "playground": "dsbench-analysis",
        "working_directory": "playground/DSBench/data_analysis",
        "settings": {"model_slug": args.model_slug, "api_base": args.api_base},
        "commands": [
            ["cd", "playground/DSBench/data_analysis"],
            ["python", "run_deepanalyze.py"],
            ["python", "compute_answer.py"],
            ["python", "show_result.py"],
        ],
        "outputs": [f"save_process/{args.model_slug}/", "results.json"],
        "notes": [
            "The data-analysis runner contains model and endpoint constants; configure them in a local wrapper or edited working copy before running.",
            "Existing per-sample JSON files are skipped.",
            "Processed DSBench data-analysis files must be unzipped under the expected data directory.",
        ],
        "dry_run_only": True,
    }


def build_dsbench_modeling(args: argparse.Namespace, errors: List[str], warnings: List[str]) -> Dict[str, object]:
    require_value("--model-slug", args.model_slug, errors, args.allow_placeholders)
    require_value("--model-path", args.model_path, errors, args.allow_placeholders)
    if args.check_files:
        root = Path(args.repo_root) / "playground" / "DSBench" / "data_modeling"
        check_paths([root / "data.json", root / "run_deepanalyze.py", root / "score4each_com.py", root / "show_result.py"], errors)
        if args.model_path and looks_like_local_path(args.model_path):
            check_paths([Path(args.model_path)], errors)
    return {
        "playground": "dsbench-modeling",
        "working_directory": "playground/DSBench/data_modeling",
        "settings": {"model_slug": args.model_slug, "model_path": args.model_path},
        "commands": [
            ["cd", "playground/DSBench/data_modeling"],
            ["python", "run_deepanalyze.py"],
            ["python", "score4each_com.py"],
            ["python", "show_result.py"],
        ],
        "outputs": [f"output_model/{args.model_slug}/", f"save_performance/{args.model_slug}/"],
        "notes": [
            "The data-modeling runner contains working directory and model constants; configure them in a local wrapper or edited working copy before running.",
            "Existing per-task CSV files are skipped.",
            "Each task can run for a long time and expects a generated submission.csv in its task workspace.",
        ],
        "dry_run_only": True,
    }


def tableqa_paths(args: argparse.Namespace, task: str) -> Tuple[str, str, str, str, str]:
    stem = f"{task}_{args.model_size}_{args.train_type}"
    pred = f"results/{args.model_slug}/{task}/{stem}.json"
    infer_log = f"results/{args.model_slug}/{task}/logs/{stem}_infer.log"
    if args.eval_mode == "standard":
        eval_out = f"results/{args.model_slug}/{task}/{stem}_eval_results.json"
        eval_log = ""
        eval_script = f"{args.tests_dir}/eval/{task}_eval.py"
    elif args.eval_mode == "llm":
        eval_out = f"results/{args.model_slug}/{task}/{stem}_llm_eval_results.json"
        eval_log = f"results/{args.model_slug}/{task}/logs/{stem}_llm_eval.log"
        eval_script = f"{args.tests_dir}/llm_eval/{task}_eval.py"
    else:
        eval_out = f"results/{args.model_slug}/{task}/{stem}_combined_eval_results.json"
        eval_log = f"results/{args.model_slug}/{task}/logs/{stem}_combined_eval.log"
        eval_script = f"{args.tests_dir}/llm_eval/{task}_combined_eval.py"
    return pred, infer_log, eval_out, eval_log, eval_script


def build_tableqa(args: argparse.Namespace, errors: List[str], warnings: List[str]) -> Dict[str, object]:
    require_value("--model-path", args.model_path, errors, args.allow_placeholders)
    require_value("--model-slug", args.model_slug, errors, args.allow_placeholders)
    tasks = parse_tasks(args.tasks)
    if args.eval_mode in {"llm", "combined"}:
        require_value("--eval-model-path", args.eval_model_path, errors, args.allow_placeholders)
    if args.check_files:
        root = Path(args.repo_root) / "playground" / "TableQA"
        check_paths([root / args.tests_dir], errors)
        for task in tasks:
            pred, infer_log, eval_out, eval_log, eval_script = tableqa_paths(args, task)
            check_paths([root / args.tests_dir / f"{task}.py", root / eval_script], errors)
        if args.model_path and looks_like_local_path(args.model_path):
            check_paths([Path(args.model_path)], errors)
        if args.eval_model_path and looks_like_local_path(args.eval_model_path):
            check_paths([Path(args.eval_model_path)], errors)
    commands: List[List[str]] = [["cd", "playground/TableQA"]]
    outputs: List[str] = []
    for task in tasks:
        pred, infer_log, eval_out, eval_log, eval_script = tableqa_paths(args, task)
        outputs.extend([pred, infer_log, eval_out])
        infer_cmd = [
            "python",
            f"{args.tests_dir}/{task}.py",
            "--model_path",
            args.model_path or "",
            "--output_file",
            pred,
            "--log_file",
            infer_log,
            "--base_path",
            ".",
            "--tensor_parallel_size",
            str(args.tensor_parallel_size),
            "--batch_size",
            str(args.batch_size),
            "--max_tokens",
            str(args.max_tokens),
            "--temperature",
            "0.0",
        ]
        commands.append(infer_cmd)
        if args.eval_mode == "standard":
            eval_cmd = [
                "python",
                eval_script,
                "--results_file",
                pred,
                "--output_file",
                eval_out,
                "--base_path",
                ".",
            ]
        else:
            eval_cmd = [
                "python",
                eval_script,
                "--results_file",
                pred,
                "--output_file",
                eval_out,
                "--model_path",
                args.eval_model_path or "",
                "--log_file",
                eval_log,
                "--base_path",
                ".",
                "--batch_size",
                str(args.llm_eval_batch_size),
                "--tensor_parallel_size",
                str(args.tensor_parallel_size),
            ]
            if args.eval_mode == "combined":
                eval_cmd.extend(["--evaluation_mode", "combined"])
            outputs.append(eval_log)
        commands.append(eval_cmd)
    return {
        "playground": "tableqa",
        "working_directory": "playground/TableQA",
        "tasks": tasks,
        "eval_mode": args.eval_mode,
        "commands": commands,
        "outputs": outputs,
        "notes": [
            "Verify whether the actual task directory is tests or tests_our before launch.",
            "LLM and combined modes require a real evaluator model path or accepted API model identifier.",
            "Prediction temp files may indicate partial inference progress.",
        ],
        "dry_run_only": True,
    }


def build_plan(args: argparse.Namespace) -> Tuple[Dict[str, object], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if args.playground == "dabstep":
        plan = build_dabstep(args, errors, warnings)
    elif args.playground == "ds1000":
        plan = build_ds1000(args, errors, warnings)
    elif args.playground == "dsbench-analysis":
        plan = build_dsbench_analysis(args, errors, warnings)
    elif args.playground == "dsbench-modeling":
        plan = build_dsbench_modeling(args, errors, warnings)
    elif args.playground == "tableqa":
        plan = build_tableqa(args, errors, warnings)
    else:
        errors.append(f"unsupported playground: {args.playground}")
        plan = {}
    return plan, warnings, errors


def render_shell(plan: Dict[str, object], warnings: Sequence[str]) -> str:
    lines: List[str] = ["# Dry-run DeepAnalyze benchmark command plan. Review before executing manually."]
    if warnings:
        lines.append("# Warnings:")
        for warning in warnings:
            lines.append(f"# - {warning}")
    lines.append(f"# Playground: {plan['playground']}")
    lines.append(f"# Working directory: {plan['working_directory']}")
    if plan.get("settings"):
        lines.append("# Settings:")
        for key, value in plan["settings"].items():  # type: ignore[index,union-attr]
            lines.append(f"# - {key}: {value}")
    if plan.get("outputs"):
        lines.append("# Expected outputs:")
        for output in plan["outputs"]:  # type: ignore[index]
            lines.append(f"# - {output}")
    if plan.get("notes"):
        lines.append("# Notes:")
        for note in plan["notes"]:  # type: ignore[index]
            lines.append(f"# - {note}")
    lines.append("")
    for command in plan["commands"]:  # type: ignore[index]
        if command and command[0] == "cd":
            lines.append(f"cd {q(command[1])}")
        else:
            lines.append(shell_command(command))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render DeepAnalyze benchmark playground command plans without executing them.")
    parser.add_argument("playground", choices=["dabstep", "ds1000", "dsbench-analysis", "dsbench-modeling", "tableqa"])
    parser.add_argument("--repo-root", default=".", help="Repository root used only for --check-files.")
    parser.add_argument("--check-files", action="store_true", help="Require local prerequisite files to exist.")
    parser.add_argument("--allow-placeholders", action="store_true", help="Allow placeholder-looking values for template generation. Default rejects them.")
    parser.add_argument("--format", choices=["shell", "json"], default="shell")

    parser.add_argument("--model-path", help="Local model checkpoint path for local vLLM-based playgrounds.")
    parser.add_argument("--model-slug", help="Filesystem-safe output slug for the evaluated model.")
    parser.add_argument("--model-id", help="Served model identifier for API-based DABStep agent.")
    parser.add_argument("--api-url", default="http://localhost:8000/v1/chat/completions", help="OpenAI-compatible chat-completions URL for DABStep.")
    parser.add_argument("--api-base", default="http://localhost:8000/v1", help="OpenAI-compatible base URL for DSBench analysis wrappers.")

    parser.add_argument("--task-jsonl", default="dabstep_research.jsonl", help="DABStep task JSONL file name.")
    parser.add_argument("--context-dir", default="context", help="DABStep context directory.")
    parser.add_argument("--output-dir", default="runs/deepanalyze", help="DABStep output directory.")
    parser.add_argument("--num-processes", type=int, default=4, help="DABStep process count.")

    parser.add_argument("--resume", action="store_true", help="Render resume flag where supported.")

    parser.add_argument("--tasks", default="wikitq", help="Comma-separated TableQA task names.")
    parser.add_argument("--eval-mode", choices=["standard", "llm", "combined"], default="standard", help="TableQA evaluation mode.")
    parser.add_argument("--eval-model-path", help="TableQA evaluator model path or API model id for llm/combined modes.")
    parser.add_argument("--train-type", default="sft", help="TableQA output suffix.")
    parser.add_argument("--model-size", default="8b", help="TableQA output suffix.")
    parser.add_argument("--tensor-parallel-size", type=int, default=1, help="TableQA tensor parallelism.")
    parser.add_argument("--batch-size", type=int, default=256, help="TableQA inference batch size.")
    parser.add_argument("--max-tokens", type=int, default=32000, help="TableQA max generation tokens.")
    parser.add_argument("--llm-eval-batch-size", type=int, default=32, help="TableQA LLM evaluation batch/concurrency.")
    parser.add_argument("--tests-dir", default="tests", help="TableQA tests directory, usually tests or tests_our.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        plan, warnings, errors = build_plan(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps({"plan": plan, "warnings": warnings}, indent=2))
    else:
        print(render_shell(plan, warnings), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
