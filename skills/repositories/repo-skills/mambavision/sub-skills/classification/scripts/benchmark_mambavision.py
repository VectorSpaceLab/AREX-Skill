#!/usr/bin/env python3
"""Safer MambaVision throughput/FLOPs helper.

This helper keeps downloads off by default, fixes the original batch-size bug by
using parsed arguments consistently, guards CUDA use, and treats ptflops as an
optional dependency.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from importlib import metadata
from pathlib import Path
from typing import Any


MODEL_NAMES = (
    "mamba_vision_T",
    "mamba_vision_T2",
    "mamba_vision_S",
    "mamba_vision_B",
    "mamba_vision_B_21k",
    "mamba_vision_L",
    "mamba_vision_L_21k",
    "mamba_vision_L2",
    "mamba_vision_L2_512_21k",
    "mamba_vision_L3_256_21k",
    "mamba_vision_L3_512_21k",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark MambaVision random-input inference with safe defaults.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", default="mamba_vision_T", choices=MODEL_NAMES, help="MambaVision factory name.")
    parser.add_argument(
        "--device",
        default="auto",
        choices=("auto", "cuda", "cpu"),
        help="Benchmark device. 'auto' selects CUDA when available, otherwise CPU.",
    )
    parser.add_argument("--resolution", type=int, default=224, help="Square input resolution used when --height/--width are omitted.")
    parser.add_argument("--height", type=int, default=None, help="Override input height.")
    parser.add_argument("--width", type=int, default=None, help="Override input width.")
    parser.add_argument("--channels", type=int, default=3, help="Input channels; released checkpoints expect 3.")
    parser.add_argument("--bs", "--batch-size", dest="batch_size", type=int, default=1, help="Batch size.")
    parser.add_argument("--warmup", type=int, default=5, help="Warmup iterations before timing.")
    parser.add_argument("--runs", type=int, default=20, help="Timed iterations.")
    parser.add_argument("--seed", type=int, default=0, help="Torch random seed for dummy input.")
    parser.add_argument("--channels-last", "--channel-last", action="store_true", help="Use channels-last memory format.")
    parser.add_argument("--amp", action="store_true", help="Use torch autocast during forward timing. CUDA only.")
    parser.add_argument(
        "--amp-dtype",
        choices=("float16", "bfloat16"),
        default="float16",
        help="Autocast dtype when --amp is enabled.",
    )
    parser.add_argument("--flops", action="store_true", help="Attempt MACs/FLOPs with optional ptflops import.")
    parser.add_argument(
        "--pretrained",
        action="store_true",
        help="Opt in to pretrained weight loading. May download to --model-path if the file is absent.",
    )
    parser.add_argument(
        "--model-path",
        default="",
        help="Destination/source file used by the factory when --pretrained is set. Required with --pretrained for explicit cache behavior.",
    )
    parser.add_argument(
        "--checkpoint-path",
        default="",
        help="Optional local checkpoint loaded after model construction.",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional file to write benchmark summary JSON. Parent directory must already exist.",
    )
    return parser.parse_args()


def die(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def pick_device(requested: str, torch_module: Any):
    if requested == "cuda":
        if not torch_module.cuda.is_available():
            die("CUDA was requested but torch.cuda.is_available() is False.")
        return torch_module.device("cuda")
    if requested == "auto":
        if torch_module.cuda.is_available():
            return torch_module.device("cuda")
        warn("CUDA is unavailable; falling back to CPU debug timing. CPU numbers are not comparable to published throughput.")
        return torch_module.device("cpu")
    return torch_module.device("cpu")


def maybe_sync(torch_module: Any, device: Any) -> None:
    if device.type == "cuda":
        torch_module.cuda.synchronize(device)


def measure_flops(model: Any, input_shape: tuple[int, int, int]) -> dict[str, Any]:
    try:
        from ptflops import get_model_complexity_info
    except Exception as exc:  # pragma: no cover - optional dependency
        return {"available": False, "error": f"ptflops import failed: {exc}"}

    try:
        macs, params = get_model_complexity_info(
            model,
            input_shape,
            as_strings=False,
            print_per_layer_stat=False,
            verbose=False,
        )
        return {"available": True, "macs": int(macs), "params": int(params)}
    except Exception as exc:  # pragma: no cover - model/tool-version dependent
        return {"available": False, "error": f"ptflops measurement failed: {exc}"}


def main() -> int:
    args = parse_args()
    height = args.height if args.height is not None else args.resolution
    width = args.width if args.width is not None else args.resolution

    for name, value in (
        ("resolution", args.resolution),
        ("height", height),
        ("width", width),
        ("channels", args.channels),
        ("batch size", args.batch_size),
    ):
        if value <= 0:
            die(f"--{name.replace(' ', '-')} must be a positive integer.")
    if args.warmup < 0 or args.runs <= 0:
        die("--warmup must be >= 0 and --runs must be > 0.")
    if args.pretrained and not args.model_path:
        die("--pretrained can download weights; pass an explicit --model-path to make cache behavior intentional.")
    if args.checkpoint_path and not Path(args.checkpoint_path).is_file():
        die(f"--checkpoint-path does not exist or is not a file: {args.checkpoint_path}")
    if args.output_json and not Path(args.output_json).parent.exists():
        die(f"Parent directory for --output-json does not exist: {Path(args.output_json).parent}")

    try:
        import torch
        from mambavision import create_model
    except Exception as exc:  # pragma: no cover - user environment dependent
        die(f"Failed to import torch/mambavision: {exc}")

    device = pick_device(args.device, torch)
    if args.amp and device.type != "cuda":
        warn("--amp was requested on a non-CUDA device; disabling autocast.")
        args.amp = False
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.benchmark = True

    torch.manual_seed(args.seed)

    model_kwargs: dict[str, Any] = {}
    if args.channels != 3:
        model_kwargs["in_chans"] = args.channels
    if args.model_path:
        model_kwargs["model_path"] = args.model_path
    if args.checkpoint_path:
        model_kwargs["checkpoint_path"] = args.checkpoint_path

    model = create_model(args.model, pretrained=args.pretrained, **model_kwargs)
    model.eval()

    param_count = sum(p.numel() for p in model.parameters())
    flops_result = measure_flops(model, (args.channels, height, width)) if args.flops else {"available": False, "skipped": True}

    model = model.to(device)
    input_data = torch.randn(args.batch_size, args.channels, height, width, device=device)
    if args.channels_last:
        model = model.to(memory_format=torch.channels_last)
        input_data = input_data.contiguous(memory_format=torch.channels_last)

    amp_dtype = torch.float16 if args.amp_dtype == "float16" else torch.bfloat16

    def forward_once():
        with torch.inference_mode():
            if args.amp:
                with torch.autocast(device_type="cuda", dtype=amp_dtype):
                    return model(input_data)
            return model(input_data)

    for _ in range(args.warmup):
        _ = forward_once()
    maybe_sync(torch, device)

    latencies = []
    for _ in range(args.runs):
        maybe_sync(torch, device)
        start = time.perf_counter()
        output = forward_once()
        maybe_sync(torch, device)
        latencies.append(time.perf_counter() - start)

    if tuple(output.shape)[0] != args.batch_size:
        die(f"Unexpected output batch dimension: {tuple(output.shape)}")
    finite = bool(torch.isfinite(output).all().item())
    if not finite:
        die("Benchmark output contains NaN or Inf values.")

    total_time = sum(latencies)
    mean_latency = total_time / len(latencies)
    median_latency = statistics.median(latencies)
    result = {
        "status": "ok",
        "model": args.model,
        "package_version": "unknown",
        "device": str(device),
        "cuda_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "input_shape": [args.batch_size, args.channels, height, width],
        "output_shape": list(output.shape),
        "output_finite": finite,
        "param_count": int(param_count),
        "flops": flops_result,
        "warmup": args.warmup,
        "runs": args.runs,
        "mean_latency_s": mean_latency,
        "median_latency_s": median_latency,
        "throughput_img_s_mean": args.batch_size / mean_latency,
        "throughput_img_s_median": args.batch_size / median_latency,
        "amp": bool(args.amp),
        "amp_dtype": args.amp_dtype if args.amp else None,
        "channels_last": bool(args.channels_last),
        "pretrained": bool(args.pretrained),
        "checkpoint_path_used": bool(args.checkpoint_path),
    }
    try:
        result["package_version"] = metadata.version("mambavision")
    except metadata.PackageNotFoundError:
        pass

    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output_json:
        Path(args.output_json).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
