#!/usr/bin/env python3
"""Inspect the current LightLLM StartArgs and CLI run-mode surface."""

from __future__ import annotations

import argparse
import dataclasses
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()

    from lightllm.server.api_cli import add_cli_args
    from lightllm.server.core.objs.start_args_type import StartArgs

    dummy = argparse.ArgumentParser(prog="lightllm-server")
    add_cli_args(dummy)
    run_mode_choices = None
    for action in dummy._actions:
        if getattr(action, "dest", None) == "run_mode":
            run_mode_choices = list(action.choices or [])
            break

    selected_fields = [
        "run_mode",
        "model_dir",
        "model_name",
        "host",
        "port",
        "tp",
        "dp",
        "pd_master_ip",
        "pd_master_port",
        "pd_master_mode",
        "tokenizer_mode",
        "load_way",
        "enable_multimodal",
        "enable_profiling",
        "use_tgi_api",
        "use_reward_model",
        "enable_rl",
        "quant_type",
        "hardware_platform",
    ]
    fields = dataclasses.fields(StartArgs)
    field_map = {field.name: field.default for field in fields if field.name in selected_fields}

    info = {
        "run_mode_choices": run_mode_choices,
        "selected_defaults": field_map,
        "field_count": len(fields),
    }

    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True, default=str))
    else:
        print(f"run_mode_choices={run_mode_choices}")
        print(f"field_count={len(fields)}")
        for key in selected_fields:
            if key in field_map:
                print(f"{key}={field_map[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
