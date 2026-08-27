#!/usr/bin/env python3
"""Build a dry XTuner RL launch snippet.

This helper adapts the useful environment/command construction behavior of
XTuner's source-style RL shell launcher without starting Ray, creating work
directories, or launching training. It prints shell exports followed by an
XTuner RL CLI command for review or copy/paste.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from dataclasses import dataclass, field
from typing import Iterable


BACKENDS = ("sglang", "lmdeploy", "vllm")


@dataclass
class Plan:
    exports: dict[str, str] = field(default_factory=dict)
    unsets: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    command: list[str] = field(default_factory=list)


def q(value: object) -> str:
    return shlex.quote(str(value))


def parse_key_value(text: str) -> tuple[str, str]:
    if "=" not in text:
        raise argparse.ArgumentTypeError(f"expected KEY=VALUE, got {text!r}")
    key, value = text.split("=", 1)
    if not key or any(ch in key for ch in " \t\n="):
        raise argparse.ArgumentTypeError(f"invalid environment key in {text!r}")
    return key, value


def visible_cuda_count() -> int | None:
    raw = os.environ.get("CUDA_VISIBLE_DEVICES")
    if not raw:
        return None
    parts = [item.strip() for item in raw.split(",") if item.strip()]
    return len(parts) or None


def default_accelerator_per_node(accelerator: str, explicit: int | None) -> int:
    if explicit is not None:
        return explicit
    if accelerator == "NPU":
        return 16
    return visible_cuda_count() or 8


def add_backend_env(plan: Plan, backend: str, fa3: str) -> None:
    for name in ("XTUNER_USE_SGLANG", "XTUNER_USE_LMDEPLOY", "XTUNER_USE_VLLM"):
        plan.exports[name] = "0"

    if backend == "sglang":
        plan.exports["XTUNER_USE_SGLANG"] = "1"
        plan.exports["SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN"] = "1"
        plan.exports["SGLANG_ENABLE_HEALTH_ENDPOINT_GENERATION"] = "False"
        plan.unsets.append("PYTORCH_CUDA_ALLOC_CONF")
    elif backend == "lmdeploy":
        plan.exports["XTUNER_USE_LMDEPLOY"] = "1"
        plan.exports["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
        plan.exports.setdefault("LMDEPLOY_LOG_FILE", "$WORK_DIR/lmdeploy_log.txt")
    elif backend == "vllm":
        plan.exports["XTUNER_USE_VLLM"] = "1"
        plan.exports["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    else:  # pragma: no cover - argparse choices prevent this
        raise ValueError(f"unsupported backend: {backend}")

    plan.exports["XTUNER_USE_FA3"] = fa3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Emit environment exports plus an XTuner RL CLI command. "
            "The helper has no Ray-start or training side effects."
        )
    )
    parser.add_argument("--config", required=True, help="RL Python config path to pass to --config.")
    parser.add_argument("--backend", required=True, choices=BACKENDS, help="Rollout backend env flag to enable.")
    parser.add_argument("--model-path", required=True, help="Value for MODEL_PATH.")
    parser.add_argument("--data-path", required=True, help="Value for DATA_PATH.")
    parser.add_argument("--eval-data-path", default="", help="Value for EVAL_DATA_PATH; many configs require it.")
    parser.add_argument("--work-dir", required=True, help="Value for WORK_DIR and optional --work-dir CLI override.")
    parser.add_argument(
        "--num-workers",
        type=int,
        default=None,
        help="Value for XTUNER_RL_NUM_WORKERS and --num-workers. Defaults to node_count * accelerators_per_node.",
    )
    parser.add_argument("--node-count", type=int, default=int(os.environ.get("NODE_COUNT", "1")))
    parser.add_argument("--node-rank", type=int, default=int(os.environ.get("NODE_RANK", os.environ.get("RANK", "0"))))
    parser.add_argument("--accelerator", choices=("GPU", "NPU", "gpu", "npu"), default=os.environ.get("ACCELERATOR", "GPU"))
    parser.add_argument("--accelerator-per-node", type=int, default=None, help="Visible accelerators per node.")
    parser.add_argument("--master-addr", default=os.environ.get("MASTER_ADDR", "127.0.0.1"))
    parser.add_argument("--master-port", default=os.environ.get("MASTER_PORT", "6000"))
    parser.add_argument("--ray-head-port", default=os.environ.get("RAY_HEAD_PORT", "6379"))
    parser.add_argument("--ray-dashboard-port", default=os.environ.get("RAY_DASHBOARD_PORT", "8265"))
    parser.add_argument("--fa3", choices=("0", "1"), default=os.environ.get("XTUNER_USE_FA3", "1"))
    parser.add_argument("--xtuner-log-level", default=os.environ.get("XTUNER_LOG_LEVEL", "INFO"))
    parser.add_argument("--python", default=os.environ.get("PYTHON", "python"), help="Python executable for the command.")
    parser.add_argument(
        "--omit-work-dir-flag",
        action="store_true",
        help="Do not pass --work-dir to the CLI command; keep WORK_DIR env only.",
    )
    parser.add_argument(
        "--omit-num-workers-flag",
        action="store_true",
        help="Do not pass --num-workers to the CLI command; keep XTUNER_RL_NUM_WORKERS env only.",
    )
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Add deterministic env used by native SGLang deterministic wrappers; requires --backend sglang.",
    )
    parser.add_argument(
        "--enable-mem-monitor",
        action="store_true",
        help="Set XTUNER_RL_MEM_DIR under WORK_DIR and XTUNER_RL_MEM_INTERVAL.",
    )
    parser.add_argument("--mem-interval", type=int, default=60)
    parser.add_argument(
        "--extra-env",
        action="append",
        type=parse_key_value,
        default=[],
        metavar="KEY=VALUE",
        help="Additional export to include; may be repeated.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON plan instead of shell text.",
    )
    parser.add_argument(
        "--no-comments",
        action="store_true",
        help="Suppress shell comments in text output.",
    )
    return parser


def build_plan(args: argparse.Namespace) -> Plan:
    accelerator = str(args.accelerator).upper()
    accelerator_per_node = default_accelerator_per_node(accelerator, args.accelerator_per_node)
    num_workers = args.num_workers if args.num_workers is not None else args.node_count * accelerator_per_node

    if args.deterministic and args.backend != "sglang":
        raise SystemExit("--deterministic is only supported with --backend sglang")
    if args.node_count < 1:
        raise SystemExit("--node-count must be >= 1")
    if accelerator_per_node < 1:
        raise SystemExit("--accelerator-per-node must be >= 1")
    if num_workers < 1:
        raise SystemExit("--num-workers must be >= 1")

    plan = Plan()
    plan.comments.extend(
        [
            "Generated dry XTuner RL launch snippet; review before executing.",
            "This helper did not start Ray, create directories, or launch training.",
            "Ray must already be running because the XTuner RL CLI uses ray.init(address=\"auto\").",
        ]
    )

    plan.exports.update(
        {
            "ACCELERATOR": accelerator,
            "MASTER_PORT": str(args.master_port),
            "WORLD_SIZE": str(args.node_count),
            "RANK": str(args.node_rank),
            "RAY_MASTER_ADDR": str(args.master_addr),
            "RAY_RANK": str(args.node_rank),
            "RAY_HEAD_PORT": str(args.ray_head_port),
            "RAY_DASHBOARD_PORT": str(args.ray_dashboard_port),
            "WORK_DIR": args.work_dir,
            "MODEL_PATH": args.model_path,
            "DATA_PATH": args.data_path,
            "EVAL_DATA_PATH": args.eval_data_path,
            "XTUNER_LOG_LEVEL": args.xtuner_log_level,
            "PYTHONUNBUFFERED": "1",
            "XTUNER_RL_NUM_WORKERS": str(num_workers),
        }
    )
    add_backend_env(plan, args.backend, args.fa3)

    if args.deterministic:
        plan.exports["XTUNER_DETERMINISTIC"] = "true"
        plan.exports["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE"] = "0"
        plan.exports["XTUNER_USE_FA3"] = "0"
        plan.comments.append("Deterministic mode mirrors native SGLang deterministic wrappers and disables FA3.")

    if args.enable_mem_monitor:
        plan.exports["XTUNER_RL_MEM_DIR"] = "$WORK_DIR/mem"
        plan.exports["XTUNER_RL_MEM_INTERVAL"] = str(args.mem_interval)

    for key, value in args.extra_env:
        plan.exports[key] = value

    command: list[str] = [args.python, "-m", "xtuner.v1.train.cli.rl"]
    command.extend(["--config", args.config])
    if not args.omit_work_dir_flag:
        command.extend(["--work-dir", args.work_dir])
    if not args.omit_num_workers_flag:
        command.extend(["--num-workers", str(num_workers)])
    plan.command = command
    return plan


def emit_shell(plan: Plan, *, comments: bool = True) -> str:
    lines: list[str] = []
    if comments:
        lines.extend(f"# {comment}" for comment in plan.comments)
    for key, value in plan.exports.items():
        if value.startswith("$WORK_DIR/"):
            lines.append(f'export {key}="$WORK_DIR/{value[len("$WORK_DIR/") :]}"')
        else:
            lines.append(f"export {key}={q(value)}")
    for key in dict.fromkeys(plan.unsets):
        lines.append(f"unset {key}")
    if comments:
        lines.append("# Optional preflight: ray status && python - <<'PY' ... ray.init(address=\"auto\") ... PY")
    lines.append(" ".join(q(part) for part in plan.command))
    return "\n".join(lines) + "\n"


def plan_to_json(plan: Plan) -> str:
    return json.dumps(
        {
            "comments": plan.comments,
            "exports": plan.exports,
            "unsets": plan.unsets,
            "command": plan.command,
            "command_string": " ".join(q(part) for part in plan.command),
        },
        indent=2,
        sort_keys=True,
    ) + "\n"


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    plan = build_plan(args)
    if args.json:
        sys.stdout.write(plan_to_json(plan))
    else:
        sys.stdout.write(emit_shell(plan, comments=not args.no_comments))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
