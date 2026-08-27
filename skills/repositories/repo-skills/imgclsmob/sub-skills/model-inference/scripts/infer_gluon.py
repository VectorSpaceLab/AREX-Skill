#!/usr/bin/env python3
"""Run one offline CPU image-classification inference through Gluon."""

import argparse
import math
import os

import numpy as np


MEAN = np.asarray((0.485, 0.456, 0.406), dtype=np.float32)
STD = np.asarray((0.229, 0.224, 0.225), dtype=np.float32)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run one CPU Gluon classification inference without downloading weights.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", default="resnet18", help="gluoncv2 model name")
    parser.add_argument("--image", help="optional local image; omitted means a zero RGB image")
    parser.add_argument("--checkpoint", help="optional existing local MXNet parameter file")
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


def provider_get_model():
    """Import the public provider in source-package or installed-package form."""
    try:
        from gluon.gluoncv2.model_provider import get_model
    except ModuleNotFoundError as exc:
        # The released package exposes the same provider as gluoncv2.
        if exc.name not in {"gluon", "gluon.gluoncv2"}:
            raise
        from gluoncv2.model_provider import get_model
    return get_model


def main():
    args = parse_args()
    if args.classes <= 0 or args.top_k <= 0:
        raise ValueError("--classes and --top-k must be positive")
    expected_classes = args.classes if args.expected_classes is None else args.expected_classes
    if expected_classes <= 0:
        raise ValueError("--expected-classes must be positive")

    import mxnet as mx

    get_model = provider_get_model()
    ctx = mx.cpu()
    net_kwargs = {"pretrained": False, "ctx": ctx, "classes": args.classes}
    net = get_model(args.model, **net_kwargs)
    # Initialize first so the no-network path is explicit and checkpoint loads
    # cannot leave an uninitialized parameter behind.
    net.initialize(mx.init.MSRAPrelu(), ctx=ctx)
    if args.checkpoint:
        if not os.path.isfile(args.checkpoint):
            raise FileNotFoundError(args.checkpoint)
        net.load_parameters(args.checkpoint, ctx=ctx, ignore_extra=False)
    net.cast("float32")

    x = mx.nd.array(make_input(args), ctx=ctx, dtype="float32")
    with mx.autograd.predict_mode():
        logits = net(x)
    shape = tuple(int(dimension) for dimension in logits.shape)
    if len(shape) != 2 or shape[0] != 1:
        raise AssertionError("expected rank-2 output with batch size one, got {}".format(shape))
    if shape[1] != expected_classes:
        raise AssertionError("expected {} classes, got {}".format(expected_classes, shape[1]))

    probabilities = mx.nd.softmax(logits, axis=1).asnumpy()[0]
    top_k = min(args.top_k, len(probabilities))
    indices = np.argsort(probabilities)[::-1][:top_k]
    parameter_count = sum(
        int(np.prod(parameter.shape))
        for parameter in net.collect_params().values()
        if parameter.shape is not None and parameter.grad_req != "null"
    )
    print("input_shape={}".format(tuple(int(dimension) for dimension in x.shape)))
    print("output_shape={}".format(shape))
    print("device={}".format(ctx))
    print("parameter_count={}".format(parameter_count))
    print("topk={}".format(repr([(int(index), float(probabilities[index])) for index in indices])))


if __name__ == "__main__":
    main()
