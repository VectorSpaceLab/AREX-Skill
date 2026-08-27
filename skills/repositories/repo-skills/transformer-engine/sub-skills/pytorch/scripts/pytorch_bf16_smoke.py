#!/usr/bin/env python3
"""Tiny BF16 smoke test for transformer_engine.pytorch.

The script intentionally:
- imports torch before transformer_engine.pytorch for the runtime path,
- sets NVTE_TORCH_COMPILE=0 before the TE import when the variable is unset,
- prints version/device/support facts,
- runs a tiny BF16 Linear forward/backward on CUDA,
- avoids any dependency on the source repository tree.

The command-line help is available even before the optional runtime packages are
loaded because framework imports happen after argument parsing.
"""

from __future__ import annotations

import argparse
import os
from importlib import metadata


def load_torch():
    import torch

    return torch


def load_te():
    if "NVTE_TORCH_COMPILE" not in os.environ:
        os.environ["NVTE_TORCH_COMPILE"] = "0"
        compile_note = "NVTE_TORCH_COMPILE=0 (set before TE import)"
    else:
        compile_note = f"NVTE_TORCH_COMPILE={os.environ['NVTE_TORCH_COMPILE']}"

    import transformer_engine.pytorch as te

    return te, compile_note


def te_distribution_version() -> str:
    for dist_name in ("transformer_engine", "transformer-engine"):
        try:
            return metadata.version(dist_name)
        except metadata.PackageNotFoundError:
            continue
    return "unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transformer Engine BF16 Linear smoke test")
    parser.add_argument("--device", default="cuda", help="CUDA device to run on, e.g. cuda or cuda:0")
    parser.add_argument("--in-features", type=int, default=16, help="Input feature size")
    parser.add_argument("--out-features", type=int, default=32, help="Output feature size")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    return parser.parse_args()


def availability_line(name: str, result: tuple[bool, str]) -> str:
    ok, reason = result
    return f"{name}={ok}" if ok else f"{name}=False ({reason})"


def print_support_facts(te, torch, device, cuda_index: int, compile_note: str) -> None:
    bf16_ok, bf16_reason = te.is_bf16_available(return_reason=True)
    fp8_ok, fp8_reason = te.is_fp8_available(return_reason=True)
    mxfp8_ok, mxfp8_reason = te.is_mxfp8_available(return_reason=True)
    fp8_block_ok, fp8_block_reason = te.is_fp8_block_scaling_available(return_reason=True)
    nvfp4_ok, nvfp4_reason = te.is_nvfp4_available(return_reason=True)

    print(f"transformer-engine={te_distribution_version()}")
    print(f"torch={torch.__version__}")
    print(f"cuda={torch.version.cuda}")
    print(f"device={torch.cuda.get_device_name(cuda_index)} ({device})")
    print(f"compute_capability={torch.cuda.get_device_capability(cuda_index)}")
    print(f"cudnn={te.get_cudnn_version()}")
    print(compile_note)
    print(availability_line("bf16", (bf16_ok, bf16_reason)))
    print(availability_line("fp8", (fp8_ok, fp8_reason)))
    print(availability_line("mxfp8", (mxfp8_ok, mxfp8_reason)))
    print(availability_line("fp8_block_scaling", (fp8_block_ok, fp8_block_reason)))
    print(availability_line("nvfp4", (nvfp4_ok, nvfp4_reason)))

    if not bf16_ok:
        raise SystemExit(f"BF16 is required for this smoke test: {bf16_reason}")


def run_smoke(te, torch, device, in_features: int, out_features: int, batch_size: int) -> None:
    layer = te.Linear(in_features, out_features, bias=True, params_dtype=torch.bfloat16, device=device)
    x = torch.randn(batch_size, in_features, dtype=torch.bfloat16, device=device, requires_grad=True)

    y = layer(x)
    assert y.shape == (batch_size, out_features), f"unexpected output shape: {tuple(y.shape)}"
    assert y.dtype == torch.bfloat16, f"unexpected output dtype: {y.dtype}"

    loss = y.sum()
    loss.backward()

    if device.type == "cuda":
        torch.cuda.synchronize(device)

    grad_dtype = None if x.grad is None else x.grad.dtype
    print(f"smoke=PASS output_shape={tuple(y.shape)} output_dtype={y.dtype} grad_dtype={grad_dtype}")


def main() -> None:
    args = parse_args()
    torch = load_torch()
    device = torch.device(args.device)

    if device.type != "cuda":
        raise SystemExit("This smoke test only supports CUDA devices.")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available on this host.")

    if device.index is None:
        cuda_index = 0
    else:
        cuda_index = device.index
    torch.cuda.set_device(cuda_index)
    device = torch.device(f"cuda:{cuda_index}")

    te, compile_note = load_te()
    print_support_facts(te, torch, device, cuda_index, compile_note)
    run_smoke(te, torch, device, args.in_features, args.out_features, args.batch_size)


if __name__ == "__main__":
    main()
