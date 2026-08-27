#!/usr/bin/env python3
"""Tiny Gluon smoke check for optional ResNeSt MXNet support.

The default path is intentionally safe: CPU context, random input, and
pretrained=False. The script only reaches the network/cache path when
--pretrained is explicitly supplied.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List

LOCAL_MODELS = [
    "resnest50",
    "resnest101",
    "resnest200",
    "resnest269",
    "resnest50_fast_1s1x64d",
    "resnest50_fast_2s1x64d",
    "resnest50_fast_4s1x64d",
    "resnest50_fast_1s2x40d",
    "resnest50_fast_2s2x40d",
    "resnest50_fast_4s2x40d",
    "resnest50_fast_1s4x24d",
]


def positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:  # pragma: no cover - argparse formatting
        raise argparse.ArgumentTypeError(f"expected an integer, got {text!r}") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a tiny optional MXNet Gluon ResNeSt smoke check.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", default="resnest50", choices=LOCAL_MODELS,
                        help="Local Gluon model builder to load.")
    parser.add_argument("--batch-size", type=positive_int, default=1,
                        help="Random input batch size.")
    parser.add_argument("--image-size", type=positive_int, default=64,
                        help="Square random input size.")
    parser.add_argument("--classes", type=positive_int, default=1000,
                        help="Classifier output classes.")
    parser.add_argument("--ctx", default="cpu",
                        help="MXNet context or comma-separated contexts such as cpu, cpu:0, gpu:0, or gpu:0,gpu:1.")
    parser.add_argument("--pretrained", action="store_true",
                        help="Load pretrained parameters from the model cache root.")
    parser.add_argument("--root", default="~/.mxnet/models",
                        help="Parameter cache root used when --pretrained is set.")
    parser.add_argument("--dilation", type=positive_int, default=1,
                        help="Optional network dilation passed into the builder.")
    parser.add_argument("--dtype", default="float32",
                        help="Forward-pass dtype.")
    parser.add_argument("--list-models", action="store_true",
                        help="Print the bundled local Gluon model names and exit.")
    parser.add_argument("--hybridize", action="store_true", default=True,
                        help="Hybridize the network before the forward pass.")
    parser.add_argument("--no-hybridize", action="store_false", dest="hybridize",
                        help="Disable hybridization for debugging.")
    return parser


def parse_contexts(mx_module, ctx_text: str):
    ctxs = []
    for raw in ctx_text.split(","):
        token = raw.strip().lower()
        if not token:
            continue
        prefix, _, suffix = token.partition(":")
        index = int(suffix) if suffix else 0
        if prefix == "cpu":
            ctxs.append(mx_module.cpu(index))
            continue
        if prefix in {"gpu", "cuda"}:
            visible = mx_module.context.num_gpus()
            if visible <= index:
                raise ValueError(
                    f"requested GPU context {token!r} is unavailable; only {visible} GPU(s) are visible"
                )
            ctxs.append(mx_module.gpu(index))
            continue
        raise ValueError(f"unsupported context token: {raw!r}")
    if not ctxs:
        raise ValueError("at least one MXNet context must be provided")
    return ctxs


def emit(payload):
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: List[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_models:
        print("\n".join(LOCAL_MODELS))
        return 0

    if args.pretrained:
        print(
            f"warning: --pretrained may read or download parameters under {os.path.expanduser(args.root)!r}",
            file=sys.stderr,
        )
        if args.classes != 1000:
            print(
                "warning: pretrained ImageNet parameters in this repo were published for classes=1000; "
                "other class counts may fail to load",
                file=sys.stderr,
            )

    try:
        import mxnet as mx
        from mxnet import gluon
        from resnest.gluon import get_model
    except ModuleNotFoundError as exc:
        if exc.name == "mxnet":
            emit({
                "status": "missing_optional_dependency",
                "ok": False,
                "model": args.model,
                "batch_size": args.batch_size,
                "image_size": args.image_size,
                "classes": args.classes,
                "ctx_requested": args.ctx,
                "pretrained": bool(args.pretrained),
                "message": "MXNet is optional for ResNeSt Gluon and is not importable in this environment.",
            })
            return 0
        emit({
            "status": "mxnet_import_error",
            "ok": False,
            "model": args.model,
            "batch_size": args.batch_size,
            "image_size": args.image_size,
            "classes": args.classes,
            "ctx_requested": args.ctx,
            "pretrained": bool(args.pretrained),
            "missing_module": exc.name,
            "message": "MXNet import failed because one of its dependencies is missing.",
        })
        return 2
    except Exception as exc:
        emit({
            "status": "mxnet_import_error",
            "ok": False,
            "model": args.model,
            "batch_size": args.batch_size,
            "image_size": args.image_size,
            "classes": args.classes,
            "ctx_requested": args.ctx,
            "pretrained": bool(args.pretrained),
            "error_type": exc.__class__.__name__,
            "error": str(exc),
            "message": "MXNet import failed; check the Python wheel and native backend compatibility.",
        })
        return 2

    try:
        ctxs = parse_contexts(mx, args.ctx)
    except Exception as exc:
        emit({
            "status": "argument_error",
            "ok": False,
            "mxnet_available": True,
            "model": args.model,
            "batch_size": args.batch_size,
            "image_size": args.image_size,
            "classes": args.classes,
            "ctx_requested": args.ctx,
            "pretrained": bool(args.pretrained),
            "message": str(exc),
        })
        return 2

    try:
        net = get_model(
            args.model,
            pretrained=bool(args.pretrained),
            root=args.root,
            ctx=ctxs[0] if len(ctxs) == 1 else ctxs,
            classes=args.classes,
            dilation=args.dilation,
        )
        if not args.pretrained:
            net.initialize(ctx=ctxs[0] if len(ctxs) == 1 else ctxs)
        if args.hybridize:
            net.hybridize()
        x = mx.nd.random.uniform(shape=(args.batch_size, 3, args.image_size, args.image_size), ctx=mx.cpu())
        shards = gluon.utils.split_and_load(x, ctx_list=ctxs, batch_axis=0, even_split=False)
        outputs = [net(shard.astype(args.dtype, copy=False)) for shard in shards]
    except Exception as exc:
        emit({
            "status": "execution_error",
            "ok": False,
            "mxnet_available": True,
            "resnest_gluon_available": True,
            "model": args.model,
            "batch_size": args.batch_size,
            "image_size": args.image_size,
            "classes": args.classes,
            "ctx": [str(ctx) for ctx in ctxs],
            "pretrained": bool(args.pretrained),
            "error_type": exc.__class__.__name__,
            "error": str(exc),
            "message": "Gluon model construction or forward execution failed.",
        })
        return 2

    emit({
        "status": "ok",
        "ok": True,
        "mxnet_available": True,
        "resnest_gluon_available": True,
        "model": args.model,
        "batch_size": args.batch_size,
        "image_size": args.image_size,
        "classes": args.classes,
        "ctx": [str(ctx) for ctx in ctxs],
        "pretrained": bool(args.pretrained),
        "dtype": args.dtype,
        "input_shape": [args.batch_size, 3, args.image_size, args.image_size],
        "output_shapes": [list(out.shape) for out in outputs],
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
