#!/usr/bin/env python3
"""Smoke-check a YiVal installation without requiring provider credentials."""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
import traceback
from typing import Any, Dict, List


BUILTIN_MODULES = [
    "yival.data.csv_reader",
    "yival.data.huggingface_dataset_reader",
    "yival.data_generators.document_data_generator",
    "yival.data_generators.openai_prompt_data_generator",
    "yival.variation_generators.chain_of_density_prompt",
    "yival.variation_generators.openai_prompt_based_variation_generator",
    "yival.variation_generators.self_exemplar",
    "yival.evaluators.alpaca_eval_evaluator",
    "yival.evaluators.bertscore_evaluator",
    "yival.evaluators.openai_elo_evaluator",
    "yival.evaluators.openai_prompt_based_evaluator",
    "yival.evaluators.python_validation_evaluator",
    "yival.evaluators.rouge_evaluator",
    "yival.evaluators.string_expected_result_evaluator",
    "yival.result_selectors.ahp_selection",
    "yival.enhancers.openai_prompt_based_combination_enhancer",
    "yival.enhancers.optimize_by_prompt_enhancer",
    "yival.enhancers.pe2_enhancer",
    "yival.wrappers.string_wrapper",
]

CORE_MODULES = [
    "yival",
    "yival.__main__",
    "yival.cli",
    "yival.cli.utils",
    "yival.configs.config_utils",
    "yival.experiment.experiment_runner",
    "yival.experiment.lite_experiment",
]


def try_import(module_name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        return {"module": module_name, "ok": True, "file": getattr(module, "__file__", None)}
    except Exception as exc:  # pragma: no cover - diagnostic script
        return {
            "module": module_name,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback_tail": traceback.format_exc().splitlines()[-5:],
        }


def collect_registries() -> Dict[str, List[str]]:
    from yival.data.base_reader import BaseReader
    from yival.data_generators.base_data_generator import BaseDataGenerator
    from yival.enhancers.base_combination_enhancer import BaseCombinationEnhancer
    from yival.evaluators.base_evaluator import BaseEvaluator
    from yival.result_selectors.selection_strategy import SelectionStrategy
    from yival.variation_generators.base_variation_generator import BaseVariationGenerator
    from yival.wrappers.base_wrapper import BaseWrapper

    return {
        "readers": sorted(BaseReader._registry.keys()),
        "data_generators": sorted(BaseDataGenerator._registry.keys()),
        "variation_generators": sorted(BaseVariationGenerator._registry.keys()),
        "evaluators": sorted(BaseEvaluator._registry.keys()),
        "selection_strategies": sorted(SelectionStrategy._registry.keys()),
        "enhancers": sorted(BaseCombinationEnhancer._registry.keys()),
        "wrappers": sorted(BaseWrapper._registry.keys()),
    }


def check_cli_help() -> Dict[str, Any]:
    cmd = [sys.executable, "-m", "yival", "--help"]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout_head": proc.stdout.splitlines()[:20],
        "stderr_head": proc.stderr.splitlines()[:20],
        "ok": proc.returncode == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-cli", action="store_true", help="also run python -m yival --help")
    args = parser.parse_args()

    imports = [try_import(name) for name in CORE_MODULES]
    imports.extend(try_import(name) for name in BUILTIN_MODULES)
    registries: Dict[str, List[str]] | Dict[str, Any]
    try:
        registries = collect_registries()
    except Exception as exc:  # pragma: no cover - diagnostic script
        registries = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    report: Dict[str, Any] = {
        "python": sys.version,
        "executable": sys.executable,
        "imports": imports,
        "registries": registries,
    }
    if args.check_cli:
        try:
            report["cli_help"] = check_cli_help()
        except Exception as exc:  # pragma: no cover - diagnostic script
            report["cli_help"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(report, indent=2, sort_keys=True))

    failed_imports = [item for item in imports if not item["ok"]]
    cli_failed = args.check_cli and not report.get("cli_help", {}).get("ok", False)
    return 1 if failed_imports or cli_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
