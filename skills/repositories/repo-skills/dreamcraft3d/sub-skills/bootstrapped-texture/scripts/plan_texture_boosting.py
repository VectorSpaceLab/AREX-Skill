#!/usr/bin/env python3
"""Plan DreamCraft3D optional texture boosting without running models."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


def exists_state(path: Path) -> Dict[str, Any]:
    return {"path": str(path), "exists": path.exists(), "is_dir": path.is_dir(), "is_file": path.is_file()}


def plan(args: argparse.Namespace) -> Dict[str, Any]:
    image = Path(args.image_path)
    instance_dir = Path(args.instance_dir)
    lora_output = Path(args.lora_output_dir)
    model_cache = Path(args.model_cache) if args.model_cache else None

    warnings: List[str] = []
    problems: List[str] = []
    if not args.prompt.strip():
        problems.append("--prompt must be non-empty")
    if not image.exists():
        warnings.append(f"image path does not currently exist: {image}")
    if image.name.endswith("_rgba.png") is False:
        warnings.append("DreamCraft3D usually feeds *_rgba.png into stages; confirm this image is already preprocessed.")
    if not instance_dir.exists():
        warnings.append("instance/multiview directory is absent; Zero123++ generation would need to create and populate it.")
    else:
        jpgs = sorted(p.name for p in instance_dir.glob("*.jpg")) + sorted(p.name for p in instance_dir.glob("*.png"))
        if len(jpgs) < 6:
            warnings.append(f"instance directory has {len(jpgs)} image-like files; inspect whether it contains a complete 2x3 multiview set.")
    if lora_output.exists() and not lora_output.is_dir():
        problems.append("--lora-output-dir exists but is not a directory")
    if args.source_helper_uses_cuda1:
        warnings.append("source img_to_mv.py uses cuda:1; adapt device selection if only one GPU is visible or scheduler remaps devices.")
    if model_cache is not None and not model_cache.exists():
        warnings.append(f"model cache path does not exist: {model_cache}; source helper uses local_files_only=True.")

    multiview_cmd = [
        "python", "threestudio/scripts/img_to_mv.py",
        "--image_path", str(image),
        "--save_path", str(instance_dir),
        "--prompt", args.prompt,
    ]
    if args.superres:
        multiview_cmd.append("--superres")

    dreambooth_cmd = [
        "accelerate", "launch", "threestudio/scripts/train_dreambooth_lora.py",
        f"--pretrained_model_name_or_path={args.model_name}",
        f"--instance_data_dir={instance_dir}",
        f"--output_dir={lora_output}",
        f"--instance_prompt={args.instance_prompt or ('a sks ' + args.prompt)}",
        "--resolution=64",
        f"--train_batch_size={args.train_batch_size}",
        "--gradient_accumulation_steps=1",
        f"--learning_rate={args.learning_rate}",
        "--scale_lr",
        f"--max_train_steps={args.max_train_steps}",
        f"--checkpointing_steps={args.checkpointing_steps}",
        "--pre_compute_text_embeddings",
        "--tokenizer_max_length=77",
        "--text_encoder_use_attention_mask",
    ]

    lora_override = f"system.guidance.lora_weights_path={lora_output}"
    return {
        "status": "fail" if problems else "warn" if warnings else "ok",
        "inputs": {
            "image_path": str(image),
            "prompt": args.prompt,
            "instance_dir": str(instance_dir),
            "lora_output_dir": str(lora_output),
            "model_name": args.model_name,
            "model_cache": str(model_cache) if model_cache else None,
        },
        "checks": {
            "image": exists_state(image),
            "instance_dir": exists_state(instance_dir),
            "lora_output_dir": exists_state(lora_output),
            "model_cache": exists_state(model_cache) if model_cache else {"path": None, "exists": None},
        },
        "suggested_commands": {
            "zero123plus_multiview": multiview_cmd,
            "dreambooth_lora": dreambooth_cmd,
            "launch_override_after_lora": lora_override,
        },
        "problems": problems,
        "warnings": warnings,
        "notes": [
            "This planner does not download models, generate multiview images, or train LoRA.",
            "Inspect generated multiview images before DreamBooth training.",
            "Only run the suggested commands after approving GPU time, model cache/downloads, and output locations.",
        ],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Plan DreamCraft3D texture boosting without running expensive steps.")
    parser.add_argument("--image-path", required=True, help="Reference image, usually a *_rgba.png file.")
    parser.add_argument("--prompt", required=True, help="Prompt used for super-resolution and instance prompt planning.")
    parser.add_argument("--instance-dir", required=True, help="Directory for Zero123++ multiview images / DreamBooth instance data.")
    parser.add_argument("--lora-output-dir", required=True, help="Directory where DreamBooth LoRA output should be written.")
    parser.add_argument("--model-name", default="DeepFloyd/IF-I-XL-v1.0", help="Base model for DreamBooth LoRA.")
    parser.add_argument("--model-cache", default="load/checkpoints/huggingface/hub", help="Local cache hint used by the source Zero123++ helper.")
    parser.add_argument("--instance-prompt", default=None, help="Override instance prompt; default is 'a sks <prompt>'.")
    parser.add_argument("--superres", action="store_true", help="Include the optional x4 upscaler flag in the planned multiview command.")
    parser.add_argument("--train-batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", default="5e-6")
    parser.add_argument("--max-train-steps", type=int, default=1200)
    parser.add_argument("--checkpointing-steps", type=int, default=600)
    parser.add_argument("--source-helper-uses-cuda1", action="store_true", default=True, help="Warn about source img_to_mv.py hard-coded cuda:1 behavior.")
    parser.add_argument("--json", action="store_true", help="Print JSON.")
    args = parser.parse_args(argv)

    report = plan(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        for problem in report["problems"]:
            print(f"problem: {problem}")
        for warning in report["warnings"]:
            print(f"warning: {warning}")
        print("\nSuggested Zero123++ command:")
        print(" ".join(report["suggested_commands"]["zero123plus_multiview"]))
        print("\nSuggested DreamBooth LoRA command:")
        print(" ".join(report["suggested_commands"]["dreambooth_lora"]))
        print("\nLaunch override after LoRA:")
        print(report["suggested_commands"]["launch_override_after_lora"])
    return 0 if report["status"] in ("ok", "warn") else 2


if __name__ == "__main__":
    raise SystemExit(main())
