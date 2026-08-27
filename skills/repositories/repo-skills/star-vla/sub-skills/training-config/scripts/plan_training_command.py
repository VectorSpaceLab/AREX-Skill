#!/usr/bin/env python3
"""Plan a StarVLA Accelerate training command without launching training.

The script reads a StarVLA YAML, validates extra dotlist overrides in KEY=VALUE
shape, and prints a shell-quoted command plan. It has no StarVLA imports and
never calls accelerate or a training entry point.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - exercised only when PyYAML is absent
    yaml = None

ENTRYPOINTS = {
    "vla": "starVLA/training/train_starvla.py",
    "cotrain": "starVLA/training/train_starvla_cotrain.py",
    "vlm": "starVLA/training/train_starvlm.py",
}

KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise SystemExit(
            "PyYAML is required to read StarVLA YAML files. Install pyyaml or run this in a StarVLA environment."
        )
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except FileNotFoundError:
        raise SystemExit(f"Config YAML not found: {path}") from None
    except Exception as exc:
        raise SystemExit(f"Failed to parse YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Expected top-level YAML mapping in {path}")
    return data


def dotted_get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    cur: Any = data
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def validate_overrides(items: Iterable[str]) -> list[str]:
    overrides: list[str] = []
    errors: list[str] = []
    for raw in items:
        if raw.startswith("--"):
            errors.append(f"{raw!r}: use KEY=VALUE without leading '--'")
            continue
        if "=" not in raw:
            errors.append(f"{raw!r}: expected KEY=VALUE")
            continue
        key, _value = raw.split("=", 1)
        if not key:
            errors.append(f"{raw!r}: empty key")
            continue
        if any(ch.isspace() for ch in key):
            errors.append(f"{raw!r}: whitespace is not allowed in the key")
            continue
        if not KEY_PATTERN.match(key):
            errors.append(
                f"{raw!r}: key should be a dotted identifier such as trainer.max_train_steps"
            )
            continue
        overrides.append(raw)
    if errors:
        raise SystemExit("Invalid override(s):\n  - " + "\n  - ".join(errors))
    return overrides


def maybe_num_processes_from_accelerate(path: Path) -> int | None:
    if not path.exists() or yaml is None:
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    if isinstance(data, dict):
        value = data.get("num_processes")
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def shell_join_multiline(tokens: list[str], env: dict[str, str]) -> str:
    prefix = " ".join(f"{name}={shlex.quote(value)}" for name, value in env.items())
    quoted = [shlex.quote(token) for token in tokens]
    parts = ([prefix] if prefix else []) + quoted
    if len(parts) <= 6:
        return " ".join(parts)
    lines = [parts[0] + " \\"]
    for part in parts[1:-1]:
        lines.append(f"  {part} \\")
    lines.append(f"  {parts[-1]}")
    return "\n".join(lines)


def summarize_config(config: dict[str, Any], overrides: list[str], entrypoint_key: str, num_processes: int) -> str:
    keys = [
        ("framework.name", dotted_get(config, "framework.name", "<unset>")),
        ("run_root_dir", dotted_get(config, "run_root_dir", "<unset>")),
        ("run_id", dotted_get(config, "run_id", "<unset>")),
        ("datasets.vla_data.dataset_py", dotted_get(config, "datasets.vla_data.dataset_py", "<unset>")),
        ("datasets.vla_data.data_mix", dotted_get(config, "datasets.vla_data.data_mix", "<unset>")),
        ("datasets.vlm_data.dataset_use", dotted_get(config, "datasets.vlm_data.dataset_use", "<unset>")),
        ("trainer.max_train_steps", dotted_get(config, "trainer.max_train_steps", "<unset>")),
        ("trainer.save_interval", dotted_get(config, "trainer.save_interval", "<unset>")),
        ("trainer.eval_interval", dotted_get(config, "trainer.eval_interval", "<unset>")),
        ("trainer.freeze_modules", dotted_get(config, "trainer.freeze_modules", "<unset>")),
    ]
    lines = [
        "# StarVLA training command plan (dry run; not executed)",
        f"# Entrypoint: {entrypoint_key} -> {ENTRYPOINTS[entrypoint_key]}",
        f"# Planned processes: {num_processes}",
        "# YAML summary:",
    ]
    lines.extend(f"#   {key}: {value}" for key, value in keys)
    if overrides:
        lines.append("# Extra overrides, applied after YAML:")
        lines.extend(f"#   {item}" for item in overrides)
    else:
        lines.append("# Extra overrides: <none>")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read a StarVLA YAML and print an accelerate launch command plan without launching training."
    )
    parser.add_argument(
        "--config-yaml",
        "--config_yaml",
        dest="config_yaml",
        required=True,
        help="Path to the StarVLA training YAML. The emitted training command uses StarVLA's --config_yaml option.",
    )
    parser.add_argument(
        "--entrypoint",
        choices=sorted(ENTRYPOINTS),
        default="vla",
        help="Training entry point to plan: vla, cotrain, or vlm. Default: vla.",
    )
    parser.add_argument(
        "--accelerate-config",
        default="starVLA/config/deepseeds/deepspeed_zero2.yaml",
        help="Accelerate/DeepSpeed config path for --config_file.",
    )
    parser.add_argument(
        "--num-processes",
        type=int,
        default=None,
        help="Number of accelerate worker processes. Defaults to num_processes in the accelerate config when readable, else 1.",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra OmegaConf dotlist override. Repeat for multiple overrides. Use an empty value as KEY=.",
    )
    parser.add_argument(
        "--enable-wandb",
        action="store_true",
        help="Do not add WANDB_MODE=disabled to the printed command plan.",
    )
    parser.add_argument(
        "--print-json-summary",
        action="store_true",
        help="Also print a compact machine-readable summary after the command plan.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path = Path(args.config_yaml)
    accelerate_config = Path(args.accelerate_config)
    config = load_yaml(config_path)
    overrides = validate_overrides(args.override)

    inferred_processes = maybe_num_processes_from_accelerate(accelerate_config)
    num_processes = args.num_processes if args.num_processes is not None else (inferred_processes or 1)
    if num_processes < 1:
        raise SystemExit("--num-processes must be >= 1")

    env: dict[str, str] = {"TOKENIZERS_PARALLELISM": "false"}
    if not args.enable_wandb:
        env = {"WANDB_MODE": "disabled", **env}

    command = [
        "accelerate",
        "launch",
        "--config_file",
        str(accelerate_config),
        "--num_processes",
        str(num_processes),
        ENTRYPOINTS[args.entrypoint],
        "--config_yaml",
        str(config_path),
    ]
    command.extend(f"--{item}" for item in overrides)

    print(summarize_config(config, overrides, args.entrypoint, num_processes))
    print("# Command:")
    print(shell_join_multiline(command, env))

    if args.print_json_summary:
        import json

        print("# JSON summary:")
        print(
            json.dumps(
                {
                    "config_yaml": str(config_path),
                    "entrypoint": ENTRYPOINTS[args.entrypoint],
                    "accelerate_config": str(accelerate_config),
                    "num_processes": num_processes,
                    "overrides": overrides,
                    "wandb_disabled": not args.enable_wandb,
                    "output_dir_from_yaml": os.path.join(
                        str(dotted_get(config, "run_root_dir", "<unset>")),
                        str(dotted_get(config, "run_id", "<unset>")),
                    ),
                },
                indent=2,
                sort_keys=True,
            )
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
