#!/usr/bin/env python3
"""Build a DALLE-pytorch VAE training command template."""
import argparse
import json
import shlex


def add_flag(cmd, flag, value=None):
    if value is None:
        cmd.append(flag)
    else:
        cmd.extend([flag, str(value)])


def main():
    p = argparse.ArgumentParser(description="Build a command matching the DALLE-pytorch VAE training helper surface.")
    p.add_argument("--image-folder", required=True, help="ImageFolder root; usually contains class/dummy subdirectories.")
    p.add_argument("--image-size", type=int, default=128)
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--learning-rate", type=float, default=1e-3)
    p.add_argument("--lr-decay-rate", type=float, default=0.98)
    p.add_argument("--num-tokens", type=int, default=8192)
    p.add_argument("--num-layers", type=int, default=3)
    p.add_argument("--num-resnet-blocks", type=int, default=2)
    p.add_argument("--emb-dim", type=int, default=512)
    p.add_argument("--hidden-dim", type=int, default=256)
    p.add_argument("--kl-loss-weight", type=float, default=0.0)
    p.add_argument("--smooth-l1-loss", action="store_true")
    p.add_argument("--transparent", action="store_true")
    p.add_argument("--starting-temp", type=float, default=1.0)
    p.add_argument("--temp-min", type=float, default=0.5)
    p.add_argument("--anneal-rate", type=float, default=1e-6)
    p.add_argument("--num-images-save", type=int, default=4)
    p.add_argument("--distributed-backend", choices=["deepspeed", "horovod"], default=None)
    p.add_argument("--deepspeed", action="store_true", help="Alias for --distributed-backend deepspeed plus --deepspeed flag.")
    p.add_argument("--as-json", action="store_true")
    args = p.parse_args()

    cmd = ["python", "train_vae.py"]
    for flag, value in [
        ("--image_folder", args.image_folder),
        ("--image_size", args.image_size),
        ("--epochs", args.epochs),
        ("--batch_size", args.batch_size),
        ("--learning_rate", args.learning_rate),
        ("--lr_decay_rate", args.lr_decay_rate),
        ("--num_tokens", args.num_tokens),
        ("--num_layers", args.num_layers),
        ("--num_resnet_blocks", args.num_resnet_blocks),
        ("--emb_dim", args.emb_dim),
        ("--hidden_dim", args.hidden_dim),
        ("--kl_loss_weight", args.kl_loss_weight),
        ("--starting_temp", args.starting_temp),
        ("--temp_min", args.temp_min),
        ("--anneal_rate", args.anneal_rate),
        ("--num_images_save", args.num_images_save),
    ]:
        add_flag(cmd, flag, value)
    if args.smooth_l1_loss:
        add_flag(cmd, "--smooth_l1_loss")
    if args.transparent:
        add_flag(cmd, "--transparent")
    backend = "deepspeed" if args.deepspeed else args.distributed_backend
    if backend:
        add_flag(cmd, "--distributed_backend", backend)
        if backend == "deepspeed":
            add_flag(cmd, "--deepspeed")

    warnings = [
        "The historical helper calls CUDA when not using a distributed backend.",
        "The command writes vae.pt/vae-final.pt and logs to W&B on the root worker.",
        "ImageFolder roots need class or dummy subdirectories, not a flat folder.",
    ]
    if args.as_json:
        print(json.dumps({"command": cmd, "shell": " ".join(shlex.quote(x) for x in cmd), "warnings": warnings}, indent=2))
    else:
        print(" ".join(shlex.quote(x) for x in cmd))
        for warning in warnings:
            print(f"# WARNING: {warning}")


if __name__ == "__main__":
    main()
