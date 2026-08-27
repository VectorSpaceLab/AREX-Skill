#!/usr/bin/env python3
"""Print a dry-run DeepAnalyze vLLM serving command.

The script never launches vLLM. It only renders the recommended command from
GPU memory, model type, and optional overrides.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from dataclasses import dataclass
from typing import Optional


SUPPORTED_ROWS = {
    16: {
        "8bit": {"max_model_len": 8192, "kv_cache_dtype": "fp8"},
        "4bit": {"max_model_len": 49152, "kv_cache_dtype": "fp8"},
    },
    24: {
        "original": {"max_model_len": 16384, "kv_cache_dtype": "fp8"},
        "8bit": {"max_model_len": 98304, "kv_cache_dtype": "fp8"},
        "4bit": {"max_model_len": 131072, "kv_cache_dtype": "fp8"},
    },
    40: {
        "original": {"max_model_len": 131072, "kv_cache_dtype": "fp8"},
        "8bit": {"max_model_len": 131072, "kv_cache_dtype": None},
    },
    80: {
        "original": {"max_model_len": 131072, "kv_cache_dtype": None},
    },
}

MODEL_SOURCE_HINT = {
    "huggingface": "RUC-DataLab/DeepAnalyze-8B on Hugging Face",
    "modelscope": "RUC-DataLab/DeepAnalyze-8B on ModelScope",
    "local": "local checkpoint path",
}


@dataclass(frozen=True)
class Selection:
    memory_gb: int
    model_type: str
    max_model_len: int
    kv_cache_dtype: Optional[str]


def choose_model_type(memory_gb: int, goal: str) -> str:
    if memory_gb == 16:
        return "4bit"
    if memory_gb == 24:
        return "4bit" if goal == "max-context" else "original"
    if memory_gb in (40, 80):
        return "original"
    raise ValueError(f"Unsupported GPU memory value: {memory_gb}")


def resolve_selection(memory_gb: int, model_type: str, goal: str, kv_cache_dtype: str) -> Selection:
    selected_type = model_type if model_type != "auto" else choose_model_type(memory_gb, goal)
    rows = SUPPORTED_ROWS.get(memory_gb)
    if rows is None:
        raise ValueError(f"Unsupported GPU memory value: {memory_gb}")
    if selected_type not in rows:
        raise ValueError(
            f"The table does not list model type '{selected_type}' for {memory_gb}GB. "
            "Pick a supported row or change the memory target."
        )
    row = rows[selected_type]
    selected_kv = row["kv_cache_dtype"]
    if kv_cache_dtype == "fp8":
        selected_kv = "fp8"
    elif kv_cache_dtype == "off":
        selected_kv = None
    return Selection(
        memory_gb=memory_gb,
        model_type=selected_type,
        max_model_len=row["max_model_len"],
        kv_cache_dtype=selected_kv,
    )


def render_shell_command(args: list[str]) -> str:
    if not args:
        return ""
    lines = [shlex.quote(args[0])]
    for arg in args[1:]:
        lines.append(f"  {shlex.quote(arg)}")
    separator = " " + "\\" + "\n"
    return separator.join(lines)


def build_plan(ns: argparse.Namespace) -> dict:
    selection = resolve_selection(ns.gpu_memory_gb, ns.model_type, ns.goal, ns.kv_cache_dtype)
    command = [
        ns.python,
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        ns.model_path,
        "--served-model-name",
        ns.served_model_name,
        "--max-model-len",
        str(selection.max_model_len),
        "--gpu-memory-utilization",
        f"{ns.gpu_memory_utilization:.2f}",
        "--port",
        str(ns.port),
    ]
    if ns.host:
        command.extend(["--host", ns.host])
    if selection.kv_cache_dtype == "fp8":
        command.extend(["--kv-cache-dtype", "fp8"])
    command.append("--trust-remote-code")
    if ns.extra_arg:
        for item in ns.extra_arg:
            command.append(item)

    return {
        "source_hint": MODEL_SOURCE_HINT.get(ns.source_hint, ns.source_hint),
        "selection": {
            "memory_gb": selection.memory_gb,
            "model_type": selection.model_type,
            "max_model_len": selection.max_model_len,
            "kv_cache_dtype": selection.kv_cache_dtype,
        },
        "command": command,
        "shell": render_shell_command(command),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a dry-run DeepAnalyze vLLM launch command."
    )
    parser.add_argument("--model-path", required=True, help="Path or model identifier to serve.")
    parser.add_argument(
        "--gpu-memory-gb",
        type=int,
        choices=sorted(SUPPORTED_ROWS),
        required=True,
        help="GPU memory bucket from the repo table.",
    )
    parser.add_argument(
        "--model-type",
        choices=["auto", "original", "8bit", "4bit"],
        default="auto",
        help="Pick a table row explicitly or let the planner choose.",
    )
    parser.add_argument(
        "--goal",
        choices=["balanced", "max-context"],
        default="balanced",
        help="Used only when model-type is auto.",
    )
    parser.add_argument(
        "--kv-cache-dtype",
        choices=["auto", "fp8", "off"],
        default="auto",
        help="Override whether the command includes --kv-cache-dtype fp8.",
    )
    parser.add_argument("--served-model-name", default="DeepAnalyze-8B")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.95)
    parser.add_argument("--host", default="", help="Optional host override for container or remote use.")
    parser.add_argument("--python", default="python", help="Python executable to print in the command.")
    parser.add_argument(
        "--source-hint",
        choices=["huggingface", "modelscope", "local"],
        default="local",
        help="Annotate the source location in the dry-run summary.",
    )
    parser.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        help="Append an extra raw argument to the rendered command.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON instead of a shell block.",
    )
    return parser.parse_args()


def main() -> int:
    ns = parse_args()
    try:
        plan = build_plan(ns)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if ns.json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0

    selection = plan["selection"]
    print(f"Source hint: {plan['source_hint']}")
    print(
        "Selection: "
        f"{selection['memory_gb']}GB / {selection['model_type']} / "
        f"max-model-len={selection['max_model_len']} / "
        f"kv-cache={selection['kv_cache_dtype'] or 'off'}"
    )
    print("\nDry-run command:\n")
    print(plan["shell"])
    print("\nNote: this script only prints a command; it does not start vLLM.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
