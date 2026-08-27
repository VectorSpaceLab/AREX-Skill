#!/usr/bin/env python3
"""No-download timm smoke check for agents using the timm skill."""

from __future__ import annotations

import argparse
import json
from typing import Any


def _json_default(value: Any) -> str:
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe no-download timm API smoke check.")
    parser.add_argument("--model", default="resnet18", help="Model architecture to create with pretrained=False.")
    parser.add_argument("--num-classes", type=int, default=3, help="Classifier output classes for the smoke model.")
    parser.add_argument("--batch-size", type=int, default=1, help="Random input batch size.")
    parser.add_argument("--image-size", type=int, default=224, help="Square random input image size.")
    parser.add_argument("--device", default="cpu", help="Torch device for the smoke forward pass.")
    parser.add_argument("--skip-forward", action="store_true", help="Only create objects; do not run a forward pass.")
    args = parser.parse_args()

    import torch
    import timm
    from timm.data import create_transform, resolve_data_config
    from timm.optim import create_optimizer_v2
    from timm.scheduler import create_scheduler_v2

    model = timm.create_model(args.model, pretrained=False, num_classes=args.num_classes)
    model.to(args.device)
    model.eval()

    data_config = resolve_data_config({"input_size": (3, args.image_size, args.image_size)}, model=model)
    transform = create_transform(**data_config)
    optimizer = create_optimizer_v2(model, opt="sgd", lr=0.01)
    scheduler, scheduler_epochs = create_scheduler_v2(optimizer, sched="cosine", num_epochs=2)

    output_shape = None
    if not args.skip_forward:
        sample = torch.randn(args.batch_size, 3, args.image_size, args.image_size, device=args.device)
        with torch.no_grad():
            output_shape = tuple(model(sample).shape)

    result = {
        "timm_version": timm.__version__,
        "torch_version": torch.__version__,
        "model": args.model,
        "num_classes": args.num_classes,
        "device": args.device,
        "output_shape": output_shape,
        "data_config": data_config,
        "transform_type": type(transform).__name__,
        "optimizer_type": type(optimizer).__name__,
        "scheduler_type": type(scheduler).__name__,
        "scheduler_epochs": scheduler_epochs,
    }
    print(json.dumps(result, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
