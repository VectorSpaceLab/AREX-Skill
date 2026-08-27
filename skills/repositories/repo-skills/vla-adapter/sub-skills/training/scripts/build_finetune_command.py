#!/usr/bin/env python3
"""Render a safe VLA-Adapter fine-tuning command.

This helper never launches training. It only prints a benchmark-aware
``torchrun`` command for ``vla-scripts/finetune.py`` and, when requested, a
small environment block for offline W&B logging.
"""

from __future__ import annotations

import argparse
import os
import shlex
from dataclasses import dataclass
from typing import Dict, List

DEFAULT_VLM_PATH = "pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b"
DEFAULT_CONFIG_FILE_PATH = "pretrained_models/configs"
DEFAULT_WANDB_ENTITY = "your-wandb-entity"
DEFAULT_WANDB_PROJECT = "your-wandb-project"


@dataclass(frozen=True)
class BenchmarkDefaults:
    dataset_name: str
    data_root_dir: str
    num_images_in_input: int
    default_gpus: int
    use_proprio: bool
    save_freq: int
    lr_warmup_steps: float
    batch_size: int
    grad_accumulation_steps: int
    num_steps_before_decay: int
    max_steps: int
    wandb_project: str
    offline_wandb: bool


PROFILE_SCHEDULES: Dict[str, Dict[str, int]] = {
    "tiny": {
        "batch_size": 1,
        "grad_accumulation_steps": 8,
        "num_steps_before_decay": 400000,
        "max_steps": 400005,
    },
    "low": {
        "batch_size": 4,
        "grad_accumulation_steps": 4,
        "num_steps_before_decay": 200000,
        "max_steps": 200005,
    },
    "medium": {
        "batch_size": 8,
        "grad_accumulation_steps": 2,
        "num_steps_before_decay": 200000,
        "max_steps": 200005,
    },
    "large": {
        "batch_size": 16,
        "grad_accumulation_steps": 1,
        "num_steps_before_decay": 150000,
        "max_steps": 150005,
    },
}

BENCHMARK_DEFAULTS: Dict[str, BenchmarkDefaults] = {
    "libero": BenchmarkDefaults(
        dataset_name="libero_spatial_no_noops",
        data_root_dir="data/libero",
        num_images_in_input=2,
        default_gpus=1,
        use_proprio=True,
        save_freq=5000,
        lr_warmup_steps=0.1,
        batch_size=1,
        grad_accumulation_steps=8,
        num_steps_before_decay=400000,
        max_steps=400005,
        wandb_project="",
        offline_wandb=False,
    ),
    "calvin": BenchmarkDefaults(
        dataset_name="calvin_abc",
        data_root_dir="data",
        num_images_in_input=2,
        default_gpus=1,
        use_proprio=True,
        save_freq=5000,
        lr_warmup_steps=0.1,
        batch_size=1,
        grad_accumulation_steps=8,
        num_steps_before_decay=400000,
        max_steps=400005,
        wandb_project="",
        offline_wandb=False,
    ),
    "aloha": BenchmarkDefaults(
        dataset_name="bowl_stack_and_shelf_aloha_realworld_50",
        data_root_dir="datasets/cobot_aloha/tfds",
        num_images_in_input=3,
        default_gpus=4,
        use_proprio=True,
        save_freq=2000,
        lr_warmup_steps=0.0,
        batch_size=12,
        grad_accumulation_steps=1,
        num_steps_before_decay=5000,
        max_steps=10005,
        wandb_project="vla_adapter",
        offline_wandb=True,
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a safe VLA-Adapter fine-tuning command without executing it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", required=True, help="Absolute VLA-Adapter source checkout root; generated command runs from here.")
    parser.add_argument("--profile", choices=tuple(PROFILE_SCHEDULES.keys()), required=True, help="GPU profile.")
    parser.add_argument("--dataset-name", default=None, help="Dataset name for the selected benchmark.")
    parser.add_argument("--data-root-dir", default=None, help="Root directory that contains the dataset (relative paths resolve from --repo-root).")
    parser.add_argument("--vlm-path", default=None, help="Base VLM or local model path (relative paths resolve from --repo-root).")
    parser.add_argument("--config-file-path", default=None, help="Path to the VLM config directory (relative paths resolve from --repo-root).")
    parser.add_argument("--run-root-dir", default=None, help="Directory that will hold outputs and checkpoints (relative paths resolve from --repo-root).")
    parser.add_argument("--gpus", type=int, default=None, help="Number of GPUs to place in CUDA_VISIBLE_DEVICES.")
    parser.add_argument(
        "--benchmark",
        choices=("libero", "calvin", "aloha"),
        required=True,
        help="Benchmark family to render.",
    )
    parser.add_argument("--wandb-entity", default=None, help="W&B entity or team.")
    parser.add_argument("--wandb-project", default=None, help="W&B project name.")
    pro_group = parser.add_mutually_exclusive_group()
    pro_group.add_argument("--use-pro-version", dest="use_pro_version", action="store_true")
    pro_group.add_argument("--no-use-pro-version", dest="use_pro_version", action="store_false")
    parser.set_defaults(use_pro_version=True)
    parser.add_argument(
        "--print-env",
        action="store_true",
        help="Print the offline environment block before the command.",
    )
    return parser.parse_args()


def quote(value: object) -> str:
    return shlex.quote(str(value))


def bool_text(value: bool) -> str:
    return "True" if value else "False"


def benchmark_defaults(benchmark: str) -> BenchmarkDefaults:
    return BENCHMARK_DEFAULTS[benchmark]


def schedule_for(benchmark: str, profile: str) -> Dict[str, int]:
    if benchmark == "aloha":
        return {
            "batch_size": BENCHMARK_DEFAULTS["aloha"].batch_size,
            "grad_accumulation_steps": BENCHMARK_DEFAULTS["aloha"].grad_accumulation_steps,
            "num_steps_before_decay": BENCHMARK_DEFAULTS["aloha"].num_steps_before_decay,
            "max_steps": BENCHMARK_DEFAULTS["aloha"].max_steps,
        }
    return PROFILE_SCHEDULES[profile]


def build_flag_lines(
    benchmark: str,
    profile: str,
    dataset_name: str,
    data_root_dir: str,
    vlm_path: str,
    config_file_path: str,
    run_root_dir: str,
    repo_root: str,
    gpus: int,
    wandb_entity: str,
    wandb_project: str,
    use_pro_version: bool,
) -> List[str]:
    defaults = benchmark_defaults(benchmark)
    schedule = schedule_for(benchmark, profile)
    per_device_batch_size = schedule["batch_size"]
    grad_accumulation_steps = schedule["grad_accumulation_steps"]
    num_steps_before_decay = schedule["num_steps_before_decay"]
    max_steps = schedule["max_steps"]

    flag_values = [
        ("vlm_path", vlm_path),
        ("config_file_path", config_file_path),
        ("data_root_dir", data_root_dir),
        ("dataset_name", dataset_name),
        ("run_root_dir", run_root_dir),
        ("use_film", False),
        ("num_images_in_input", defaults.num_images_in_input),
        ("use_proprio", defaults.use_proprio),
        ("use_l1_regression", True),
        ("use_diffusion", False),
        ("num_steps_before_decay", num_steps_before_decay),
        ("max_steps", max_steps),
        ("save_freq", defaults.save_freq),
        ("save_latest_checkpoint_only", False),
        ("merge_lora_during_training", True),
        ("batch_size", per_device_batch_size),
        ("grad_accumulation_steps", grad_accumulation_steps),
        ("learning_rate", 2e-4),
        ("lora_rank", 64),
        ("use_lora", True),
        ("use_fz", False),
        ("use_minivlm", True),
        ("image_aug", True),
        ("lr_warmup_steps", defaults.lr_warmup_steps),
        ("use_pro_version", use_pro_version),
        ("wandb_entity", wandb_entity),
        ("wandb_project", wandb_project),
    ]

    lines: List[str] = []
    cuda_devices = ",".join(str(i) for i in range(gpus))
    lines.append(
        f"cd {quote(repo_root)} && CUDA_VISIBLE_DEVICES={cuda_devices} torchrun --standalone --nnodes 1 --nproc-per-node {gpus} "
        "vla-scripts/finetune.py"
    )
    for name, value in flag_values:
        rendered_value = bool_text(value) if isinstance(value, bool) else quote(value)
        lines.append(f"  --{name} {rendered_value}")
    continuation = " " + "\\"
    return [line + continuation if index < len(lines) - 1 else line for index, line in enumerate(lines)]


def main() -> None:
    args = parse_args()
    if not os.path.isabs(args.repo_root):
        raise SystemExit("--repo-root must be an absolute VLA-Adapter source checkout path")
    defaults = benchmark_defaults(args.benchmark)
    dataset_name = args.dataset_name or defaults.dataset_name
    data_root_dir = args.data_root_dir or defaults.data_root_dir
    vlm_path = args.vlm_path or DEFAULT_VLM_PATH
    config_file_path = args.config_file_path or DEFAULT_CONFIG_FILE_PATH
    run_root_dir = args.run_root_dir or (
        f"outputs/{dataset_name}" if args.benchmark == "aloha" else "outputs"
    )
    gpus = defaults.default_gpus if args.gpus is None else args.gpus
    if gpus < 1:
        raise SystemExit("--gpus must be a positive integer")
    wandb_entity = args.wandb_entity or os.environ.get("WANDB_ENTITY", DEFAULT_WANDB_ENTITY)
    wandb_project = (
        args.wandb_project
        or os.environ.get("WANDB_PROJECT")
        or (defaults.wandb_project if args.benchmark == "aloha" else dataset_name)
    )

    if defaults.offline_wandb or args.print_env:
        print("export WANDB_CONSOLE=off")
        print("export WANDB_MODE=offline")
        print("export TOKENIZERS_PARALLELISM=false")
        print()

    print(f"# benchmark={args.benchmark} profile={args.profile} gpus={gpus} repo_root={args.repo_root}")
    for line in build_flag_lines(
        benchmark=args.benchmark,
        profile=args.profile,
        dataset_name=dataset_name,
        data_root_dir=data_root_dir,
        vlm_path=vlm_path,
        config_file_path=config_file_path,
        run_root_dir=run_root_dir,
        repo_root=args.repo_root,
        gpus=gpus,
        wandb_entity=wandb_entity,
        wandb_project=wandb_project,
        use_pro_version=args.use_pro_version,
    ):
        print(line)


if __name__ == "__main__":
    main()
