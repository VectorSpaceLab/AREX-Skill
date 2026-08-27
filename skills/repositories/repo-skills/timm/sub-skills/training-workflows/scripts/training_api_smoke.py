#!/usr/bin/env python3
"""Smoke-check timm training API composition on CPU.

Creates a timm model, optimizer, scheduler, loss, metrics, optional task wrapper,
EMA, and optionally runs one fake forward/loss/backward/step.
"""
import argparse
import json
from typing import Tuple

import torch

from timm import create_model
from timm.loss import BinaryCrossEntropy, LabelSmoothingCrossEntropy, SoftTargetCrossEntropy
from timm.optim import create_optimizer_v2
from timm.scheduler import create_scheduler_v2
from timm.task import ClassificationTask
from timm.utils import AverageMeter, ModelEmaV3, accuracy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-check timm training API composition on CPU.")
    parser.add_argument("--model", default="resnet18", help="timm model name to instantiate with pretrained=False.")
    parser.add_argument("--num-classes", type=int, default=10, help="Classifier output classes for the smoke model.")
    parser.add_argument("--batch-size", type=int, default=2, help="Fake batch size.")
    parser.add_argument("--image-size", type=int, default=64, help="Square fake image size.")
    parser.add_argument("--opt", default="adamw", help="Optimizer name for create_optimizer_v2.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Base learning rate.")
    parser.add_argument("--weight-decay", type=float, default=0.05, help="Weight decay.")
    parser.add_argument("--sched", default="cosine", help="Scheduler name for create_scheduler_v2.")
    parser.add_argument("--num-epochs", type=int, default=3, help="Requested scheduler epochs.")
    parser.add_argument("--warmup-epochs", type=int, default=1, help="Scheduler warmup epochs.")
    parser.add_argument(
        "--loss",
        choices=("ce", "label-smoothing", "soft-target", "bce"),
        default="label-smoothing",
        help="Loss family to instantiate.",
    )
    parser.add_argument("--task", action="store_true", help="Route forward/loss through ClassificationTask.")
    parser.add_argument("--ema", action="store_true", help="Instantiate and update ModelEmaV3.")
    parser.add_argument("--no-backward", action="store_true", help="Skip fake backward and optimizer step.")
    return parser.parse_args()


def create_loss(name: str):
    if name == "ce":
        return torch.nn.CrossEntropyLoss(), False
    if name == "label-smoothing":
        return LabelSmoothingCrossEntropy(smoothing=0.1), False
    if name == "soft-target":
        return SoftTargetCrossEntropy(), True
    if name == "bce":
        return BinaryCrossEntropy(smoothing=0.1), True
    raise AssertionError(f"Unhandled loss choice: {name}")


def fake_batch(batch_size: int, num_classes: int, image_size: int, soft_target: bool) -> Tuple[torch.Tensor, torch.Tensor]:
    images = torch.randn(batch_size, 3, image_size, image_size)
    labels = torch.randint(0, num_classes, (batch_size,))
    if not soft_target:
        return images, labels
    targets = torch.zeros(batch_size, num_classes)
    targets.scatter_(1, labels.view(-1, 1), 1.0)
    return images, targets


def main() -> None:
    args = parse_args()
    torch.manual_seed(42)

    model = create_model(args.model, pretrained=False, num_classes=args.num_classes)
    model.train()
    optimizer = create_optimizer_v2(
        model,
        opt=args.opt,
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    scheduler, adjusted_epochs = create_scheduler_v2(
        optimizer,
        sched=args.sched,
        num_epochs=args.num_epochs,
        warmup_epochs=args.warmup_epochs,
    )
    criterion, soft_target = create_loss(args.loss)
    images, targets = fake_batch(args.batch_size, args.num_classes, args.image_size, soft_target)

    task = ClassificationTask(model, criterion, verbose=False) if args.task else None
    model_ema = ModelEmaV3(model, decay=0.9999, foreach=False) if args.ema else None

    if task is not None:
        result = task(images, targets)
        output = result["output"]
        loss = result["loss"]
    else:
        output = model(images)
        loss = criterion(output, targets)

    if not args.no_backward:
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        if model_ema is not None:
            model_ema.update(model, step=1)

    scheduler.step(1)

    hard_targets = targets.argmax(dim=1) if targets.ndim == 2 else targets
    top1 = accuracy(output.detach(), hard_targets, topk=(1,))[0]
    loss_meter = AverageMeter()
    loss_meter.update(loss.item(), n=args.batch_size)

    report = {
        "model": args.model,
        "optimizer": type(optimizer).__name__,
        "scheduler": type(scheduler).__name__ if scheduler is not None else None,
        "adjusted_epochs": adjusted_epochs,
        "loss": type(criterion).__name__,
        "task": type(task).__name__ if task is not None else None,
        "ema": type(model_ema).__name__ if model_ema is not None else None,
        "backward": not args.no_backward,
        "loss_value": round(loss_meter.avg, 6),
        "top1": round(float(top1.item()), 4),
        "param_groups": len(optimizer.param_groups),
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
