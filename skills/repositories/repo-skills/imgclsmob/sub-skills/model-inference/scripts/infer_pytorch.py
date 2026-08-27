#!/usr/bin/env python3
"""Run one offline CPU image-classification inference through pytorchcv."""

import argparse
import math
import os

import numpy as np


MEAN = np.asarray((0.485, 0.456, 0.406), dtype=np.float32)
STD = np.asarray((0.229, 0.224, 0.225), dtype=np.float32)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run one CPU pytorchcv classification inference without downloading weights.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", default="resnet18", help="pytorchcv model name")
    parser.add_argument("--image", help="optional local image; omitted means a zero RGB image")
    parser.add_argument("--checkpoint", help="optional existing local PyTorch state-dict file")
    parser.add_argument("--input-size", type=int, default=224, help="square crop size")
    parser.add_argument(
        "--resize-inv-factor",
        type=float,
        default=0.875,
        help="input-size divided by the shorter-side resize length",
    )
    parser.add_argument("--classes", type=int, default=1000, help="classifier output count")
    parser.add_argument(
        "--expected-classes",
        type=int,
        help="optional output-count assertion; defaults to --classes",
    )
    parser.add_argument("--top-k", type=int, default=5, help="number of probabilities to print")
    parser.add_argument(
        "--remove-module",
        action="store_true",
        help="remove a leading module. from DataParallel checkpoint keys",
    )
    return parser.parse_args()


def load_rgb(path, input_size, resize_inv_factor):
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required only when --image is supplied") from exc

    with Image.open(path) as source:
        image = source.convert("RGB")
        resize_side = int(math.ceil(float(input_size) / resize_inv_factor))
        width, height = image.size
        if width <= 0 or height <= 0:
            raise ValueError("image has an invalid size")
        if width < height:
            new_size = (resize_side, int(round(resize_side * height / width)))
        else:
            new_size = (int(round(resize_side * width / height)), resize_side)
        resampling = getattr(Image, "Resampling", Image)
        image = image.resize(new_size, resampling.BILINEAR)
        left = max(0, int(round(0.5 * (image.width - input_size))))
        top = max(0, int(round(0.5 * (image.height - input_size))))
        image = image.crop((left, top, left + input_size, top + input_size))
        return np.asarray(image, dtype=np.uint8)


def make_input(args):
    if args.input_size <= 0 or args.resize_inv_factor <= 0:
        raise ValueError("--input-size and --resize-inv-factor must be positive")
    if args.image:
        if not os.path.isfile(args.image):
            raise FileNotFoundError(args.image)
        image = load_rgb(args.image, args.input_size, args.resize_inv_factor)
    else:
        image = np.zeros((args.input_size, args.input_size, 3), dtype=np.uint8)
    normalized = image.astype(np.float32) / 255.0
    normalized = (normalized - MEAN) / STD
    return np.expand_dims(normalized.transpose(2, 0, 1), axis=0)


def load_state_dict(path, device, remove_module):
    import torch

    checkpoint = torch.load(path, map_location=device)
    if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        checkpoint = checkpoint["state_dict"]
    if not isinstance(checkpoint, dict):
        raise TypeError("checkpoint must be a state_dict or contain a state_dict key")
    if not all(isinstance(key, str) for key in checkpoint):
        raise TypeError("checkpoint state_dict keys must be strings")
    if remove_module:
        checkpoint = {
            (key[7:] if key.startswith("module.") else key): value
            for key, value in checkpoint.items()
        }
    return checkpoint


def main():
    args = parse_args()
    if args.classes <= 0 or args.top_k <= 0:
        raise ValueError("--classes and --top-k must be positive")
    expected_classes = args.classes if args.expected_classes is None else args.expected_classes
    if expected_classes <= 0:
        raise ValueError("--expected-classes must be positive")

    import torch
    from pytorchcv.model_provider import get_model

    device = torch.device("cpu")
    # pretrained=False is intentional: this script has no download path.
    net = get_model(args.model, pretrained=False, num_classes=args.classes)
    net.to(device)
    if args.checkpoint:
        if not os.path.isfile(args.checkpoint):
            raise FileNotFoundError(args.checkpoint)
        state = load_state_dict(args.checkpoint, device, args.remove_module)
        missing, unexpected = net.load_state_dict(state, strict=True)
        if missing or unexpected:
            raise RuntimeError(
                "checkpoint mismatch: missing={}, unexpected={}".format(missing, unexpected)
            )
    net.eval()

    x = torch.from_numpy(make_input(args)).to(device=device, dtype=torch.float32)
    with torch.no_grad():
        logits = net(x)
    shape = tuple(int(dimension) for dimension in logits.shape)
    if len(shape) != 2 or shape[0] != 1:
        raise AssertionError("expected rank-2 output with batch size one, got {}".format(shape))
    if shape[1] != expected_classes:
        raise AssertionError("expected {} classes, got {}".format(expected_classes, shape[1]))

    probabilities = torch.softmax(logits, dim=1)[0].detach().cpu().numpy()
    top_k = min(args.top_k, len(probabilities))
    indices = np.argsort(probabilities)[::-1][:top_k]
    parameter_count = sum(
        int(parameter.numel()) for parameter in net.parameters() if parameter.requires_grad
    )
    print("input_shape={}".format(tuple(int(dimension) for dimension in x.shape)))
    print("output_shape={}".format(shape))
    print("device={}".format(device))
    print("parameter_count={}".format(parameter_count))
    print("topk={}".format(repr([(int(index), float(probabilities[index])) for index in indices])))


if __name__ == "__main__":
    main()
