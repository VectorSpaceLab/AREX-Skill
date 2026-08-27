#!/usr/bin/env python3
"""Build an InternVideo2 single-modality command skeleton without running it."""
from __future__ import annotations

import argparse
import shlex

WORKFLOW_ENTRY = {
    "pretrain": "run_pretraining.py",
    "finetune": "run_finetuning.py",
    "linear-probe": "run_linear_probing.py",
    "distill": "run_distill.py",
}
DATASET_DEFAULTS = {
    "k400": {"data_set": "Kinetics_sparse", "classes": 400},
    "k600": {"data_set": "Kinetics_sparse", "classes": 600},
    "k700": {"data_set": "Kinetics_sparse", "classes": 700},
    "k710": {"data_set": "Kinetics_sparse", "classes": 710},
    "ssv2": {"data_set": "SSV2", "classes": 174},
    "hmdb51": {"data_set": "HMDB51", "classes": 51},
    "ucf101": {"data_set": "UCF101", "classes": 101},
}


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(p)) for p in parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a safe InternVideo2 single-modality launch skeleton.")
    parser.add_argument("--workflow", choices=sorted(WORKFLOW_ENTRY), required=True)
    parser.add_argument("--dataset", default="k400", help="Dataset key such as k400, k600, k700, k710, ssv2, hmdb51, ucf101.")
    parser.add_argument("--model", default="1B", help="Model family: 1B, 6B, S14, B14, L14, or full model constructor name.")
    parser.add_argument("--data-root", default="${INTERNVIDEO2_DATA_PATH}")
    parser.add_argument("--model-root", default="${INTERNVIDEO2_MODEL_PATH}")
    parser.add_argument("--checkpoint", help="Explicit checkpoint path; otherwise a placeholder under model-root is shown.")
    parser.add_argument("--partition", default="video")
    parser.add_argument("--gpus", type=int, default=8)
    parser.add_argument("--gpus-per-node", type=int, default=8)
    parser.add_argument("--cpus-per-task", type=int, default=16)
    parser.add_argument("--eval-only", action="store_true")
    args = parser.parse_args()

    ds = DATASET_DEFAULTS.get(args.dataset.lower(), {"data_set": args.dataset, "classes": "<classes>"})
    entry = WORKFLOW_ENTRY[args.workflow]
    checkpoint = args.checkpoint or f"{args.model_root}/<checkpoint-for-{args.model}-{args.dataset}>.pth"
    model_name = args.model if "internvideo" in args.model.lower() else f"internvideo2_{args.model}_patch14_224"

    print("# Run from the InternVideo2/single_modality directory of a checkout with dependencies installed.")
    print("export MASTER_PORT=$((12000 + $RANDOM % 20000))")
    print("export OMP_NUM_THREADS=1")
    print(f"export INTERNVIDEO2_DATA_PATH={shlex.quote(args.data_root)}")
    print(f"export INTERNVIDEO2_MODEL_PATH={shlex.quote(args.model_root)}")
    cmd = [
        "srun", "-p", args.partition,
        f"--gres=gpu:{args.gpus_per_node}",
        f"--ntasks={args.gpus}",
        f"--ntasks-per-node={args.gpus_per_node}",
        f"--cpus-per-task={args.cpus_per_task}",
        "python", entry,
    ]
    if args.workflow == "pretrain":
        cmd += ["--data_path", f"{args.data_root}/<train-list>.csv", "--model", f"pretrain_{model_name}", "--enable_deepspeed", "--bf16"]
    elif args.workflow == "distill":
        cmd += ["--data_path", f"{args.data_root}/<train-list>.csv", "--model", model_name, "--finetune", checkpoint, "--enable_deepspeed", "--bf16"]
    else:
        cmd += [
            "--model", model_name,
            "--data_path", f"{args.data_root}/{args.dataset}",
            "--prefix", f"{args.data_root}/{args.dataset}",
            "--data_set", str(ds["data_set"]),
            "--nb_classes", str(ds["classes"]),
            "--finetune", checkpoint,
            "--test_num_segment", "4",
            "--test_num_crop", "3",
            "--enable_deepspeed",
            "--bf16",
        ]
        if args.eval_only:
            cmd.append("--eval")
    print(shell_join(cmd))
    print("# Review dataset class count, checkpoint family, GPU count, batch size, and crop/segment strategy before execution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
