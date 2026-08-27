#!/usr/bin/env python3
"""Write CPU-safe RoboSat dataset and model TOML templates."""

import argparse
from pathlib import Path


DATASET_TEMPLATE = """# RoboSat dataset configuration.
# Edit dataset to point at a directory with training/images, training/labels,
# validation/images, and validation/labels Slippy Map subtrees.

[common]
  dataset = '{dataset_root}'
  classes = ['background', '{foreground_class}']
  colors  = ['denim', 'orange']

[weights]
  # Replace with output from: rs weights --dataset dataset.toml
  values = [1.0, 1.0]
"""


MODEL_TEMPLATE = """# RoboSat model configuration.
# CPU is the safe default. Set cuda = true only after verifying a compatible
# torch CUDA build and driver in the target environment.

[common]
  cuda       = {cuda}
  batch_size = {batch_size}
  image_size = {image_size}
  checkpoint = '{checkpoint_dir}'

[opt]
  epochs = {epochs}
  lr     = {learning_rate}
  # Supported values: Lovasz, CrossEntropy, mIoU, Focal
  loss   = '{loss}'
"""


def build_parser():
    parser = argparse.ArgumentParser(description="Create RoboSat dataset/model TOML templates.")
    parser.add_argument("--out-dir", default=".", help="directory to write dataset.toml and model.toml")
    parser.add_argument("--dataset-root", default="/data/dataset", help="dataset root to put in dataset.toml")
    parser.add_argument("--foreground-class", default="parking", help="foreground class name")
    parser.add_argument("--checkpoint-dir", default="/data/checkpoints", help="checkpoint directory for model.toml")
    parser.add_argument("--cuda", action="store_true", help="write cuda = true instead of the CPU-safe default")
    parser.add_argument("--batch-size", type=int, default=2, help="training batch size")
    parser.add_argument("--image-size", type=int, default=512, help="model image size; must be divisible by 32")
    parser.add_argument("--epochs", type=int, default=10, help="number of epochs")
    parser.add_argument("--learning-rate", type=float, default=0.0001, help="optimizer learning rate")
    parser.add_argument("--loss", default="Lovasz", choices=["Lovasz", "CrossEntropy", "mIoU", "Focal"], help="loss name")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.image_size % 32 != 0:
        raise SystemExit("Error: --image-size must be divisible by 32 for RoboSat's ResNet-backed U-Net")
    if args.batch_size <= 0:
        raise SystemExit("Error: --batch-size must be positive")
    if args.epochs <= 0:
        raise SystemExit("Error: --epochs must be positive")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = out_dir / "dataset.toml"
    model_path = out_dir / "model.toml"

    dataset_path.write_text(
        DATASET_TEMPLATE.format(dataset_root=args.dataset_root, foreground_class=args.foreground_class),
        encoding="utf-8",
    )
    model_path.write_text(
        MODEL_TEMPLATE.format(
            cuda="true" if args.cuda else "false",
            batch_size=args.batch_size,
            image_size=args.image_size,
            checkpoint_dir=args.checkpoint_dir,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            loss=args.loss,
        ),
        encoding="utf-8",
    )

    print("wrote {}".format(dataset_path))
    print("wrote {}".format(model_path))
    if args.cuda:
        print("note: cuda=true requires a verified compatible torch CUDA environment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
