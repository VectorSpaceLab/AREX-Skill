#!/usr/bin/env python3
"""Tiny no-network ImagenTrainer smoke check.

This is a standalone adaptation of the repository's trainer test intent:
construct a tiny ImagenTrainer, optionally register a tiny dataset, run one
train step, and assert the per-unet step counter increments.

It deliberately avoids text conditioning and monkeypatches the Transformers T5
configuration lookup before importing imagen-pytorch so the script does not need
network access or a Hugging Face cache just to import class defaults.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny no-network ImagenTrainer smoke check.")
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="auto",
        help="Requested execution device. 'auto' uses CUDA when torch/Accelerate select it, otherwise CPU.",
    )
    parser.add_argument(
        "--run-step",
        action="store_true",
        help="Also register a tiny dataset and run one train_step. Without this, only construction is checked.",
    )
    parser.add_argument("--image-size", type=int, default=16, help="Tiny square image size for the smoke dataset.")
    parser.add_argument("--dataset-size", type=int, default=4, help="Number of synthetic images in the dataset.")
    parser.add_argument("--batch-size", type=int, default=2, help="Dataloader batch size for --run-step.")
    parser.add_argument("--max-batch-size", type=int, default=1, help="Microbatch size passed to train_step for accumulation.")
    return parser.parse_args()


def configure_device_environment(device: str) -> None:
    # Set before importing torch/accelerate/imagen-pytorch so CPU smoke remains CPU even on CUDA hosts.
    if device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""


def patch_t5_config_for_offline_import():
    import transformers

    original = transformers.T5Config.from_pretrained

    @classmethod
    def offline_from_pretrained(cls, *args, **kwargs):  # noqa: ANN001 - mirrors transformers signature loosely
        return cls(d_model=768)

    transformers.T5Config.from_pretrained = offline_from_pretrained
    return original


@dataclass
class SmokeModules:
    torch: object
    Dataset: type
    Imagen: type
    Unet: type
    ImagenTrainer: type


def import_smoke_modules() -> SmokeModules:
    original_from_pretrained = patch_t5_config_for_offline_import()
    try:
        import torch
        from torch.utils.data import Dataset
        from imagen_pytorch.imagen_pytorch import Imagen, Unet
        from imagen_pytorch.trainer import ImagenTrainer
    finally:
        # Restore for code that may import this script as a module after imagen-pytorch classes are loaded.
        import transformers

        transformers.T5Config.from_pretrained = original_from_pretrained

    return SmokeModules(
        torch=torch,
        Dataset=Dataset,
        Imagen=Imagen,
        Unet=Unet,
        ImagenTrainer=ImagenTrainer,
    )


def choose_device(torch, requested: str) -> str:  # noqa: ANN001 - torch module
    cuda_available = torch.cuda.is_available()
    if requested == "cuda" and not cuda_available:
        raise RuntimeError("--device cuda requested, but torch.cuda.is_available() is false")
    if requested == "auto":
        return "cuda" if cuda_available else "cpu"
    return requested


def reset_trainer_lock(ImagenTrainer) -> None:  # noqa: ANN001 - class from package
    # Safe for local smoke. Do not use this to bypass the distributed one-trainer-per-process invariant.
    ImagenTrainer.locked = False


def build_tiny_trainer(mods: SmokeModules, image_size: int):
    torch = mods.torch
    Imagen = mods.Imagen
    Unet = mods.Unet
    ImagenTrainer = mods.ImagenTrainer

    reset_trainer_lock(ImagenTrainer)

    torch.manual_seed(0)
    unet = Unet(
        dim=8,
        dim_mults=(1, 1),
        num_resnet_blocks=1,
        layer_attns=False,
        layer_cross_attns=False,
        attn_heads=2,
        cond_on_text=False,
    )
    imagen = Imagen(
        unets=(unet,),
        image_sizes=(image_size,),
        timesteps=4,
        condition_on_text=False,
    )
    trainer = ImagenTrainer(
        imagen=imagen,
        use_ema=False,
        lr=1e-4,
        precision="no",
        verbose=True,
    )
    return trainer


def make_dataset(mods: SmokeModules, *, image_size: int, dataset_size: int):
    torch = mods.torch
    Dataset = mods.Dataset

    class TinyImageDataset(Dataset):
        def __len__(self):
            return dataset_size

        def __getitem__(self, index):
            generator = torch.Generator().manual_seed(int(index))
            return torch.rand((3, image_size, image_size), generator=generator)

    return TinyImageDataset()


def main() -> int:
    args = parse_args()
    configure_device_environment(args.device)
    mods = import_smoke_modules()
    torch = mods.torch

    try:
        chosen_device = choose_device(torch, args.device)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.image_size < 8:
        print("ERROR: --image-size must be at least 8 for the tiny U-Net downsampling path", file=sys.stderr)
        return 2
    if args.dataset_size < args.batch_size:
        print("ERROR: --dataset-size must be >= --batch-size", file=sys.stderr)
        return 2
    if args.max_batch_size < 1 or args.batch_size < 1:
        print("ERROR: batch sizes must be positive", file=sys.stderr)
        return 2

    trainer = None
    try:
        trainer = build_tiny_trainer(mods, args.image_size)
        actual_device = getattr(trainer.device, "type", str(trainer.device))
        if args.device != "auto" and actual_device != chosen_device:
            print(
                f"ERROR: requested {chosen_device}, but trainer is on {trainer.device}",
                file=sys.stderr,
            )
            return 3

        print(f"constructed ImagenTrainer on {trainer.device}; run_step={args.run_step}")

        if args.run_step:
            ds = make_dataset(mods, image_size=args.image_size, dataset_size=args.dataset_size)
            trainer.add_train_dataset(ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
            loss = trainer.train_step(unet_number=1, max_batch_size=args.max_batch_size)
            steps = trainer.num_steps_taken(1)
            if steps != 1:
                print(f"ERROR: expected 1 step, observed {steps}", file=sys.stderr)
                return 4
            if not isinstance(loss, float) or not torch.isfinite(torch.tensor(loss)):
                print(f"ERROR: non-finite loss {loss!r}", file=sys.stderr)
                return 5
            print(f"train_step ok; loss={loss:.6f}; steps={steps}")

        return 0
    finally:
        if trainer is not None:
            del trainer
        reset_trainer_lock(mods.ImagenTrainer)


if __name__ == "__main__":
    raise SystemExit(main())
