#!/usr/bin/env python3
"""Print safe Diffusers training recipe plans without launching training.

This helper is self-contained: it does not assume the original Diffusers
repository examples are present. It validates common recipe choices and emits a
copyable plan of arguments a future agent can map onto a user-provided training
entrypoint or a maintained project-local script.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


RECIPES = {
    "dreambooth-lora": {
        "entrypoint_hint": "DreamBooth LoRA training entrypoint for SD 1.x/2.x",
        "dataset_arg": "--instance_data_dir",
        "requires_instance_prompt": True,
        "defaults": ["--resolution", "512", "--train_batch_size", "1", "--gradient_accumulation_steps", "4", "--learning_rate", "1e-4", "--checkpointing_steps", "500"],
    },
    "dreambooth-lora-sdxl": {
        "entrypoint_hint": "DreamBooth LoRA training entrypoint for SDXL",
        "dataset_arg": "--instance_data_dir",
        "requires_instance_prompt": True,
        "defaults": ["--resolution", "1024", "--train_batch_size", "1", "--gradient_accumulation_steps", "4", "--learning_rate", "1e-4", "--checkpointing_steps", "500", "--gradient_checkpointing"],
        "expensive": True,
    },
    "dreambooth-lora-flux": {
        "entrypoint_hint": "DreamBooth LoRA training entrypoint for Flux",
        "dataset_arg": "--instance_data_dir",
        "requires_instance_prompt": True,
        "defaults": ["--resolution", "512", "--train_batch_size", "1", "--gradient_accumulation_steps", "8", "--learning_rate", "1e-4", "--checkpointing_steps", "500", "--gradient_checkpointing"],
        "expensive": True,
    },
    "text-to-image": {
        "entrypoint_hint": "Text-to-image fine-tuning entrypoint",
        "dataset_arg": "--train_data_dir",
        "defaults": ["--resolution", "512", "--train_batch_size", "1", "--gradient_accumulation_steps", "4", "--learning_rate", "1e-5", "--checkpointing_steps", "500"],
    },
    "text-to-image-lora": {
        "entrypoint_hint": "Text-to-image LoRA fine-tuning entrypoint",
        "dataset_arg": "--train_data_dir",
        "defaults": ["--resolution", "512", "--train_batch_size", "1", "--gradient_accumulation_steps", "4", "--learning_rate", "1e-4", "--rank", "4", "--checkpointing_steps", "500"],
    },
    "text-to-image-sdxl": {
        "entrypoint_hint": "SDXL text-to-image fine-tuning entrypoint",
        "dataset_arg": "--train_data_dir",
        "defaults": ["--resolution", "1024", "--train_batch_size", "1", "--gradient_accumulation_steps", "4", "--learning_rate", "1e-6", "--checkpointing_steps", "500", "--gradient_checkpointing"],
        "expensive": True,
    },
    "textual-inversion": {
        "entrypoint_hint": "Textual inversion training entrypoint",
        "dataset_arg": "--train_data_dir",
        "requires_placeholder": True,
        "defaults": ["--resolution", "512", "--train_batch_size", "1", "--gradient_accumulation_steps", "4", "--learning_rate", "5e-4", "--max_train_steps", "3000"],
    },
    "controlnet": {
        "entrypoint_hint": "ControlNet training entrypoint",
        "dataset_arg": "--dataset_name",
        "control_columns": True,
        "defaults": ["--resolution", "512", "--train_batch_size", "1", "--gradient_accumulation_steps", "4", "--learning_rate", "1e-5", "--checkpointing_steps", "500", "--gradient_checkpointing"],
        "expensive": True,
    },
    "controlnet-sdxl": {
        "entrypoint_hint": "SDXL ControlNet training entrypoint",
        "dataset_arg": "--dataset_name",
        "control_columns": True,
        "defaults": ["--resolution", "1024", "--train_batch_size", "1", "--gradient_accumulation_steps", "4", "--learning_rate", "1e-5", "--checkpointing_steps", "500", "--gradient_checkpointing"],
        "expensive": True,
    },
    "controlnet-sd3": {
        "entrypoint_hint": "SD3 ControlNet training entrypoint",
        "dataset_arg": "--dataset_name",
        "control_columns": True,
        "defaults": ["--resolution", "512", "--train_batch_size", "1", "--gradient_accumulation_steps", "8", "--learning_rate", "1e-5", "--checkpointing_steps", "500", "--gradient_checkpointing"],
        "expensive": True,
    },
    "controlnet-flux": {
        "entrypoint_hint": "Flux ControlNet training entrypoint",
        "dataset_arg": "--dataset_name",
        "control_columns": True,
        "defaults": ["--resolution", "512", "--train_batch_size", "1", "--gradient_accumulation_steps", "16", "--learning_rate", "1e-5", "--checkpointing_steps", "500", "--gradient_checkpointing"],
        "expensive": True,
    },
    "t2i-adapter-sdxl": {
        "entrypoint_hint": "SDXL T2I-Adapter training entrypoint",
        "dataset_arg": "--dataset_name",
        "control_columns": True,
        "defaults": ["--resolution", "1024", "--train_batch_size", "1", "--gradient_accumulation_steps", "4", "--learning_rate", "1e-5", "--checkpointing_steps", "500", "--gradient_checkpointing"],
        "expensive": True,
    },
    "instruct-pix2pix": {
        "entrypoint_hint": "InstructPix2Pix training entrypoint",
        "dataset_arg": "--dataset_name",
        "edit_columns": True,
        "defaults": ["--resolution", "256", "--train_batch_size", "1", "--gradient_accumulation_steps", "4", "--learning_rate", "1e-5", "--checkpointing_steps", "500"],
    },
    "flux-control-lora": {
        "entrypoint_hint": "Flux control LoRA training entrypoint",
        "dataset_arg": "--dataset_name",
        "control_columns": True,
        "defaults": ["--resolution", "512", "--train_batch_size", "1", "--gradient_accumulation_steps", "16", "--learning_rate", "1e-4", "--checkpointing_steps", "500", "--gradient_checkpointing"],
        "expensive": True,
    },
}


def shell_join(parts: list[str]) -> str:
    return " \\\n  ".join(shlex.quote(part) for part in parts)


def existing_nonempty_dir(path_text: str) -> bool:
    path = Path(path_text)
    return path.exists() and path.is_dir() and any(path.iterdir())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", required=True, choices=sorted(RECIPES), help="Training recipe template to emit.")
    parser.add_argument("--model", required=True, help="Model id or local model path for --pretrained_model_name_or_path.")
    parser.add_argument("--dataset", required=True, help="Local dataset path or Hub dataset id.")
    parser.add_argument("--output-dir", required=True, help="Directory where checkpoints/model artifacts should be written.")
    parser.add_argument("--entrypoint", default="<user-training-entrypoint.py>", help="User-provided training script/module to place in the skeleton.")
    parser.add_argument("--instance-prompt", help="DreamBooth instance prompt, such as 'a photo of sks dog'.")
    parser.add_argument("--placeholder-token", help="Textual inversion placeholder token, such as '<sks-style>'.")
    parser.add_argument("--initializer-token", help="Textual inversion initializer token, such as 'dog' or 'style'.")
    parser.add_argument("--caption-column", default="text", help="Caption/text column for dataset-backed recipes.")
    parser.add_argument("--image-column", default="image", help="Image column for dataset-backed recipes.")
    parser.add_argument("--conditioning-image-column", default="conditioning_image", help="Conditioning image column for control recipes.")
    parser.add_argument("--original-image-column", default="original_image", help="Original image column for InstructPix2Pix.")
    parser.add_argument("--edited-image-column", default="edited_image", help="Edited image column for InstructPix2Pix.")
    parser.add_argument("--edit-prompt-column", default="edit_prompt", help="Edit prompt column for InstructPix2Pix.")
    parser.add_argument("--mixed-precision", choices=["no", "fp16", "bf16"], default="fp16", help="Accelerate mixed precision launcher value.")
    parser.add_argument("--max-train-steps", type=int, default=1000, help="Training step cap to include unless recipe has a fixed default.")
    parser.add_argument("--extra-arg", action="append", default=[], help="Additional script argument; repeat for each complete token, e.g. --extra-arg=--center_crop.")
    parser.add_argument("--confirm-expensive-run", action="store_true", help="Allow templates marked as high-memory/expensive and non-empty output dirs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    recipe = RECIPES[args.recipe]

    if recipe.get("expensive") and not args.confirm_expensive_run:
        print(f"Refusing to emit {args.recipe!r} without --confirm-expensive-run because this recipe is high-memory or expensive.", file=sys.stderr)
        return 2
    if existing_nonempty_dir(args.output_dir) and not args.confirm_expensive_run:
        print("Refusing to target a non-empty --output-dir without --confirm-expensive-run.", file=sys.stderr)
        return 2
    if recipe.get("requires_instance_prompt") and not args.instance_prompt:
        print("This recipe requires --instance-prompt.", file=sys.stderr)
        return 2
    if recipe.get("requires_placeholder") and (not args.placeholder_token or not args.initializer_token):
        print("This recipe requires --placeholder-token and --initializer-token.", file=sys.stderr)
        return 2

    command = ["accelerate", "launch"]
    if args.mixed_precision != "no":
        command.append(f"--mixed_precision={args.mixed_precision}")
    command.append(args.entrypoint)
    command.extend(["--pretrained_model_name_or_path", args.model, recipe["dataset_arg"], args.dataset, "--output_dir", args.output_dir])

    if args.instance_prompt:
        command.extend(["--instance_prompt", args.instance_prompt])
    if args.placeholder_token:
        command.extend(["--placeholder_token", args.placeholder_token])
    if args.initializer_token:
        command.extend(["--initializer_token", args.initializer_token])
    if recipe.get("control_columns"):
        command.extend(["--image_column", args.image_column, "--caption_column", args.caption_column, "--conditioning_image_column", args.conditioning_image_column])
    elif recipe.get("edit_columns"):
        command.extend(["--original_image_column", args.original_image_column, "--edited_image_column", args.edited_image_column, "--edit_prompt_column", args.edit_prompt_column])
    elif recipe["dataset_arg"] in {"--train_data_dir", "--dataset_name"} and not recipe.get("requires_instance_prompt") and not recipe.get("requires_placeholder"):
        command.extend(["--caption_column", args.caption_column])

    command.extend(recipe["defaults"])
    if "--max_train_steps" not in recipe["defaults"]:
        command.extend(["--max_train_steps", str(args.max_train_steps)])
    command.extend(args.extra_arg)

    print("# Self-contained plan: replace <user-training-entrypoint.py> with a script the user owns or has explicitly provided.")
    print(f"# Recipe intent: {recipe['entrypoint_hint']}")
    print("# Review hardware, model access, dataset columns, output path, and logging/Hugging Face Hub side effects before running.")
    print(shell_join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
