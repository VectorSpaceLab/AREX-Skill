#!/usr/bin/env python3
"""Print safe InternImage classification command templates.

This helper is intentionally standalone: it imports only Python standard-library
modules and never imports the InternImage repository. It prints commands for a
user to inspect, edit, and run in their own checkout.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List


DEFAULT_REPO_PLACEHOLDER = "CHANGE_ME/InternImage"
DEFAULT_DATA_PLACEHOLDER = "CHANGE_ME/imagenet"
DEFAULT_CHECKPOINT_PLACEHOLDER = "CHANGE_ME/checkpoint.pth"
DEFAULT_IMAGE_PLACEHOLDER = "CHANGE_ME/image.png"


def q(value: object) -> str:
    """Shell-quote one token."""
    return shlex.quote(str(value))


def split_cfg_option(option: str) -> List[str]:
    if "=" not in option:
        raise argparse.ArgumentTypeError(
            "configuration overrides must use KEY=VALUE form, e.g. TRAIN.EPOCHS=1"
        )
    key, value = option.split("=", 1)
    if not key.strip():
        raise argparse.ArgumentTypeError("configuration override key cannot be empty")
    return [key.strip(), value]


def add_common_main_args(cmd: List[str], args: argparse.Namespace, *, include_resume: bool) -> None:
    cmd.extend(["--cfg", args.config, "--data-path", args.data_path])
    if args.dataset != "auto":
        cmd.extend(["--dataset", args.dataset])
    if args.batch_size is not None:
        cmd.extend(["--batch-size", str(args.batch_size)])
    if args.zip:
        cmd.append("--zip")
    if args.cache_mode is not None:
        cmd.extend(["--cache-mode", args.cache_mode])
    if args.output:
        cmd.extend(["--output", args.output])
    if args.tag:
        cmd.extend(["--tag", args.tag])
    if args.pretrained:
        cmd.extend(["--pretrained", args.pretrained])
    if include_resume and args.resume:
        cmd.extend(["--resume", args.resume])
    if args.accumulation_steps is not None:
        cmd.extend(["--accumulation-steps", str(args.accumulation_steps)])
    if args.save_ckpt_num is not None:
        cmd.extend(["--save-ckpt-num", str(args.save_ckpt_num)])
    for pair in args.cfg_option:
        cmd.extend(["--opts", *pair] if "--opts" not in cmd else pair)
    for extra in args.extra_arg:
        cmd.append(extra)


def add_main_only_args(cmd: List[str], args: argparse.Namespace) -> None:
    if args.use_checkpoint:
        cmd.append("--use-checkpoint")
    if args.amp_opt_level:
        cmd.extend(["--amp-opt-level", args.amp_opt_level])
    if args.use_zero:
        cmd.append("--use-zero")


def launcher_prefix(args: argparse.Namespace, script_name: str) -> List[str]:
    if args.launcher == "launch":
        return [
            "python",
            "-m",
            "torch.distributed.launch",
            "--nproc_per_node",
            str(args.gpus),
            "--master_port",
            str(args.master_port),
            script_name,
        ]
    if args.launcher == "srun":
        cmd = [
            "srun",
            "-p",
            args.partition,
            f"--job-name={args.job_name}",
            f"--gres=gpu:{args.gpus_per_node}",
            f"--ntasks={args.gpus}",
            f"--ntasks-per-node={args.gpus_per_node}",
            f"--cpus-per-task={args.cpus_per_task}",
            "--kill-on-bad-exit=1",
        ]
        cmd.extend(args.srun_arg)
        cmd.extend(["python", "-u", script_name, "--local-rank", "0"])
        return cmd
    raise AssertionError(f"unsupported launcher: {args.launcher}")


def shell_template(command: Iterable[str], *, needs_checkout: bool = True) -> str:
    lines: List[str] = []
    if needs_checkout:
        lines.extend(
            [
                "# Fill in INTERNIMAGE_REPO before running; this helper only prints templates.",
                f'export INTERNIMAGE_REPO="${{INTERNIMAGE_REPO:-{DEFAULT_REPO_PLACEHOLDER}}}"',
                'cd "$INTERNIMAGE_REPO/classification"',
                'export PYTHONPATH="$INTERNIMAGE_REPO/classification:$INTERNIMAGE_REPO:${PYTHONPATH:-}"',
            ]
        )
    lines.append(" ".join(q(token) for token in command))
    return "\n".join(lines)


def build_eval_or_train(args: argparse.Namespace, *, mode: str) -> str:
    cmd = launcher_prefix(args, "main.py")
    include_resume = bool(args.resume)
    add_common_main_args(cmd, args, include_resume=include_resume)
    add_main_only_args(cmd, args)
    if mode == "eval":
        if "--resume" not in cmd:
            cmd.extend(["--resume", args.checkpoint])
        cmd.append("--eval")
    elif mode == "throughput":
        if "--resume" not in cmd:
            cmd.extend(["--resume", args.checkpoint])
        cmd.append("--throughput")
    elif mode != "train":
        raise AssertionError(mode)
    return shell_template(cmd)


def build_deepspeed(args: argparse.Namespace) -> str:
    cmd = launcher_prefix(args, "main_deepspeed.py")
    include_resume = bool(args.resume or args.eval)
    if args.eval and not args.resume:
        args.resume = args.checkpoint
    add_common_main_args(cmd, args, include_resume=include_resume)
    if args.eval:
        cmd.append("--eval")
    if args.throughput:
        cmd.append("--throughput")
    if args.disable_grad_scalar:
        cmd.append("--disable-grad-scalar")
    cmd.extend(["--offload-optimizer", args.offload_optimizer])
    cmd.extend(["--offload-param", args.offload_param])
    cmd.extend(["--zero-stage", str(args.zero_stage)])
    return shell_template(cmd)


def build_accelerate(args: argparse.Namespace) -> str:
    cmd = [
        "accelerate",
        "launch",
        "--config_file",
        args.accelerate_config,
        "main_accelerate.py",
        "--cfg",
        args.config,
        "--data-path",
        args.data_path,
    ]
    if args.dataset != "auto":
        cmd.extend(["--dataset", args.dataset])
    if args.batch_size is not None:
        cmd.extend(["--batch-size", str(args.batch_size)])
    if args.zip:
        cmd.append("--zip")
    if args.cache_mode is not None:
        cmd.extend(["--cache-mode", args.cache_mode])
    if args.pretrained:
        cmd.extend(["--pretrained", args.pretrained])
    if args.resume:
        cmd.extend(["--resume", args.resume])
    elif args.eval:
        cmd.extend(["--resume", args.checkpoint])
    if args.output:
        cmd.extend(["--output", args.output])
    if args.accumulation_steps is not None:
        cmd.extend(["--accumulation-steps", str(args.accumulation_steps)])
    if args.eval:
        cmd.append("--eval")
    if args.throughput:
        cmd.append("--throughput")
    if args.disable_grad_scalar:
        cmd.append("--disable-grad-scalar")
    if args.logger:
        cmd.extend(["--logger", args.logger])
    for pair in args.cfg_option:
        cmd.extend(["--opts", *pair] if "--opts" not in cmd else pair)
    for extra in args.extra_arg:
        cmd.append(extra)
    return shell_template(cmd)


def build_extract_features(args: argparse.Namespace) -> str:
    keys = args.keys or ["patch_embed", "levels.0.downsample"]
    cmd = [
        "python",
        "extract_feature.py",
        "--cfg",
        args.config,
        "--img",
        args.image,
        "--keys",
        *keys,
        "--resume",
        args.checkpoint,
    ]
    if args.save_features:
        cmd.append("--save")
    return shell_template(cmd)


def build_hf_transformers(args: argparse.Namespace) -> str:
    task = args.hf_task
    lines = [
        "# Standalone Transformers template; no InternImage checkout import is used.",
        "python - <<'PY'",
        "import torch",
        "from PIL import Image",
        "from transformers import AutoModel, AutoModelForImageClassification, CLIPImageProcessor",
        f"model_name = {args.hf_model!r}",
        f"image_path = {args.image!r}",
        "device = 'cuda' if torch.cuda.is_available() else 'cpu'",
        "image = Image.open(image_path).convert('RGB')",
        "processor = CLIPImageProcessor.from_pretrained(model_name)",
        "pixel_values = processor(images=image, return_tensors='pt').pixel_values.to(device)",
    ]
    if task in {"backbone", "both"}:
        lines.extend(
            [
                "backbone = AutoModel.from_pretrained(model_name, trust_remote_code=True).to(device).eval()",
                "with torch.no_grad():",
                "    hidden_states = backbone(pixel_values).hidden_states",
                "print('hidden_states:', [tuple(x.shape) for x in hidden_states])",
            ]
        )
    if task in {"classify", "both"}:
        lines.extend(
            [
                "classifier = AutoModelForImageClassification.from_pretrained(model_name, trust_remote_code=True).to(device).eval()",
                "with torch.no_grad():",
                "    logits = classifier(pixel_values).logits",
                "label_id = int(torch.argmax(logits, dim=1))",
                "print('logits:', tuple(logits.shape), 'label_id:', label_id)",
            ]
        )
    lines.append("PY")
    return "\n".join(lines)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print standalone command templates for InternImage classification "
            "workflows without importing the original repository."
        )
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=[
            "eval",
            "train",
            "throughput",
            "deepspeed",
            "accelerate",
            "extract-features",
            "hf-transformers",
        ],
        help="Workflow command template to print.",
    )
    parser.add_argument("--config", default="configs/internimage_b_1k_224.yaml", help="Classification config label/path inside the classification tree.")
    parser.add_argument("--data-path", default=DEFAULT_DATA_PLACEHOLDER, help="Dataset root placeholder or path for --data-path.")
    parser.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT_PLACEHOLDER, help="Checkpoint path used by eval, throughput, feature extraction, or eval-style DeepSpeed/Accelerate.")
    parser.add_argument("--pretrained", default="", help="Pretrained checkpoint for training initialization.")
    parser.add_argument("--resume", default="", help="Checkpoint or checkpoint directory for resume; overrides --checkpoint when supplied.")
    parser.add_argument("--dataset", default="auto", help="Optional dataset override: auto, imagenet, imagenet22K, inat18, or a custom value supported by the user's code.")
    parser.add_argument("--batch-size", type=int, default=None, help="Per-GPU batch size override.")
    parser.add_argument("--gpus", type=int, default=1, help="Total GPU/process count for launch or Slurm templates.")
    parser.add_argument("--master-port", type=int, default=12345, help="Master port for torch.distributed.launch templates.")
    parser.add_argument("--launcher", choices=["launch", "srun"], default="launch", help="Distributed launcher shape for main.py/main_deepspeed.py modes.")
    parser.add_argument("--output", default="output", help="Output root; source appends the config-derived model name.")
    parser.add_argument("--tag", default="", help="Experiment tag stored in config but not appended to output path by source code.")
    parser.add_argument("--zip", action="store_true", help="Append --zip for zipped ImageNet-style data.")
    parser.add_argument("--cache-mode", choices=["no", "full", "part"], default=None, help="Optional cache mode override.")
    parser.add_argument("--accumulation-steps", type=int, default=None, help="Gradient accumulation steps.")
    parser.add_argument("--save-ckpt-num", type=int, default=None, help="Number of checkpoints to keep when supported by the source parser.")
    parser.add_argument("--cfg-option", action="append", type=split_cfg_option, default=[], metavar="KEY=VALUE", help="YACS override converted to --opts KEY VALUE. Repeatable.")
    parser.add_argument("--extra-arg", action="append", default=[], help="Append one extra raw CLI token to the generated source command. Repeatable; use --extra-arg=--flag when the token begins with '-'.")

    parser.add_argument("--use-checkpoint", action="store_true", help="Append --use-checkpoint for main.py training/eval templates.")
    parser.add_argument("--amp-opt-level", default="", choices=["", "O0", "O1", "O2"], help="AMP opt level for main.py templates.")
    parser.add_argument("--use-zero", action="store_true", help="Append --use-zero for main.py ZeroRedundancyOptimizer experiments.")

    parser.add_argument("--partition", default="CHANGE_ME_PARTITION", help="Slurm partition placeholder for --launcher srun.")
    parser.add_argument("--job-name", default="internimage_classification", help="Slurm job name for --launcher srun.")
    parser.add_argument("--gpus-per-node", type=int, default=1, help="Slurm GPUs per node.")
    parser.add_argument("--cpus-per-task", type=int, default=12, help="Slurm CPUs per task.")
    parser.add_argument("--srun-arg", action="append", default=[], help="Append one approved site-specific srun argument. Repeatable; use --srun-arg=--flag when the token begins with '-'.")

    parser.add_argument("--eval", action="store_true", help="For deepspeed/accelerate modes, append --eval and use --checkpoint when --resume is absent.")
    parser.add_argument("--throughput", action="store_true", help="For deepspeed/accelerate modes, append --throughput.")
    parser.add_argument("--disable-grad-scalar", action="store_true", help="Append --disable-grad-scalar for DeepSpeed/Accelerate templates.")
    parser.add_argument("--offload-optimizer", choices=["cpu", "none"], default="none", help="DeepSpeed optimizer offload device for main_deepspeed.py templates.")
    parser.add_argument("--offload-param", choices=["cpu", "none"], default="none", help="DeepSpeed parameter offload device for main_deepspeed.py templates.")
    parser.add_argument("--zero-stage", type=int, choices=[1, 2], default=1, help="Plain main_deepspeed.py source parser supports only stages 1 or 2.")
    parser.add_argument("--accelerate-config", default="configs/accelerate/dist_8gpus_zero3_offload.yaml", help="Accelerate YAML config label/path.")
    parser.add_argument("--logger", choices=["", "tensorboard", "wandb"], default="", help="Logger for main_accelerate.py.")

    parser.add_argument("--image", default=DEFAULT_IMAGE_PLACEHOLDER, help="Image path for feature extraction or Transformers template.")
    parser.add_argument("--keys", nargs="*", default=None, help="Feature-extraction module keys after --mode extract-features.")
    parser.add_argument("--save-features", action="store_true", help="Append --save for extract_feature.py; source derives the output filename from the image path.")

    parser.add_argument("--hf-model", default="OpenGVLab/internimage_t_1k_224", help="Hugging Face model ID or local model directory.")
    parser.add_argument("--hf-task", choices=["backbone", "classify", "both"], default="classify", help="Transformers template task.")
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    if args.gpus < 1:
        parser.error("--gpus must be >= 1")
    if args.gpus_per_node < 1:
        parser.error("--gpus-per-node must be >= 1")
    if args.cpus_per_task < 1:
        parser.error("--cpus-per-task must be >= 1")

    if args.mode in {"eval", "train", "throughput"}:
        text = build_eval_or_train(args, mode=args.mode)
    elif args.mode == "deepspeed":
        text = build_deepspeed(args)
    elif args.mode == "accelerate":
        text = build_accelerate(args)
    elif args.mode == "extract-features":
        text = build_extract_features(args)
    elif args.mode == "hf-transformers":
        text = build_hf_transformers(args)
    else:
        parser.error(f"unsupported mode: {args.mode}")
        return 2

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
