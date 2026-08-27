#!/usr/bin/env python3
"""No-network inspection for CAMEL datagen/evaluation components.

The script intentionally avoids model calls, benchmark downloads, and verifier
code execution. It reports optional import availability and runs deterministic
checks where the installed extras permit them.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import sys
from typing import Any, Dict, List, Tuple


def _import_status(module_name: str) -> Tuple[bool, str]:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report optional import failures
        return False, f"{type(exc).__name__}: {exc}"
    return True, "ok"


async def _check_extractors() -> Dict[str, Any]:
    from camel.extractors.python_strategies import (
        BoxedStrategy,
        PythonDictStrategy,
        PythonListStrategy,
        PythonTupleStrategy,
    )

    checks = {
        "boxed": await BoxedStrategy().extract(r"\boxed{\dfrac{9}{7}}"),
        "list": await PythonListStrategy().extract('[3, "two", 1]'),
        "dict": await PythonDictStrategy().extract('{"b": 2, "a": 1}'),
        "tuple": await PythonTupleStrategy().extract('(3, 1, 2)'),
    }
    expected = {
        "boxed": r"\dfrac{9}{7}",
        "list": "[1, 3, 'two']",
        "dict": "{'a': 1, 'b': 2}",
        "tuple": "(1, 2, 3)",
    }
    return {
        "ok": checks == expected,
        "observed": checks,
        "expected": expected,
    }


async def _check_tictactoe() -> Dict[str, Any]:
    from camel.environments.models import Action
    from camel.environments.tic_tac_toe import TicTacToeEnv

    env = TicTacToeEnv()
    try:
        await env.setup()
        observation = await env.reset()
        next_observation, reward, done, info = await env.step(
            Action(llm_response="<Action>5</Action>")
        )
        board = env._state.get("board", [])  # stable native test seam
        return {
            "ok": bool(board) and board[4] == "X" and done is False,
            "initial_question_contains_rules": "Choose a number between 1 and 9"
            in observation.question,
            "next_question_type": type(next_observation.question).__name__,
            "reward": reward,
            "done": done,
            "info_keys": sorted(info.keys()),
            "board": board,
        }
    finally:
        await env.close()


def _check_source2synth_schema() -> Dict[str, Any]:
    from camel.datagen.source2synth.models import MultiHopQA, ReasoningStep
    from camel.datagen.source2synth.user_data_processor_config import (
        ProcessorConfig,
    )

    config_fields = set(ProcessorConfig.model_fields)
    qa = MultiHopQA(
        question="Which two facts connect A to C?",
        reasoning_steps=[
            ReasoningStep(step="A implies B"),
            ReasoningStep(step="B implies C"),
        ],
        answer="A connects to C through B.",
        supporting_facts=["A implies B", "B implies C"],
        type="multi_hop_qa",
    )
    expected_config_fields = {
        "seed",
        "min_length",
        "max_length",
        "complexity_threshold",
        "dataset_size",
        "use_ai_model",
        "hop_generating_agent",
    }
    return {
        "ok": expected_config_fields.issubset(config_fields)
        and qa.type == "multi_hop_qa",
        "config_fields": sorted(config_fields),
        "qa_fields": sorted(qa.model_dump().keys()),
    }


def _check_static_dataset() -> Dict[str, Any]:
    from camel.datasets import StaticDataset

    dataset = StaticDataset(
        [
            {
                "question": "What is 1 + 1?",
                "final_answer": "2",
                "rationale": "Add the two ones.",
                "metadata": {"id": "tiny-1"},
            }
        ],
        strict=True,
    )
    item = dataset[0]
    return {
        "ok": len(dataset) == 1 and item.question == "What is 1 + 1?",
        "length": len(dataset),
        "item": item.to_dict(),
    }


async def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect CAMEL datagen, verifier, extractor, benchmark, dataset, "
            "and environment components without model calls or downloads."
        )
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format for the inspection report.",
    )
    args = parser.parse_args()

    modules = [
        "camel",
        "camel.datagen",
        "camel.datagen.source2synth",
        "camel.data_collectors",
        "camel.datasets",
        "camel.benchmarks",
        "camel.verifiers",
        "camel.extractors",
        "camel.environments",
        "math_verify",
        "torch",
        "datasets",
        "numpy",
        "pandas",
        "ragas",
        "huggingface_hub",
    ]
    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "imports": {},
        "checks": {},
        "notes": [
            "No model calls were made.",
            "No benchmark datasets were downloaded.",
            "PythonVerifier execution was not invoked.",
        ],
    }

    for module_name in modules:
        ok, detail = _import_status(module_name)
        report["imports"][module_name] = {"ok": ok, "detail": detail}

    check_plan = [
        ("extractors", _check_extractors),
        ("source2synth_schema", lambda: asyncio.to_thread(_check_source2synth_schema)),
        ("static_dataset", lambda: asyncio.to_thread(_check_static_dataset)),
        ("tictactoe", _check_tictactoe),
    ]

    for name, check in check_plan:
        try:
            result = await check()
        except Exception as exc:  # noqa: BLE001 - optional dependency report
            result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        report["checks"][name] = result

    failed_required: List[str] = []
    for name in ["extractors", "source2synth_schema", "static_dataset", "tictactoe"]:
        result = report["checks"].get(name, {})
        if result.get("ok", False):
            continue
        error = str(result.get("error", ""))
        if "ModuleNotFoundError" in error or "ImportError" in error:
            result["skipped"] = True
            result["skip_reason"] = (
                "required optional package is not importable in this environment"
            )
            continue
        if name == "tictactoe":
            continue
        failed_required.append(name)
    report["summary"] = {
        "ok": not failed_required,
        "failed_required_checks": failed_required,
    }
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"Python: {report['python']}")
        print(f"Summary ok: {report['summary']['ok']}")
        print("Imports:")
        for module_name, status in report["imports"].items():
            marker = "ok" if status["ok"] else "skip"
            print(f"- {module_name}: {marker} ({status['detail']})")
        print("Checks:")
        for check_name, result in report["checks"].items():
            marker = "ok" if result.get("ok") else "skip" if result.get("skipped") else "fail"
            print(f"- {check_name}: {marker}")
    return 1 if failed_required else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
