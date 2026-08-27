#!/usr/bin/env python3
"""Inspect Otter checkpoint conversion arguments without loading checkpoints.

This helper is intentionally static and safe. It does not import torch,
transformers, otter_ai, or any converter module. Use it to list available
conversion routes, validate required flags, and emit a command only after the
caller has chosen explicit checkpoint/output paths.
"""

from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Converter:
    manifest_id: str
    module: str
    purpose: str
    required_flags: tuple[str, ...]
    optional_flags: tuple[str, ...]
    defaults: dict[str, str]
    effects: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    known_risk: bool = False


CONVERTERS: dict[str, Converter] = {
    "fp32-to-fp16": Converter(
        manifest_id="fp32-to-fp16",
        module="otter_ai.models.otter.converting_otter_fp32_to_fp16",
        purpose="Load an Otter Hugging Face checkpoint in fp16 or bf16 and save a lower-precision checkpoint.",
        required_flags=("--checkpoint_path",),
        optional_flags=("--load_bit {fp16,bf16}", "--save_path"),
        defaults={"load_bit": "fp16", "save_path": "<checkpoint_path>-<load_bit>"},
        effects=("Loads OtterForConditionalGeneration.from_pretrained(..., device_map='auto').", "Saves with OtterForConditionalGeneration.save_pretrained(...)."),
        warnings=("Requires enough memory to load the checkpoint before writing output.",),
    ),
    "flamingo-to-otter": Converter(
        manifest_id="flamingo-to-otter",
        module="otter_ai.models.otter.converting_flamingo_to_otter",
        purpose="Convert a Hugging Face Flamingo checkpoint to an Otter-format checkpoint by adding the <answer> token and saving through Otter.",
        required_flags=("--checkpoint_path", "--save_path"),
        optional_flags=(),
        defaults={"save_path": "source parser default is None; provide explicitly"},
        effects=("Loads FlamingoForConditionalGeneration.from_pretrained(..., device_map='auto').", "Adds Otter answer token and resizes Llama embeddings when applicable.", "Saves with OtterForConditionalGeneration.save_pretrained(...)."),
        warnings=("Use only for Hugging Face-format Flamingo checkpoints.", "Do not omit --save_path."),
    ),
    "otter-to-lora": Converter(
        manifest_id="otter-to-lora",
        module="otter_ai.models.otter.converting_otter_to_lora",
        purpose="Add PEFT LoRA structure and lora_config metadata to an Otter checkpoint.",
        required_flags=("--checkpoint_path", "--save_path"),
        optional_flags=(),
        defaults={"checkpoint_path": "private development default omitted", "save_path": "private development default omitted"},
        effects=("Loads OtterForConditionalGeneration.from_pretrained(..., device_map='auto').", "Adds LoRA r=16, alpha=32, dropout=0.05.", "Targets q_proj/v_proj for Llama/OPT/GPT-J, query_key_value for GPT-NeoX, and Wqkv for MPT.", "Saves with OtterForConditionalGeneration.save_pretrained(...)."),
        warnings=("Always pass explicit checkpoint and output paths.", "Architecture must be supported by the converter's target-module map."),
    ),
    "pt-to-hf": Converter(
        manifest_id="pt-to-hf",
        module="otter_ai.models.otter.converting_otter_pt_to_hf",
        purpose="Inject a .pt state dict into a pretrained Otter Hugging Face base and save a Hugging Face folder.",
        required_flags=("--old_ckpt_path", "--new_hf_path", "--pretrained_model_path"),
        optional_flags=("-old", "-new", "-pretrained"),
        defaults={"pretrained_model_path": "luodian/OTTER-MPT7B-Init in source, but helper requires explicit selection"},
        effects=("Loads torch checkpoint on CPU and unwraps model_state_dict when present.", "Loads pretrained Otter base with device_map='auto'.", "load_state_dict(..., strict=False), then save_pretrained(...)."),
        warnings=("Known packaged-entry import defect was observed before argument parsing in the inspected build.", "Use only after verifying a fixed installed package or a project-owned patched workflow."),
        known_risk=True,
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely inspect Otter checkpoint conversion arguments and optionally emit a command. No model loading is performed.",
    )
    parser.add_argument("--list", action="store_true", help="List known conversion routes.")
    parser.add_argument("--script", choices=sorted(CONVERTERS), help="Conversion route to describe or validate.")
    parser.add_argument("--checkpoint-path", help="Value for --checkpoint_path.")
    parser.add_argument("--save-path", help="Value for --save_path.")
    parser.add_argument("--load-bit", choices=("fp16", "bf16"), default="fp16", help="Precision for fp32-to-fp16 route.")
    parser.add_argument("--old-ckpt-path", help="Value for --old_ckpt_path in PT-to-HF route.")
    parser.add_argument("--new-hf-path", help="Value for --new_hf_path in PT-to-HF route.")
    parser.add_argument("--pretrained-model-path", help="Value for --pretrained_model_path in PT-to-HF route.")
    parser.add_argument("--emit-command", action="store_true", help="Emit a python -m command after validating required values.")
    parser.add_argument("--allow-known-risk", action="store_true", help="Allow command emission for converters marked as known-risk.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args()


def converter_to_json(conv: Converter) -> dict[str, Any]:
    data = asdict(conv)
    data["required_flags"] = list(conv.required_flags)
    data["optional_flags"] = list(conv.optional_flags)
    data["effects"] = list(conv.effects)
    data["warnings"] = list(conv.warnings)
    return data


def selected_values(args: argparse.Namespace, conv: Converter) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    command_args: list[str] = []

    def require(attr: str, flag: str) -> str | None:
        value = getattr(args, attr)
        if not value:
            errors.append(f"{flag} is required for {conv.manifest_id}")
            return None
        return value

    if conv.manifest_id == "fp32-to-fp16":
        checkpoint = require("checkpoint_path", "--checkpoint-path")
        if checkpoint:
            command_args.extend(["--checkpoint_path", checkpoint])
        command_args.extend(["--load_bit", args.load_bit])
        if args.save_path:
            command_args.extend(["--save_path", args.save_path])

    elif conv.manifest_id == "flamingo-to-otter":
        checkpoint = require("checkpoint_path", "--checkpoint-path")
        save = require("save_path", "--save-path")
        if checkpoint:
            command_args.extend(["--checkpoint_path", checkpoint])
        if save:
            command_args.extend(["--save_path", save])

    elif conv.manifest_id == "otter-to-lora":
        checkpoint = require("checkpoint_path", "--checkpoint-path")
        save = require("save_path", "--save-path")
        if checkpoint:
            command_args.extend(["--checkpoint_path", checkpoint])
        if save:
            command_args.extend(["--save_path", save])

    elif conv.manifest_id == "pt-to-hf":
        old = require("old_ckpt_path", "--old-ckpt-path")
        new = require("new_hf_path", "--new-hf-path")
        pretrained = require("pretrained_model_path", "--pretrained-model-path")
        if old:
            command_args.extend(["--old_ckpt_path", old])
        if new:
            command_args.extend(["--new_hf_path", new])
        if pretrained:
            command_args.extend(["--pretrained_model_path", pretrained])

    if conv.known_risk and args.emit_command and not args.allow_known_risk:
        errors.append(f"{conv.manifest_id} is marked known-risk; pass --allow-known-risk after verifying the installed build")

    return errors, command_args


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    if args.list or not args.script:
        report = {
            "safe": True,
            "converters": [converter_to_json(CONVERTERS[key]) for key in sorted(CONVERTERS)],
        }
        return report, 0

    conv = CONVERTERS[args.script]
    errors, command_args = selected_values(args, conv)
    command = ["python", "-m", conv.module] + command_args if args.emit_command and not errors else None
    report = {
        "safe": True,
        "converter": converter_to_json(conv),
        "valid": not errors,
        "errors": errors,
        "command": command,
        "shell_command": shlex.join(command) if command else None,
    }
    return report, 0 if not errors else 2


def print_text(report: dict[str, Any]) -> None:
    if "converters" in report:
        print("Known safe-inspection conversion routes:")
        for conv in report["converters"]:
            risk = " [KNOWN RISK]" if conv["known_risk"] else ""
            print(f"- {conv['manifest_id']}{risk}: {conv['purpose']}")
            print(f"  module: {conv['module']}")
            print(f"  required: {', '.join(conv['required_flags']) or '(none)'}")
        return

    conv = report["converter"]
    risk = " [KNOWN RISK]" if conv["known_risk"] else ""
    print(f"{conv['manifest_id']}{risk}")
    print(f"purpose: {conv['purpose']}")
    print(f"module: {conv['module']}")
    print(f"required: {', '.join(conv['required_flags']) or '(none)'}")
    if conv["optional_flags"]:
        print(f"optional: {', '.join(conv['optional_flags'])}")
    if conv["defaults"]:
        print("defaults/effects:")
        for key, value in conv["defaults"].items():
            print(f"  {key}: {value}")
    if conv["warnings"]:
        print("warnings:")
        for warning in conv["warnings"]:
            print(f"  - {warning}")
    if report["errors"]:
        print("errors:")
        for error in report["errors"]:
            print(f"  - {error}")
    if report["shell_command"]:
        print("command:")
        print(report["shell_command"])


def main() -> int:
    args = parse_args()
    report, code = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=False))
    else:
        print_text(report)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
