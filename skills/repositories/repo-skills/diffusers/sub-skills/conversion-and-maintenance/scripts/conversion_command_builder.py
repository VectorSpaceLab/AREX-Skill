#!/usr/bin/env python3
"""Print safe Diffusers conversion plans without running conversion.

This helper is self-contained. It does not assume the original Diffusers
repository conversion scripts are available. It emits an argument checklist and a
skeleton using a user-provided conversion entrypoint placeholder.
"""

from __future__ import annotations

import argparse
import shlex


FAMILIES = (
    "original-sd-to-diffusers",
    "diffusers-to-original-sd",
    "diffusers-to-original-sdxl",
    "lora-safetensor-to-diffusers",
    "extract-lora",
    "stable-diffusion-onnx",
)

ENTRYPOINT_HINTS = {
    "original-sd-to-diffusers": "entrypoint that converts original Stable Diffusion .ckpt/.safetensors checkpoints into a Diffusers directory",
    "diffusers-to-original-sd": "entrypoint that exports a Diffusers Stable Diffusion directory to an original-format checkpoint",
    "diffusers-to-original-sdxl": "entrypoint that exports a Diffusers SDXL directory to an original-format checkpoint",
    "lora-safetensor-to-diffusers": "entrypoint that merges a LoRA safetensors adapter into a base Diffusers pipeline",
    "extract-lora": "entrypoint that extracts LoRA deltas from a base/fine-tuned model pair",
    "stable-diffusion-onnx": "entrypoint that exports a Stable Diffusion Diffusers directory to ONNX",
}


def shell_join(parts: list[str]) -> str:
    return " \\\n  ".join(shlex.quote(part) for part in parts)


def value_or_placeholder(value: str | None, placeholder: str) -> str:
    return value if value is not None else placeholder


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=FAMILIES, required=True, help="Conversion family to plan.")
    parser.add_argument("--entrypoint", default="<user-conversion-entrypoint.py>", help="User-provided conversion script/module to place in the skeleton.")
    parser.add_argument("--checkpoint-path", help="Source or target checkpoint path, depending on family.")
    parser.add_argument("--model-path", help="Source Diffusers model directory or model id, depending on family.")
    parser.add_argument("--base-model-path", help="Base Diffusers model path for LoRA merge/extraction.")
    parser.add_argument("--finetune-ckpt-path", help="Fine-tuned model path for LoRA extraction.")
    parser.add_argument("--output-path", help="Output file or directory path.")
    parser.add_argument("--config-path", help="Original config file/config directory when required by the source format.")
    parser.add_argument("--device", default="cpu", help="Device to include for scripts that accept a device argument.")
    parser.add_argument("--half", action="store_true", help="Include half/fp16 output flags where supported.")
    parser.add_argument("--safetensors", action="store_true", help="Prefer safetensors input/output flags where supported.")
    parser.add_argument("--local-only", action="store_true", help="Add reminder comments for local/offline operation.")
    parser.add_argument("--alpha", type=float, default=0.75, help="LoRA merge alpha for lora-safetensor-to-diffusers.")
    parser.add_argument("--rank", type=int, default=64, help="LoRA rank for extract-lora.")
    parser.add_argument("--opset", type=int, default=14, help="ONNX opset for stable-diffusion-onnx.")
    args = parser.parse_args()

    comments = [
        "# Self-contained plan: replace <user-conversion-entrypoint.py> with a conversion script the user owns or has explicitly provided.",
        "# This builder prints a skeleton only; it does not run conversion, download weights, or push to the Hub.",
        f"# Family intent: {ENTRYPOINT_HINTS[args.family]}",
    ]
    if args.local_only:
        comments.append("# Local/offline requested: use local paths/configs and avoid Hub-oriented commands.")

    if args.family == "original-sd-to-diffusers":
        command = [
            "python",
            args.entrypoint,
            "--checkpoint_path",
            value_or_placeholder(args.checkpoint_path, "./model.safetensors"),
            "--dump_path",
            value_or_placeholder(args.output_path, "./converted-diffusers"),
            "--device",
            args.device,
        ]
        if args.config_path:
            command += ["--original_config_file", args.config_path]
        if args.safetensors:
            command += ["--from_safetensors", "--to_safetensors"]
        if args.half:
            command.append("--half")
    elif args.family == "diffusers-to-original-sd":
        command = [
            "python",
            args.entrypoint,
            "--model_path",
            value_or_placeholder(args.model_path, "./diffusers-model"),
            "--checkpoint_path",
            value_or_placeholder(args.output_path, "./model.safetensors" if args.safetensors else "./model.ckpt"),
        ]
        if args.safetensors:
            command.append("--use_safetensors")
        if args.half:
            command.append("--half")
    elif args.family == "diffusers-to-original-sdxl":
        command = [
            "python",
            args.entrypoint,
            "--model_path",
            value_or_placeholder(args.model_path, "./sdxl-diffusers-model"),
            "--checkpoint_path",
            value_or_placeholder(args.output_path, "./sdxl-model.safetensors" if args.safetensors else "./sdxl-model.ckpt"),
        ]
        if args.safetensors:
            command.append("--use_safetensors")
        if args.half:
            command.append("--half")
    elif args.family == "lora-safetensor-to-diffusers":
        command = [
            "python",
            args.entrypoint,
            "--base_model_path",
            value_or_placeholder(args.base_model_path, "./base-diffusers-model"),
            "--checkpoint_path",
            value_or_placeholder(args.checkpoint_path, "./adapter.safetensors"),
            "--dump_path",
            value_or_placeholder(args.output_path, "./merged-pipeline"),
            "--alpha",
            str(args.alpha),
            "--device",
            args.device,
        ]
        if args.safetensors:
            command.append("--to_safetensors")
    elif args.family == "extract-lora":
        output_path = value_or_placeholder(args.output_path, "./extracted-lora.safetensors")
        if not output_path.endswith(".safetensors"):
            parser.error("extract-lora requires --output-path ending in .safetensors")
        command = [
            "python",
            args.entrypoint,
            "--base_ckpt_path",
            value_or_placeholder(args.base_model_path, "./base-model"),
            "--base_subfolder",
            "transformer",
            "--finetune_ckpt_path",
            value_or_placeholder(args.finetune_ckpt_path, "./finetuned-model"),
            "--finetune_subfolder",
            "transformer",
            "--rank",
            str(args.rank),
            "--lora_out_path",
            output_path,
        ]
    else:
        command = [
            "python",
            args.entrypoint,
            "--model_path",
            value_or_placeholder(args.model_path, "./sd-diffusers-model"),
            "--output_path",
            value_or_placeholder(args.output_path, "./sd-onnx"),
            "--opset",
            str(args.opset),
        ]
        if args.half:
            comments.append("# fp16 ONNX export generally requires CUDA; do not request it on CPU-only hosts.")
            command.append("--fp16")

    print("\n".join(comments))
    print(shell_join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
