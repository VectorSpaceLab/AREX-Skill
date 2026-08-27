#!/usr/bin/env python3
"""Print a safe Tencent ML-Images finetuning command.

This helper does not run finetuning. It expands the repo's shell example into a
command with explicit flag names and warns about legacy example typos.
"""

import argparse
import shlex


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--python", default="python2.7", help="Python executable or command to prefix the script with.")
    p.add_argument("--script", default="finetune.py", help="Finetuning script path inside a Tencent ML-Images checkout.")
    p.add_argument("--mode", default="train", help="Mode flag passed to finetune.py.")
    p.add_argument("--class-num", type=int, default=1000, help="ImageNet class count for the finetuning head.")
    p.add_argument("--data-dir", required=True, help="Parent directory containing train/ and val/ TFRecord splits.")
    p.add_argument("--num-gpus", type=int, default=4, help="Number of GPUs to use.")
    p.add_argument("--batch-size", type=int, default=64, help="Batch size across all GPUs.")
    p.add_argument("--max-iter", type=int, default=600000, help="Maximum training steps.")
    p.add_argument("--lr", type=float, default=0.1, help="Initial learning rate.")
    p.add_argument("--lr-decay-step", type=int, default=150000, help="Step size for decay schedule.")
    p.add_argument("--lr-decay-factor", type=float, default=0.1, help="Learning rate decay factor.")
    p.add_argument("--weight-decay", type=float, default=0.0001, help="Weight decay factor; prefer this flag over the typo in the public example.")
    p.add_argument("--optimizer", default="mom", choices=["mom", "sgd"], help="Optimizer type.")
    p.add_argument("--batch-norm-epsilon", type=float, default=1e-5, help="Batch norm epsilon.")
    p.add_argument("--resnet-size", type=int, default=101, choices=[50, 101, 152], help="ResNet depth.")
    p.add_argument("--prof-interval", type=int, default=500, help="Timing log interval.")
    p.add_argument("--log-interval", type=int, default=5000, help="Summary log interval.")
    p.add_argument("--snapshot", type=int, default=5000, help="Checkpoint save interval.")
    p.add_argument("--model-dir", required=True, help="Checkpoint directory.")
    p.add_argument("--log-dir", required=True, help="Log directory.")
    p.add_argument("--image-size", type=int, default=224, help="Input size.")
    p.add_argument("--fix-block2", action="store_true", help="Restrict trainable vars to later blocks/global/logits.")
    p.add_argument("--restore", action="store_true", help="Restore from a pretrained checkpoint.")
    p.add_argument("--data-format", default="NCHW", choices=["NCHW", "NHWC"], help="TensorFlow data format string.")
    p.add_argument("--pretrain-ckpt", required=True, help="Checkpoint prefix/path to restore.")
    return p.parse_args()


def main() -> int:
    a = parse_args()
    cmd = [
        a.python,
        a.script,
        f"--mode={a.mode}",
        f"--class_num={a.class_num}",
        f"--data_dir={a.data_dir}",
        f"--num_gpus={a.num_gpus}",
        f"--batch_size={a.batch_size}",
        f"--max_iter={a.max_iter}",
        f"--lr={a.lr}",
        f"--lr_decay_step={a.lr_decay_step}",
        f"--lr_decay_factor={a.lr_decay_factor}",
        f"--weight_decay={a.weight_decay}",
        f"--optimizer={a.optimizer}",
        f"--batch_norm_epsilon={a.batch_norm_epsilon}",
        f"--resnet_size={a.resnet_size}",
        f"--prof_interval={a.prof_interval}",
        f"--log_interval={a.log_interval}",
        f"--snapshot={a.snapshot}",
        f"--model_dir={a.model_dir}",
        f"--log_dir={a.log_dir}",
        f"--image_size={a.image_size}",
        f"--data_format={a.data_format}",
        f"--pretrain_ckpt={a.pretrain_ckpt}",
    ]
    if a.fix_block2:
        cmd.append("--FixBlock2=True")
    if a.restore:
        cmd.append("--restore=True")
    print(" \\\n  ".join(shlex.quote(part) for part in cmd))
    print("\n# Note: the public example uses typoed flags --weight_decay_rate and --batch_norm_elipson; the source flags are --weight_decay and --batch_norm_epsilon.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
