#!/usr/bin/env python3
"""Tiny PhysicsNeMo ONNX export smoke.

Exports a small linear model with `physicsnemo.deploy.onnx.export_to_onnx_stream`
and optionally runs a tiny onnxruntime inference if the runtime is installed.
"""

from __future__ import annotations

import argparse
import json

import torch
from torch import nn


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--try-ort", action="store_true", help="Try running the exported model with onnxruntime if installed.")
    args = parser.parse_args()

    from physicsnemo.deploy.onnx import export_to_onnx_stream

    model = nn.Linear(4, 2)
    model.eval()
    x = torch.randn(1, 4)
    onnx_bytes = export_to_onnx_stream(model, x)

    payload = {
        "onnx_byte_count": len(onnx_bytes),
        "exported_model": model.__class__.__name__,
    }

    if args.try_ort:
        try:
            import onnxruntime as ort
            session = ort.InferenceSession(onnx_bytes, providers=["CPUExecutionProvider"])
            output = session.run(None, {session.get_inputs()[0].name: x.numpy()})
            payload["ort_status"] = "passed"
            payload["ort_output_shape"] = [list(t.shape) for t in output]
        except Exception as exc:  # pragma: no cover - smoke path only
            payload["ort_status"] = f"SKIP_OR_FAIL: {type(exc).__name__}: {exc}"
    else:
        payload["ort_status"] = "not-run"

    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
