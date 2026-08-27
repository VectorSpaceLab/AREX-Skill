#!/usr/bin/env python3
"""Print a safe Tencent ML-Images pretraining command.

This helper does not run training. It expands the repo's shell example into an
explicit command with concrete directories and flags.
"""

import argparse
import shlex


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--python", default="python", help="Python executable or command to prefix the script with.")
    p.add_argument("--script", default="train.py", help="Training script path inside a Tencent ML-Images checkout.")
    p.add_argument("--data-dir", required=True, help="Parent directory containing train/ and val/ TFRecord splits.")
    p.add_argument("--model-dir", required=True, help="Directory for checkpoints.")
    p.add_argument("--tmp-model-dir", required=True, help="Directory for temporary checkpoints.")
    p.add_argument("--log-dir", required=True, help="Directory for log output.")
    p.add_argument("--class-num", type=int, default=11166, help="Number of classes; use 11166 for ML-Images pretraining.")
    p.add_argument("--resnet-size", type=int, default=101, choices=[50, 101, 152], help="Supported ResNet depth.")
    p.add_argument("--image-size", type=int, default=224, help="Input image crop size.")
    p.add_argument("--data-format", default="NCHW", choices=["NCHW", "NHWC"], help="TensorFlow data format string.")
    p.add_argument("--batch-size", type=int, default=1, help="Batch size per step.")
    p.add_argument("--max-iter", type=int, default=440000, help="Maximum training steps.")
    p.add_argument("--snapshot", type=int, default=4400, help="Checkpoint save interval.")
    p.add_argument("--log-interval", type=int, default=100, help="Log interval.")
    p.add_argument("--lr", type=float, default=0.08, help="Initial learning rate.")
    p.add_argument("--lr-decay-step", type=int, default=110000, help="Step size for decay schedule.")
    p.add_argument("--lr-decay-factor", type=float, default=0.1, help="Learning rate decay factor.")
    p.add_argument("--warmup", type=int, default=35200, help="Warmup step count.")
    p.add_argument("--lr-warmup", type=float, default=0.01, help="Warmup learning rate.")
    p.add_argument("--lr-warmup-decay-step", type=int, default=4400, help="Warmup decay step.")
    p.add_argument("--lr-warmup-decay-factor", type=float, default=1.297, help="Warmup decay factor.")
    p.add_argument("--mask-thres", type=float, default=0.7, help="Positive mask threshold.")
    p.add_argument("--neg-select", type=float, default=0.1, help="Fraction of negative classes selected per step.")
    p.add_argument("--weight-decay", type=float, default=0.0001, help="L2 weight decay factor.")
    p.add_argument("--num-preprocess-threads", type=int, default=4, help="Preprocess threads per tower.")
    return p.parse_args()


def main() -> int:
    a = parse_args()
    cmd = [
        a.python,
        a.script,
        f"--data_dir={a.data_dir}",
        f"--model_dir={a.model_dir}",
        f"--tmp_model_dir={a.tmp_model_dir}",
        f"--image_size={a.image_size}",
        f"--class_num={a.class_num}",
        f"--resnet_size={a.resnet_size}",
        f"--mask_thres={a.mask_thres}",
        f"--neg_select={a.neg_select}",
        f"--batch_size={a.batch_size}",
        f"--num_preprocess_threads={a.num_preprocess_threads}",
        f"--batch_norm_decay=0.997",
        f"--batch_norm_epsilon=1e-5",
        f"--lr={a.lr}",
        f"--lr_decay_step={a.lr_decay_step}",
        f"--lr_decay_factor={a.lr_decay_factor}",
        f"--weight_decay={a.weight_decay}",
        f"--max_iter={a.max_iter}",
        f"--snapshot={a.snapshot}",
        f"--warmup={a.warmup}",
        f"--lr_warmup={a.lr_warmup}",
        f"--lr_warmup_decay_step={a.lr_warmup_decay_step}",
        f"--lr_warmup_decay_factor={a.lr_warmup_decay_factor}",
        f"--log_interval={a.log_interval}",
        f"--data_format={a.data_format}",
    ]
    print(" \\\n  ".join(shlex.quote(part) for part in cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
