#!/usr/bin/env python3
"""Render explicit fastMRI Lightning train/test command guidance.

This helper is intentionally source-independent: it does not import fastMRI or
repository demo scripts. It converts the bundled skill guidance into concrete
commands and configuration notes that agents can adapt into scripts.
"""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable, List


MODEL_DEFAULTS = {
    "unet": {
        "challenge": "singlecoil",
        "mask_type": "random",
        "center_fractions": ["0.08"],
        "accelerations": ["4"],
        "train_entry": "train_fastmri_unet.py",
        "notes": [
            "Use UnetDataTransform(challenge, mask_func=mask, use_seed=False) for train.",
            "Use UnetDataTransform(challenge, mask_func=mask) for validation.",
            "Use UnetDataTransform(challenge) for test.",
        ],
    },
    "varnet": {
        "challenge": "multicoil",
        "mask_type": "equispaced_fraction",
        "center_fractions": ["0.08"],
        "accelerations": ["4"],
        "train_entry": "train_fastmri_varnet.py",
        "notes": [
            "Use VarNetDataTransform(mask_func=mask, use_seed=False) for train.",
            "Use VarNetDataTransform(mask_func=mask) for validation.",
            "Use VarNetDataTransform() for test.",
        ],
    },
}


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def add_repeated(parts: List[str], flag: str, values: Iterable[str]) -> None:
    values = [str(value) for value in values]
    if values:
        parts.append(flag)
        parts.extend(values)


def build_command(args: argparse.Namespace) -> List[str]:
    defaults = MODEL_DEFAULTS[args.model]
    challenge = args.challenge or defaults["challenge"]
    mask_type = args.mask_type or defaults["mask_type"]
    center_fractions = args.center_fractions or defaults["center_fractions"]
    accelerations = args.accelerations or defaults["accelerations"]

    command = [
        "python",
        args.entrypoint or defaults["train_entry"],
        "--mode",
        args.mode,
        "--data_path",
        args.data_path,
        "--default_root_dir",
        args.default_root_dir,
        "--challenge",
        challenge,
        "--mask_type",
        mask_type,
    ]
    add_repeated(command, "--center_fractions", center_fractions)
    add_repeated(command, "--accelerations", accelerations)

    command.extend(["--batch_size", str(args.batch_size)])
    command.extend(["--num_workers", str(args.num_workers)])
    command.extend(["--test_split", args.test_split])

    if args.test_path:
        command.extend(["--test_path", args.test_path])
    if args.sample_rate is not None:
        command.extend(["--sample_rate", str(args.sample_rate)])
    if args.volume_sample_rate is not None:
        command.extend(["--volume_sample_rate", str(args.volume_sample_rate)])
    if args.combine_train_val:
        command.extend(["--combine_train_val", "True"])

    if args.cpu_fast_dev:
        command.extend(["--accelerator", "cpu", "--devices", "1", "--fast_dev_run", "True"])
    elif args.ddp:
        command.extend(
            [
                "--accelerator",
                "gpu",
                "--devices",
                str(args.devices),
                "--strategy",
                "ddp",
            ]
        )
    else:
        command.extend(["--accelerator", args.accelerator, "--devices", str(args.devices)])

    if args.max_epochs is not None:
        command.extend(["--max_epochs", str(args.max_epochs)])
    if args.ckpt_path:
        command.extend(["--ckpt_path", args.ckpt_path])

    return command


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.sample_rate is not None and args.volume_sample_rate is not None:
        parser.error("choose either --sample-rate or --volume-sample-rate, not both")
    if args.ddp and args.cpu_fast_dev:
        parser.error("--ddp and --cpu-fast-dev are mutually exclusive")
    if args.combine_train_val and args.mode != "train":
        parser.error("--combine-train-val is only meaningful for train mode")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render explicit fastMRI Lightning command guidance."
    )
    parser.add_argument("--model", choices=sorted(MODEL_DEFAULTS), required=True)
    parser.add_argument("--mode", choices=("train", "test"), default="train")
    parser.add_argument("--data-path", required=True, dest="data_path")
    parser.add_argument("--default-root-dir", required=True, dest="default_root_dir")
    parser.add_argument("--entrypoint", help="Generated local training script to call")
    parser.add_argument("--challenge", choices=("singlecoil", "multicoil"))
    parser.add_argument(
        "--mask-type",
        choices=("random", "equispaced", "equispaced_fraction", "magic", "magic_fraction"),
    )
    parser.add_argument("--center-fractions", nargs="+")
    parser.add_argument("--accelerations", nargs="+")
    parser.add_argument("--batch-size", type=int, default=1, dest="batch_size")
    parser.add_argument("--num-workers", type=int, default=4, dest="num_workers")
    parser.add_argument(
        "--test-split", choices=("val", "test", "challenge"), default="test", dest="test_split"
    )
    parser.add_argument("--test-path", dest="test_path")
    parser.add_argument("--sample-rate", type=float, dest="sample_rate")
    parser.add_argument("--volume-sample-rate", type=float, dest="volume_sample_rate")
    parser.add_argument("--combine-train-val", action="store_true", dest="combine_train_val")
    parser.add_argument("--cpu-fast-dev", action="store_true", dest="cpu_fast_dev")
    parser.add_argument("--ddp", action="store_true")
    parser.add_argument("--accelerator", default="gpu")
    parser.add_argument("--devices", type=int, default=1)
    parser.add_argument("--max-epochs", type=int, dest="max_epochs")
    parser.add_argument("--ckpt-path", dest="ckpt_path")
    args = parser.parse_args()
    validate_args(parser, args)
    return args


def main() -> None:
    args = parse_args()
    defaults = MODEL_DEFAULTS[args.model]
    command = build_command(args)
    ddp_enabled = args.ddp and not args.cpu_fast_dev

    print("# Rendered command")
    print(shell_join(command))
    print()
    print("# Required wiring notes")
    for note in defaults["notes"]:
        print(f"- {note}")
    print(
        "- Build mask with create_mask_for_mask_type(mask_type, center_fractions, accelerations)."
    )
    print(
        f"- Set FastMriDataModule(distributed_sampler={ddp_enabled}) for this rendered hardware path."
    )
    if args.cpu_fast_dev:
        print("- CPU fast-dev runs should use num_workers=0 when multiprocessing is fragile.")
    if args.combine_train_val:
        print("- combine_train_val=True is for final leaderboard-style training after validation policy is fixed.")
    if args.mode == "test":
        print("- Test reconstructions are written under default_root_dir/reconstructions.")
    print(
        "- Modern Lightning may require direct Trainer construction and ckpt_path instead of old argparse helpers."
    )


if __name__ == "__main__":
    main()
