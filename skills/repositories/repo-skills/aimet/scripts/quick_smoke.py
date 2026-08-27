#!/usr/bin/env python3
"""Tiny AIMET installed-package smoke checks.

This script is self-contained: it does not import from an AIMET source checkout.
It verifies imports plus a minimal PyTorch QuantSim and/or ONNX QuantSim
calibration flow with synthetic data.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from typing import Iterable


def _print_header(title: str) -> None:
    print(f"\n== {title} ==")


def _torch_device(requested: str):
    import torch

    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def torch_smoke(device_request: str) -> None:
    _print_header("Torch smoke")
    import torch
    import torch.nn as nn
    import aimet_torch

    class Tiny(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.fc = nn.Linear(4, 3)
            self.relu = nn.ReLU()

        def forward(self, x):
            return self.relu(self.fc(x))

    device = _torch_device(device_request)
    print("aimet_torch", aimet_torch.__version__)
    print("torch", torch.__version__, "cuda", torch.version.cuda, "device", device)
    if device.type == "cuda":
        torch.empty((1,), device=device)
        print("cuda_device", torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))

    model = Tiny().eval().to(device)
    dummy_input = torch.randn(2, 4, device=device)
    sim = aimet_torch.QuantizationSimModel(
        model,
        dummy_input=dummy_input,
        default_param_bw=8,
        default_output_bw=8,
    )
    sim.compute_encodings(lambda m, _: m(dummy_input), None)
    output = sim.model(dummy_input)
    print("torch_quantsim_ok", tuple(output.shape))


def onnx_smoke(use_cuda_provider: bool) -> None:
    _print_header("ONNX smoke")
    import numpy as np
    import onnx
    import onnxruntime as ort
    import torch
    import torch.nn as nn
    import aimet_onnx

    providers: list[str] = ["CPUExecutionProvider"]
    available = ort.get_available_providers()
    if use_cuda_provider:
        if "CUDAExecutionProvider" not in available:
            raise RuntimeError(
                f"CUDAExecutionProvider requested but unavailable; providers={available}"
            )
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

    class Tiny(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.fc = nn.Linear(4, 3)
            self.relu = nn.ReLU()

        def forward(self, x):
            return self.relu(self.fc(x))

    print("aimet_onnx", aimet_onnx.__version__)
    print("onnxruntime", ort.__version__, "providers", providers, "available", available)

    model = Tiny().eval().cpu()
    dummy_input = torch.randn(2, 4)
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, "tiny.onnx")
        torch.onnx.export(
            model,
            dummy_input,
            model_path,
            input_names=["input"],
            output_names=["output"],
            dynamo=False,
        )
        onnx_model = onnx.load_model(model_path)
        sim = aimet_onnx.QuantizationSimModel(
            onnx_model,
            param_type=aimet_onnx.int8,
            activation_type=aimet_onnx.int8,
            providers=providers,
        )
        sim.compute_encodings([{"input": dummy_input.numpy().astype(np.float32)}])
        result = sim.session.run(None, {"input": dummy_input.numpy().astype(np.float32)})
        print("onnx_quantsim_ok", [tuple(x.shape) for x in result])


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--framework",
        choices=["torch", "onnx", "both"],
        default="both",
        help="Which AIMET package surface to smoke-test.",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Torch device for the PyTorch smoke check.",
    )
    parser.add_argument(
        "--onnx-cuda",
        action="store_true",
        help="Require ONNX Runtime CUDAExecutionProvider for the ONNX smoke check.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.framework in {"torch", "both"}:
            torch_smoke(args.device)
        if args.framework in {"onnx", "both"}:
            onnx_smoke(args.onnx_cuda)
    except Exception as exc:  # pragma: no cover - diagnostic script
        print(f"SMOKE_FAILED: {exc}", file=sys.stderr)
        return 1
    print("\nAIMET smoke checks completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
