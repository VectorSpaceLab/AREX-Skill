#!/usr/bin/env python3
"""Print a safe disaggregated launch plan from a LightX2V config file.

This helper does not start any processes. It only resolves the service mode
and prints the entry-point commands and a short role summary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _resolve_mode(args: argparse.Namespace, cfg: dict[str, Any]) -> str:
    if args.service != "auto":
        return args.service
    mode = cfg.get("disagg_mode")
    if mode in {"controller", "encoder", "transformer", "decoder"}:
        return str(mode)
    raise ValueError("Cannot resolve service mode: use --service or set disagg_mode in config_json")


def _role_commands(model_cls: str, task: str, model_path: str, config_json: str, service_mode: str, seed: int, prompt: str, negative_prompt: str, save_result_path: str) -> dict[str, str]:
    base = (
        "python -m lightx2v.disagg.examples.run_service "
        f"--service {service_mode} "
        f"--model_cls {model_cls} "
        f"--task {task} "
        f"--model_path {model_path} "
        f"--config_json {config_json} "
        f"--seed {seed} "
        f"--prompt {json.dumps(prompt)} "
        f"--negative_prompt {json.dumps(negative_prompt)} "
        f"--save_result_path {json.dumps(save_result_path)}"
    )
    return {"service": base}


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a LightX2V disagg launch plan")
    parser.add_argument("--config_json", required=True, help="Disagg config JSON")
    parser.add_argument("--service", default="auto", choices=["auto", "controller", "encoder", "transformer", "decoder"], help="Explicit service mode")
    parser.add_argument("--model_cls", default="wan2.1")
    parser.add_argument("--task", default="t2v")
    parser.add_argument("--model_path", default="/path/to/model")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--prompt", default="Two anthropomorphic cats in comfy boxing gear and bright gloves fight intensely on a spotlighted stage.")
    parser.add_argument("--negative_prompt", default="")
    parser.add_argument("--save_result_path", default="save_results/disagg_output.mp4")
    parser.add_argument("--emit-shell", action="store_true", help="Print a shell-friendly command instead of JSON")
    args = parser.parse_args()

    cfg = _load_json(args.config_json)
    service_mode = _resolve_mode(args, cfg)
    commands = _role_commands(args.model_cls, args.task, args.model_path, args.config_json, service_mode, args.seed, args.prompt, args.negative_prompt, args.save_result_path)

    report = {
        "service_mode": service_mode,
        "config_json": str(Path(args.config_json)),
        "commands": commands,
        "important_keys": {
            "disagg_mode": cfg.get("disagg_mode"),
            "bootstrap_addr": cfg.get("disagg_config", {}).get("bootstrap_addr") if isinstance(cfg.get("disagg_config"), dict) else None,
            "encoder_engine_rank": cfg.get("disagg_config", {}).get("encoder_engine_rank") if isinstance(cfg.get("disagg_config"), dict) else None,
            "transformer_engine_rank": cfg.get("disagg_config", {}).get("transformer_engine_rank") if isinstance(cfg.get("disagg_config"), dict) else None,
            "decoder_engine_rank": cfg.get("disagg_config", {}).get("decoder_engine_rank") if isinstance(cfg.get("disagg_config"), dict) else None,
        },
    }

    if args.emit_shell:
        print(commands["service"])
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
