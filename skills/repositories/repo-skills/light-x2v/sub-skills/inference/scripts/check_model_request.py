#!/usr/bin/env python3
"""Validate a LightX2V inference request without running generation.

The script resolves the same config path used by the inference stack, then
prints a compact summary of the normalized request.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path



def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a LightX2V inference request")
    parser.add_argument("--model_cls", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--config_json", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--prompt", default="")
    parser.add_argument("--negative_prompt", default="")
    parser.add_argument("--image_path", default="")
    parser.add_argument("--audio_path", default="")
    parser.add_argument("--last_frame_path", default="")
    parser.add_argument("--save_result_path", default="")
    parser.add_argument("--omni_vision_subtask", default=None)
    parser.add_argument("--subfolder", default=None)
    parser.add_argument("--enable_bf16", action="store_true")
    parser.add_argument("--save_rendered", action="store_true")
    parser.add_argument("--wm_config_path", default=None)
    parser.add_argument("--wm_ckpt_path", default=None)
    parser.add_argument("--strict", action="store_true", help="Fail when the config summary cannot be resolved")
    return parser


def _promote_unknown_flags(args: argparse.Namespace, unknown: list[str]) -> None:
    index = 0
    while index < len(unknown):
        token = unknown[index]
        if not token.startswith("--"):
            index += 1
            continue
        key = token[2:].replace("-", "_")
        next_value = unknown[index + 1] if index + 1 < len(unknown) else None
        if next_value is None or next_value.startswith("--"):
            setattr(args, key, True)
            index += 1
        else:
            setattr(args, key, next_value)
            index += 2


def main() -> int:
    parser = _make_parser()
    args, unknown = parser.parse_known_args()
    _promote_unknown_flags(args, unknown)

    from lightx2v.utils.set_config import set_config

    config = set_config(args)

    summary = {
        "model_cls": config.get("model_cls"),
        "task": config.get("task"),
        "model_path": config.get("model_path"),
        "config_json": config.get("config_json"),
        "infer_steps": config.get("infer_steps"),
        "target_video_length": config.get("target_video_length"),
        "enable_cfg": config.get("enable_cfg"),
        "parallel": config.get("parallel"),
        "cpu_offload": config.get("cpu_offload"),
        "dit_quantized": config.get("dit_quantized"),
        "dit_quant_scheme": config.get("dit_quant_scheme"),
        "lora_configs": config.get("lora_configs"),
        "transformer_model_path": config.get("transformer_model_path"),
        "resolved_model_path_exists": Path(config["model_path"]).exists(),
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
