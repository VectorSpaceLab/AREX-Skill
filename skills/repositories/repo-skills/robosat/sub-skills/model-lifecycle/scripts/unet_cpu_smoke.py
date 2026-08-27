#!/usr/bin/env python3
"""Run a tiny CPU smoke test for robosat.unet.UNet.

This script is intentionally offline-safe: it always constructs UNet with
pretrained=False so that help output and the forward pass do not depend on a
network download.
"""

import argparse


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run a CPU-only UNet smoke test without pretrained weight downloads."
    )
    parser.add_argument("--num-classes", type=int, default=2, help="number of output classes")
    parser.add_argument("--num-filters", type=int, default=32, help="base decoder width")
    parser.add_argument("--height", type=int, default=64, help="input height; must be divisible by 32")
    parser.add_argument("--width", type=int, default=64, help="input width; must be divisible by 32")
    parser.add_argument("--seed", type=int, default=0, help="torch seed for reproducibility")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.num_classes < 1:
        parser.error("--num-classes must be positive")

    if args.height % 32 != 0 or args.width % 32 != 0:
        parser.error("--height and --width must both be divisible by 32")

    try:
        import torch
        from robosat.unet import UNet
    except Exception as exc:
        raise SystemExit("Error: unable to import torch or robosat.unet: {}".format(exc))

    torch.manual_seed(args.seed)

    net = UNet(num_classes=args.num_classes, num_filters=args.num_filters, pretrained=False)
    net.eval()

    with torch.no_grad():
        inputs = torch.zeros(1, 3, args.height, args.width)
        outputs = net(inputs)

    expected = (1, args.num_classes, args.height, args.width)
    actual = tuple(outputs.shape)

    if actual != expected:
        raise SystemExit("Error: expected output shape {}, got {}".format(expected, actual))

    print("UNet CPU smoke passed: {}".format(actual))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
