#!/usr/bin/env python3
"""Evaluate or smoke-test an OFA model.

Purpose: provide a safe bundled replacement for the repo's evaluation scripts.

Safe defaults:
- supernet mode
- no pretrained weights
- no dataset required
- CPU or CUDA smoke only unless a data root is provided

Examples:
  python scripts/evaluate_ofa.py
  python scripts/evaluate_ofa.py --mode specialized --specialized-id flops@389M_top1@79.1_finetune@75 --pretrained
  python scripts/evaluate_ofa.py --data-root /path/to/imagenet --mode supernet --sample-subnet --max-batches 2
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import datasets, transforms


def _pick_device(requested: str) -> str:
    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return requested


def _maybe_add_repo_root(repo_root: str) -> None:
    if repo_root:
        sys.path.insert(0, str(Path(repo_root).resolve()))


def _build_loader(root: Path, image_size: int, batch_size: int, workers: int):
    split_root = root / "val" if (root / "val").is_dir() else root
    dataset = datasets.ImageFolder(
        str(split_root),
        transforms.Compose(
            [
                transforms.Resize(int(math.ceil(image_size / 0.875))),
                transforms.CenterCrop(image_size),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        ),
    )
    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
    )
    return loader


def _forward_smoke(model: nn.Module, device: str, image_size: int):
    model = model.to(device)
    x = torch.zeros(1, 3, image_size, image_size, device=device)
    with torch.no_grad():
        y = model(x)
    print(f"smoke_ok shape={tuple(y.shape)} device={device}")


def _evaluate(model: nn.Module, loader, device: str, max_batches: int):
    from ofa.utils import accuracy

    if device == "cuda":
        model = nn.DataParallel(model).to(device)
    else:
        model = model.to(device)

    model.eval()
    criterion = nn.CrossEntropyLoss().to(device)
    top1_sum = 0.0
    top5_sum = 0.0
    seen = 0

    with torch.no_grad():
        for step, (images, labels) in enumerate(loader):
            if step >= max_batches:
                break
            images = images.to(device)
            labels = labels.to(device)
            output = model(images)
            loss = criterion(output, labels)
            acc1, acc5 = accuracy(output, labels, topk=(1, 5))
            top1_sum += acc1[0].item() * images.size(0)
            top5_sum += acc5[0].item() * images.size(0)
            seen += images.size(0)
            print(
                f"batch={step} loss={loss.item():.5f} top1={acc1[0].item():.2f} top5={acc5[0].item():.2f}"
            )

    if seen:
        print(f"summary top1={top1_sum / seen:.2f} top5={top5_sum / seen:.2f} samples={seen}")
    else:
        print("summary no_samples")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default="", help="Optional local checkout root for import fallback.")
    parser.add_argument("--mode", choices=["supernet", "specialized"], default="supernet")
    parser.add_argument("--net-id", default="ofa_resnet50")
    parser.add_argument("--specialized-id", default="")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--data-root", default="")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--max-batches", type=int, default=1)
    parser.add_argument("--pretrained", action="store_true")
    parser.add_argument("--sample-subnet", action="store_true")
    args = parser.parse_args()

    _maybe_add_repo_root(args.repo_root)
    device = _pick_device(args.device)

    from ofa.model_zoo import ofa_net, ofa_specialized

    if args.mode == "supernet":
        model = ofa_net(args.net_id, pretrained=args.pretrained)
        image_size = args.image_size
        if args.sample_subnet and hasattr(model, "sample_active_subnet"):
            model.sample_active_subnet()
            model = model.get_active_subnet(preserve_weight=True)
            print("sampled_subnet_ok")
    else:
        specialized_id = args.specialized_id or args.net_id
        model, image_size = ofa_specialized(specialized_id, pretrained=args.pretrained)
        print(f"specialized_id={specialized_id}")

    print(f"mode={args.mode} device={device} image_size={image_size}")

    if not args.data_root:
        _forward_smoke(model, device, image_size)
        return 0

    loader = _build_loader(Path(args.data_root), image_size, args.batch_size, args.workers)
    _evaluate(model, loader, device, args.max_batches)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
