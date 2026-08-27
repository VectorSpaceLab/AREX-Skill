#!/usr/bin/env python3
"""Print NanoDet FLOPs when the optional helper dependency is available."""

from __future__ import annotations

import argparse

import torch

from nanodet.model.arch import build_model
from nanodet.util import cfg, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Print NanoDet FLOPs when the optional helper dependency is available.",
    )
    parser.add_argument("cfg", type=str, help="Path to a YAML config file.")
    parser.add_argument("--input_shape", type=str, default=None, help="Model input shape as width,height.")
    return parser.parse_args()


def main(config, input_shape=(320, 320)):
    model = build_model(config.model)
    try:
        import mobile_cv.lut.lib.pt.flops_utils as flops_utils
    except ImportError:
        print("mobile-cv is not installed. Skip flops calculation.")
        return
    first_batch = torch.rand((1, 3, input_shape[0], input_shape[1]))
    input_args = (first_batch,)
    flops_utils.print_model_flops(model, input_args)


def entrypoint() -> None:
    args = parse_args()
    load_config(cfg, args.cfg)
    if args.input_shape is None:
        input_shape = cfg.data.train.input_size
    else:
        input_shape = tuple(map(int, args.input_shape.split(",")))
        assert len(input_shape) == 2
    main(config=cfg, input_shape=input_shape)


if __name__ == "__main__":
    entrypoint()
