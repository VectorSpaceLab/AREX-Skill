#!/usr/bin/env python3
"""Run a tiny, synthetic, download-free ST-GCN forward check.

See [the recognition skill](../SKILL.md), [API reference](../references/api-reference.md),
and [troubleshooting](../references/troubleshooting.md). This script imports the
installed package only; it does not locate a checkout, read a config, load a
checkpoint, access a dataset, or run native training/evaluation.
"""

from __future__ import print_function

import argparse
import sys


JOINTS = {
    "openpose": 18,
    "ntu-rgb+d": 25,
    "ntu_edge": 24,
    "coco": 17,
}


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny synthetic ST-GCN import/graph/forward smoke. "
            "No dataset, checkpoint, or download is used."
        )
    )
    parser.add_argument(
        "--device",
        default="auto",
        help="auto (default), cpu, cuda, or a CUDA device such as cuda:0",
    )
    parser.add_argument(
        "--layout",
        choices=sorted(JOINTS),
        default="openpose",
        help="graph layout; the synthetic V dimension follows this layout",
    )
    parser.add_argument(
        "--strategy",
        choices=("uniform", "distance", "spatial"),
        default="uniform",
        help="graph partition strategy",
    )
    parser.add_argument("--num-class", type=int, default=4, help="classifier output width")
    parser.add_argument(
        "--sequence-length", type=int, default=8, help="small synthetic T dimension"
    )
    parser.add_argument("--batch-size", type=int, default=1, help="synthetic N dimension")
    parser.add_argument("--persons", type=int, default=1, help="synthetic M dimension")
    parser.add_argument("--in-channels", type=int, default=3, help="synthetic C dimension")
    return parser


def resolve_device(requested, torch):
    if requested == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        print(
            "WARNING: CUDA is unavailable; using CPU for a limited API smoke. "
            "This does not verify the CUDA/native-extension gate.",
            file=sys.stderr,
        )
        return torch.device("cpu")

    try:
        device = torch.device(requested)
    except Exception as exc:
        raise RuntimeError(
            "invalid --device {!r}; use auto, cpu, cuda, or cuda:N ({})".format(
                requested, exc
            )
        )
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA was requested but torch.cuda.is_available() is false. "
            "Check the installed PyTorch CUDA runtime, driver, and visible device; "
            "use --device cpu only for a limited API smoke."
        )
    return device


def main(argv=None):
    args = build_parser().parse_args(argv)
    for name in ("num_class", "sequence_length", "batch_size", "persons", "in_channels"):
        if getattr(args, name) <= 0:
            print("ERROR: --{} must be positive".format(name.replace("_", "-")), file=sys.stderr)
            return 2

    try:
        import torch
    except Exception as exc:
        print(
            "ERROR: PyTorch could not be imported ({}: {}). Install a compatible "
            "PyTorch environment before running this smoke.".format(type(exc).__name__, exc),
            file=sys.stderr,
        )
        return 2

    try:
        # Import the public model implementation after argument parsing so --help
        # remains useful even when the optional runtime is not installed.
        from mmskeleton.models.backbones.st_gcn_aaai18 import ST_GCN_18
    except Exception as exc:
        print(
            "ERROR: ST_GCN_18 could not be imported ({}: {}). This smoke needs "
            "the installed mmskeleton package and a compatible torch/backend "
            "environment. Check package imports and native-extension messages; "
            "nothing was downloaded.".format(type(exc).__name__, exc),
            file=sys.stderr,
        )
        return 2

    device = None
    try:
        device = resolve_device(args.device, torch)
        model = ST_GCN_18(
            in_channels=args.in_channels,
            num_class=args.num_class,
            edge_importance_weighting=True,
            graph_cfg={"layout": args.layout, "strategy": args.strategy},
        ).to(device)
        model.eval()

        node_count = JOINTS[args.layout]
        inputs = torch.randn(
            args.batch_size,
            args.in_channels,
            args.sequence_length,
            node_count,
            args.persons,
            device=device,
        )
        with torch.no_grad():
            output = model(inputs)

        expected = (args.batch_size, args.num_class)
        actual = tuple(output.shape)
        if actual != expected:
            raise AssertionError("expected output shape {}, got {}".format(expected, actual))
        if not bool(torch.isfinite(output).all().item()):
            raise AssertionError("output contains NaN or infinite values")

        print(
            "ST-GCN smoke passed: device={}, layout={}, strategy={}, input={}, "
            "output={}, finite=True".format(
                device,
                args.layout,
                args.strategy,
                tuple(inputs.shape),
                actual,
            )
        )
        if device.type != "cuda":
            print(
                "Note: this result verifies model construction/forward only; "
                "CUDA and native NMS readiness remain unverified."
            )
        return 0
    except Exception as exc:
        print(
            "ERROR: ST-GCN smoke failed ({}: {}).".format(type(exc).__name__, exc),
            file=sys.stderr,
        )
        if "cuda" in str(exc).lower() or (
            "device" in str(exc).lower() and device is not None and device.type == "cuda"
        ):
            print(
                "CUDA guidance: compare torch.version.cuda with the driver and "
                "nvcc/toolchain used for extensions, check visible GPU memory, "
                "and retry the tiny smoke after alignment. Do not diagnose this "
                "with a long training/evaluation run.",
                file=sys.stderr,
            )
        return 2


if __name__ == "__main__":
    sys.exit(main())
