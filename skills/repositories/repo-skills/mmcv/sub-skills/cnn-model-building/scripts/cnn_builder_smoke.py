#!/usr/bin/env python3
"""CPU-safe smoke checks for MMCV CNN layer builders and modules."""

from __future__ import annotations

import argparse
import io
import sys
from typing import Callable, Type


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build representative mmcv.cnn layers/modules on CPU, run tiny "
            "forward checks, and report common dependency or config errors."
        )
    )
    parser.add_argument(
        "--check-errors",
        action="store_true",
        help="also exercise expected invalid config failures",
    )
    parser.add_argument(
        "--check-flops",
        action="store_true",
        help="also run get_model_complexity_info on a tiny model",
    )
    parser.add_argument(
        "--skip-forward",
        action="store_true",
        help="build layers but skip tensor forward checks",
    )
    return parser.parse_args()


def require_imports():
    try:
        import torch
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "ERROR: PyTorch is required for mmcv.cnn. Install or activate an "
            "environment with torch before running this smoke check."
        ) from exc

    try:
        import mmcv
        import mmcv.cnn as cnn
    except ModuleNotFoundError as exc:
        missing = exc.name or "unknown module"
        if missing.startswith("mmcv"):
            raise SystemExit(
                "ERROR: MMCV is not importable as 'mmcv'. Install mmcv-lite "
                "or full mmcv before running this smoke check."
            ) from exc
        raise

    return torch, mmcv, cnn


def check_shape(name: str, actual: tuple[int, ...], expected: tuple[int, ...]) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected shape {expected}, got {actual}")


def expect_error(label: str, exc_type: Type[BaseException], fn: Callable[[], object]) -> str:
    try:
        fn()
    except exc_type as exc:
        return f"{label}: got expected {exc_type.__name__}: {exc}"
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise AssertionError(
            f"{label}: expected {exc_type.__name__}, got {type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError(f"{label}: expected {exc_type.__name__}, but no error was raised")


def run_build_checks(torch, cnn, skip_forward: bool) -> list[str]:
    messages: list[str] = []

    conv = cnn.build_conv_layer(
        dict(type="Conv2d"), in_channels=3, out_channels=4, kernel_size=3, padding=1
    )
    norm_name, norm = cnn.build_norm_layer(dict(type="BN"), 4)
    act = cnn.build_activation_layer(dict(type="ReLU"))
    pad = cnn.build_padding_layer(dict(type="reflect"), 1)
    upsample = cnn.build_upsample_layer(dict(type="nearest", scale_factor=2))
    plugin_name, plugin = cnn.build_plugin_layer(
        dict(type="ContextBlock", ratio=0.25, pooling_type="avg"), in_channels=4
    )

    messages.append(f"built conv={conv.__class__.__name__}")
    messages.append(f"built norm={norm_name}:{norm.__class__.__name__}")
    messages.append(f"built activation={act.__class__.__name__}")
    messages.append(f"built padding={pad.__class__.__name__}")
    messages.append(f"built upsample={upsample.__class__.__name__}")
    messages.append(f"built plugin={plugin_name}:{plugin.__class__.__name__}")

    conv_module = cnn.ConvModule(
        3,
        4,
        kernel_size=3,
        padding=1,
        norm_cfg=dict(type="BN"),
        act_cfg=dict(type="ReLU"),
    )
    depthwise = cnn.DepthwiseSeparableConvModule(
        4, 6, kernel_size=3, padding=1, norm_cfg=dict(type="BN")
    )
    scale = cnn.Scale(2.0)
    nonlocal_block = cnn.NonLocal2d(4, mode="embedded_gaussian")
    linear = cnn.Linear(6, 2)
    pool = cnn.MaxPool2d(2)

    messages.append("built ConvModule, DepthwiseSeparableConvModule, Scale, NonLocal2d, Linear, MaxPool2d")

    if skip_forward:
        return messages

    torch.manual_seed(0)
    x = torch.randn(1, 3, 8, 8)
    y = conv_module(x)
    check_shape("ConvModule", tuple(y.shape), (1, 4, 8, 8))
    messages.append("ConvModule forward shape ok")

    z = depthwise(y)
    check_shape("DepthwiseSeparableConvModule", tuple(z.shape), (1, 6, 8, 8))
    messages.append("DepthwiseSeparableConvModule forward shape ok")

    padded = pad(torch.randn(1, 3, 4, 4))
    check_shape("padding", tuple(padded.shape), (1, 3, 6, 6))
    upsampled = upsample(torch.randn(1, 3, 4, 4))
    check_shape("upsample", tuple(upsampled.shape), (1, 3, 8, 8))
    messages.append("padding and upsample forward shapes ok")

    context_out = plugin(torch.randn(1, 4, 4, 4))
    check_shape("ContextBlock", tuple(context_out.shape), (1, 4, 4, 4))
    nonlocal_out = nonlocal_block(torch.randn(1, 4, 4, 4))
    check_shape("NonLocal2d", tuple(nonlocal_out.shape), (1, 4, 4, 4))
    messages.append("plugin and NonLocal2d forward shapes ok")

    scale_out = scale(torch.ones(1, 1, 2, 2))
    if not torch.allclose(scale_out, torch.full_like(scale_out, 2.0)):
        raise AssertionError("Scale did not multiply by the initialized factor")
    linear_out = linear(torch.randn(1, 6))
    check_shape("Linear", tuple(linear_out.shape), (1, 2))
    pool_out = pool(torch.randn(1, 3, 8, 8))
    check_shape("MaxPool2d", tuple(pool_out.shape), (1, 3, 4, 4))
    messages.append("Scale, Linear, and MaxPool2d checks ok")

    fused_source = torch.nn.Sequential(
        cnn.ConvModule(3, 4, 3, padding=1, norm_cfg=dict(type="BN"))
    ).eval()
    fused = cnn.fuse_conv_bn(fused_source)
    fused_out = fused(torch.randn(1, 3, 8, 8))
    check_shape("fuse_conv_bn", tuple(fused_out.shape), (1, 4, 8, 8))
    messages.append("fuse_conv_bn forward shape ok")

    return messages


def run_error_checks(cnn) -> list[str]:
    return [
        expect_error("conv cfg must be dict", TypeError, lambda: cnn.build_conv_layer("Conv2d")),
        expect_error("norm cfg needs type", KeyError, lambda: cnn.build_norm_layer({}, 4)),
        expect_error(
            "GN needs num_groups",
            AssertionError,
            lambda: cnn.build_norm_layer(dict(type="GN"), 4),
        ),
        expect_error(
            "unknown activation",
            KeyError,
            lambda: cnn.build_activation_layer(dict(type="NotAnActivation")),
        ),
        expect_error(
            "invalid ConvModule order",
            AssertionError,
            lambda: cnn.ConvModule(3, 4, 3, order=("conv", "norm", "norm")),
        ),
        expect_error(
            "depthwise groups are internal",
            AssertionError,
            lambda: cnn.DepthwiseSeparableConvModule(3, 4, 3, groups=3),
        ),
    ]


def run_flops_check(torch, cnn) -> list[str]:
    model = torch.nn.Sequential(
        torch.nn.Conv2d(3, 4, 3, padding=1),
        torch.nn.ReLU(),
        torch.nn.AdaptiveAvgPool2d((1, 1)),
        torch.nn.Flatten(),
        torch.nn.Linear(4, 2),
    )
    stream = io.StringIO()
    flops, params = cnn.get_model_complexity_info(
        model,
        (3, 8, 8),
        print_per_layer_stat=False,
        as_strings=False,
        ost=stream,
    )
    if flops <= 0 or params <= 0:
        raise AssertionError(f"Expected positive FLOPs and params, got {flops}, {params}")
    return [f"complexity ok: flops={flops}, params={params}"]


def main() -> int:
    args = parse_args()
    torch, mmcv, cnn = require_imports()

    messages = [
        f"mmcv import ok: version={getattr(mmcv, '__version__', 'unknown')}",
        f"torch import ok: version={getattr(torch, '__version__', 'unknown')}",
    ]
    messages.extend(run_build_checks(torch, cnn, args.skip_forward))
    if args.check_errors:
        messages.extend(run_error_checks(cnn))
    if args.check_flops:
        messages.extend(run_flops_check(torch, cnn))

    print("MMCV CNN builder smoke checks passed")
    for message in messages:
        print(f"- {message}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
