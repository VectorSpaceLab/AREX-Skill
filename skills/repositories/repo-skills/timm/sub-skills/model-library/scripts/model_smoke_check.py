#!/usr/bin/env python3
"""No-download timm model creation and forward-pass smoke check."""

import argparse
import sys
import warnings

try:
    import torch
    import timm
except ModuleNotFoundError as exc:
    raise SystemExit(
        f"Missing required package: {exc.name}. Install timm with its PyTorch runtime before running this smoke check."
    ) from exc


def _parse_args():
    parser = argparse.ArgumentParser(description="Create a timm model and run a tiny random forward pass.")
    parser.add_argument("--model", default="resnet18", help="timm model name or architecture.tag identifier")
    parser.add_argument("--num-classes", type=int, default=1000, help="classifier class count to request")
    parser.add_argument("--batch-size", type=int, default=1, help="batch size for the random input")
    parser.add_argument("--img-size", type=int, default=64, help="max H/W used for the random smoke input")
    parser.add_argument("--in-chans", type=int, default=None, help="override input channels")
    parser.add_argument("--pretrained", action="store_true", help="load pretrained weights; may download or require auth")
    parser.add_argument("--cache-dir", default=None, help="optional cache directory for pretrained weights")
    return parser.parse_args()


def _smoke_input_size(model, max_img_size, in_chans):
    cfg = getattr(model, "pretrained_cfg", {}) or {}
    cfg_input_size = cfg.get("input_size", (3, 224, 224))
    channels = in_chans or cfg_input_size[0]
    height = min(cfg_input_size[-2], max_img_size)
    width = min(cfg_input_size[-1], max_img_size)
    return channels, height, width


def main():
    args = _parse_args()
    if args.pretrained:
        warnings.warn(
            "--pretrained may download weights or require Hugging Face authentication; "
            "omit it for an offline smoke check.",
            stacklevel=2,
        )

    kwargs = {"num_classes": args.num_classes}
    if args.in_chans is not None:
        kwargs["in_chans"] = args.in_chans

    model = timm.create_model(
        args.model,
        pretrained=args.pretrained,
        cache_dir=args.cache_dir,
        **kwargs,
    )
    model.eval()

    input_size = _smoke_input_size(model, args.img_size, args.in_chans)
    inputs = torch.randn(args.batch_size, *input_size)

    with torch.inference_mode():
        outputs = model(inputs)

    if isinstance(outputs, (tuple, list)):
        shape = [tuple(output.shape) for output in outputs]
    elif isinstance(outputs, dict):
        shape = {key: tuple(value.shape) for key, value in outputs.items()}
    else:
        shape = tuple(outputs.shape)

    print(f"model={args.model}")
    print(f"pretrained={args.pretrained}")
    print(f"input_shape={tuple(inputs.shape)}")
    print(f"output_shape={shape}")


if __name__ == "__main__":
    main()
