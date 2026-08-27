#!/usr/bin/env python3
"""CPU-safe bitsandbytes quantized module/signature smoke check.

By default this script imports bitsandbytes, validates key public signatures, and
constructs quantized modules on CPU without running quantized kernels. Use
--device and --run-forward only when the selected backend is available.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from typing import Any


def _signature_text(obj: Any) -> str:
    return str(inspect.signature(obj))


def _assert_signature_contains(name: str, signature: str, expected_parts: tuple[str, ...]) -> None:
    missing = [part for part in expected_parts if part not in signature]
    if missing:
        raise AssertionError(f"{name} signature {signature!r} is missing {missing!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device",
        default="cpu",
        help="Device used for optional .to(device)/forward checks. Default only constructs on CPU.",
    )
    parser.add_argument(
        "--run-forward",
        action="store_true",
        help="Run tiny forwards after moving modules to --device. Requires native kernels for that backend.",
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of text.")
    args = parser.parse_args()

    import torch
    import bitsandbytes as bnb
    import bitsandbytes.functional as F

    signatures = {
        "Linear8bitLt": _signature_text(bnb.nn.Linear8bitLt),
        "Linear4bit": _signature_text(bnb.nn.Linear4bit),
        "LinearNF4": _signature_text(bnb.nn.LinearNF4),
        "LinearFP4": _signature_text(bnb.nn.LinearFP4),
        "Embedding8bit": _signature_text(bnb.nn.Embedding8bit),
        "Embedding4bit": _signature_text(bnb.nn.Embedding4bit),
        "Params4bit": _signature_text(bnb.nn.Params4bit),
        "Int8Params": _signature_text(bnb.nn.Int8Params),
        "QuantState": _signature_text(F.QuantState),
        "quantize_4bit": _signature_text(F.quantize_4bit),
        "dequantize_4bit": _signature_text(F.dequantize_4bit),
        "int8_vectorwise_quant": _signature_text(F.int8_vectorwise_quant),
        "matmul": _signature_text(bnb.matmul),
        "matmul_4bit": _signature_text(bnb.matmul_4bit),
    }

    _assert_signature_contains("Linear8bitLt", signatures["Linear8bitLt"], ("input_features", "output_features", "threshold"))
    _assert_signature_contains("Linear4bit", signatures["Linear4bit"], ("compute_dtype", "compress_statistics", "quant_type", "quant_storage"))
    _assert_signature_contains("quantize_4bit", signatures["quantize_4bit"], ("blocksize", "compress_statistics", "quant_type", "quant_storage"))
    _assert_signature_contains("QuantState", signatures["QuantState"], ("absmax", "blocksize", "quant_type"))

    torch.manual_seed(0)
    modules = {
        "linear8": bnb.nn.Linear8bitLt(8, 4, bias=True, has_fp16_weights=False, threshold=0.0),
        "linear4": bnb.nn.Linear4bit(8, 4, bias=True, quant_type="fp4", quant_storage=torch.uint8),
        "linearnf4": bnb.nn.LinearNF4(8, 4, bias=False, quant_storage=torch.uint8),
        "embedding8": bnb.nn.Embedding8bit(16, 64),
        "embedding4": bnb.nn.Embedding4bit(16, 64, quant_type="fp4", quant_storage=torch.uint8),
    }

    summary: dict[str, Any] = {
        "ok": True,
        "torch": torch.__version__,
        "bitsandbytes": getattr(bnb, "__version__", "unknown"),
        "device": args.device,
        "run_forward": args.run_forward,
        "constructed_modules": sorted(modules),
        "signatures": signatures,
        "forward_checks": {},
    }

    if args.run_forward:
        if args.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("--device cuda requested but torch.cuda.is_available() is false")

        device = torch.device(args.device)
        linear_input = torch.randn(2, 8, device=device, dtype=torch.float16 if device.type != "cpu" else torch.float32)
        token_input = torch.tensor([[0, 1, 2], [3, 4, 5]], device=device, dtype=torch.long)

        for name, module in modules.items():
            module = module.to(device)
            if name.startswith("linear"):
                output = module(linear_input)
            else:
                output = module(token_input)
            summary["forward_checks"][name] = {"shape": list(output.shape), "dtype": str(output.dtype)}

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"bitsandbytes {summary['bitsandbytes']} with torch {summary['torch']}")
        print("Validated signatures:")
        for name in sorted(signatures):
            print(f"- {name}{signatures[name]}")
        print("Constructed modules: " + ", ".join(summary["constructed_modules"]))
        if args.run_forward:
            print("Forward checks:")
            for name, check in summary["forward_checks"].items():
                print(f"- {name}: shape={check['shape']} dtype={check['dtype']}")
        else:
            print("Forward checks skipped; pass --run-forward with a supported --device to execute kernels.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
