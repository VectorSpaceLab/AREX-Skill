#!/usr/bin/env python3
"""Safely inspect MetaGPT AFlow/SPO optimizer help and imports.

This helper intentionally avoids optimizer construction, dataset downloads,
LLM initialization, and full extension runs. Help mode uses copied argparse
surfaces from the MetaGPT AFlow/SPO examples; import mode separately reports
whether the installed extension modules are importable in the current runtime.
"""

from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
import sys


sys.path.insert(0, str(Path.cwd()))


TARGET_MODULES = {
    "aflow": [
        "examples.aflow.optimize",
        "metagpt.ext.aflow.scripts.optimizer",
        "metagpt.ext.aflow.scripts.evaluator",
        "metagpt.ext.aflow.benchmark.benchmark",
    ],
    "spo": [
        "examples.spo.optimize",
        "metagpt.ext.spo.components.optimizer",
        "metagpt.ext.spo.utils.llm_client",
    ],
}

AFLOW_DATASETS = ["DROP", "HotpotQA", "MATH", "GSM8K", "MBPP", "HumanEval"]


@dataclass
class CheckResult:
    target: str
    mode: str
    ok: bool
    modules: dict[str, str] = field(default_factory=dict)
    help_text: str = ""
    error: str = ""
    traceback: str = ""


def selected_targets(target: str) -> list[str]:
    if target == "all":
        return sorted(TARGET_MODULES)
    return [target]


def import_modules(target: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for module_name in TARGET_MODULES[target]:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - diagnostic helper should report all import failures
            statuses[module_name] = f"ERROR: {exc.__class__.__name__}: {exc}"
        else:
            statuses[module_name] = "ok"
    return statuses


def build_aflow_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AFlow Optimizer")
    parser.add_argument("--dataset", type=str, choices=AFLOW_DATASETS, required=True, help="Dataset type")
    parser.add_argument("--sample", type=int, default=4, help="Sample count")
    parser.add_argument(
        "--optimized_path",
        type=str,
        default="metagpt/ext/aflow/scripts/optimized",
        help="Optimized result save path",
    )
    parser.add_argument("--initial_round", type=int, default=1, help="Initial round")
    parser.add_argument("--max_rounds", type=int, default=20, help="Max iteration rounds")
    parser.add_argument("--check_convergence", type=bool, default=True, help="Whether to enable early stop")
    parser.add_argument("--validation_rounds", type=int, default=5, help="Validation rounds")
    parser.add_argument(
        "--if_first_optimize",
        type=lambda value: value.lower() == "true",
        default=True,
        help="Whether to download dataset for the first time",
    )
    parser.add_argument(
        "--opt_model_name",
        type=str,
        default="claude-3-5-sonnet-20240620",
        help="Specifies the name of the model used for optimization tasks.",
    )
    parser.add_argument(
        "--exec_model_name",
        type=str,
        default="gpt-4o-mini",
        help="Specifies the name of the model used for execution tasks.",
    )
    return parser


def build_spo_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SPO PromptOptimizer CLI")
    parser.add_argument("--opt-model", type=str, default="claude-3-5-sonnet-20240620", help="Model for optimization")
    parser.add_argument("--opt-temp", type=float, default=0.7, help="Temperature for optimization")
    parser.add_argument("--eval-model", type=str, default="gpt-4o-mini", help="Model for evaluation")
    parser.add_argument("--eval-temp", type=float, default=0.3, help="Temperature for evaluation")
    parser.add_argument("--exec-model", type=str, default="gpt-4o-mini", help="Model for execution")
    parser.add_argument("--exec-temp", type=float, default=0, help="Temperature for execution")
    parser.add_argument("--workspace", type=str, default="workspace", help="Path for optimized output")
    parser.add_argument("--initial-round", type=int, default=1, help="Initial round number")
    parser.add_argument("--max-rounds", type=int, default=10, help="Maximum number of rounds")
    parser.add_argument("--template", type=str, default="Poem.yaml", help="Template file name")
    parser.add_argument("--name", type=str, default="Poem", help="Project name")
    return parser


def capture_parser_help(parser: argparse.ArgumentParser) -> str:
    return parser.format_help()


def run_import_check(target: str) -> CheckResult:
    modules = import_modules(target)
    ok = all(status == "ok" for status in modules.values())
    return CheckResult(target=target, mode="import", ok=ok, modules=modules)


def run_help_check(target: str) -> CheckResult:
    if target == "aflow":
        help_text = capture_parser_help(build_aflow_parser())
    elif target == "spo":
        help_text = capture_parser_help(build_spo_parser())
    else:
        return CheckResult(target=target, mode="help", ok=False, error=f"Unsupported target: {target}")
    modules = {module_name: "not imported in help mode" for module_name in TARGET_MODULES[target]}
    return CheckResult(target=target, mode="help", ok=True, modules=modules, help_text=help_text)


def render_text(results: list[CheckResult], show_help: bool) -> str:
    chunks: list[str] = []
    for result in results:
        status = "ok" if result.ok else "failed"
        chunks.append(f"[{result.target}] {result.mode}: {status}")
        for module_name, module_status in result.modules.items():
            chunks.append(f"  - {module_name}: {module_status}")
        if result.error:
            chunks.append(f"  error: {result.error}")
        if show_help and result.help_text:
            chunks.append("  help:")
            chunks.extend(f"    {line}" for line in result.help_text.rstrip().splitlines())
    return "\n".join(chunks)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely inspect MetaGPT AFlow/SPO optimizer parser help or imports.")
    parser.add_argument("--target", choices=["all", "aflow", "spo"], default="all", help="Optimizer surface to inspect.")
    parser.add_argument("--mode", choices=["help", "import"], default="help", help="Inspection mode.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--show-help",
        action="store_true",
        help="Include captured parser help in text mode. JSON output always includes help_text.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = []
    for target in selected_targets(args.target):
        if args.mode == "import":
            results.append(run_import_check(target))
        else:
            results.append(run_help_check(target))

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
    else:
        print(render_text(results, show_help=args.show_help))

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
