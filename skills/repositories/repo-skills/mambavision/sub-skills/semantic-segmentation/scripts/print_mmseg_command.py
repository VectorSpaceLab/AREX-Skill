#!/usr/bin/env python3
"""Print safe single-GPU MambaVision MMSegmentation command templates.

This helper never launches training or evaluation. It emits command templates
with placeholder entry points and config roots by default. Replace placeholders
with concrete paths in the user's target checkout or project before running.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import PurePosixPath

CONFIG_BASENAMES = {
    "tiny": "mamba_vision_160k_ade20k-512x512_tiny.py",
    "small": "mamba_vision_160k_ade20k-512x512_small.py",
    "base": "mamba_vision_160k_ade20k-512x512_base.py",
    "l3": "mamba_vision_160k_ade20k-640x640_l3_21k.py",
}

PLACEHOLDERS = {
    "config_root": "MAMBAVISION_SEGMENTATION_CONFIG_ROOT",
    "train_entrypoint": "MMSEG_TRAIN_ENTRYPOINT",
    "test_entrypoint": "MMSEG_TEST_ENTRYPOINT",
    "checkpoint": "SEGMENTATION_CHECKPOINT",
}


def shell_quote(value: str) -> str:
    return shlex.quote(str(value))


def build_command(
    mode: str,
    config_id: str,
    checkpoint: str,
    device: str,
    work_dir: str | None,
    data_root: str | None,
    config_root: str,
    train_entrypoint: str,
    test_entrypoint: str,
) -> str:
    config_path = str(PurePosixPath(config_root) / CONFIG_BASENAMES[config_id])
    entrypoint = train_entrypoint if mode == "train" else test_entrypoint
    parts = ["env", f"CUDA_VISIBLE_DEVICES={shell_quote(device)}", "python", shell_quote(entrypoint), shell_quote(config_path)]
    if mode == "test":
        parts.append(shell_quote(checkpoint))
    if work_dir:
        parts.extend(["--work-dir", shell_quote(work_dir)])
    if data_root:
        overrides = [
            shell_quote(f"train_dataloader.dataset.data_root={data_root}"),
            shell_quote(f"val_dataloader.dataset.data_root={data_root}"),
            shell_quote(f"test_dataloader.dataset.data_root={data_root}"),
        ]
        parts.extend(["--cfg-options", *overrides])
    return " ".join(parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a safe single-GPU MambaVision MMSegmentation command template.",
        epilog=(
            "Examples:\n"
            "  print_mmseg_command.py train base --config-root ./configs/mamba_vision --train-entrypoint TARGET_MMSEG_TRAIN\n"
            "  print_mmseg_command.py test l3 --checkpoint ./ckpts/l3.pth --config-root ./configs/mamba_vision --test-entrypoint TARGET_MMSEG_TEST\n"
            "  print_mmseg_command.py test base --data-root /data/ADEChallengeData2016 --config-root ./configs/mamba_vision"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("mode", choices=("train", "test"), help="Which command to print.")
    parser.add_argument("config_id", choices=tuple(CONFIG_BASENAMES), help="MambaVision segmentation config id.")
    parser.add_argument("--config-root", default=PLACEHOLDERS["config_root"], help="Directory containing the selected MambaVision segmentation config in the target project.")
    parser.add_argument("--train-entrypoint", default=PLACEHOLDERS["train_entrypoint"], help="MMSegmentation training entry point in the target project.")
    parser.add_argument("--test-entrypoint", default=PLACEHOLDERS["test_entrypoint"], help="MMSegmentation test entry point in the target project.")
    parser.add_argument("--checkpoint", default=PLACEHOLDERS["checkpoint"], help="Checkpoint path used for test commands.")
    parser.add_argument("--device", default="0", help="CUDA_VISIBLE_DEVICES value for the single-GPU command.")
    parser.add_argument("--work-dir", default=None, help="Optional work directory to append to the printed command.")
    parser.add_argument("--data-root", default=None, help="Optional ADE20K root to inject into the printed command.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = build_command(
        mode=args.mode,
        config_id=args.config_id,
        checkpoint=args.checkpoint,
        device=args.device,
        work_dir=args.work_dir,
        data_root=args.data_root,
        config_root=args.config_root,
        train_entrypoint=args.train_entrypoint,
        test_entrypoint=args.test_entrypoint,
    )
    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
