#!/usr/bin/env python3
"""Print a tiny torch/CUDA readiness summary for LightLLM work."""

from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--require", action="store_true", help="exit nonzero if CUDA is unavailable")
    args = parser.parse_args()

    try:
        import torch
    except Exception as exc:  # pragma: no cover - import failure is the signal
        msg = {"ok": False, "error": f"torch import failed: {exc}"}
        print(json.dumps(msg, indent=2) if args.json else msg["error"])
        return 1

    info = {
        "torch_version": torch.__version__,
        "torch_cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
    }
    if torch.cuda.is_available():
        info["device_name"] = torch.cuda.get_device_name(0)
        info["device_capability"] = torch.cuda.get_device_capability(0)
        probe = torch.empty((1,), device="cuda")
        info["probe_device"] = str(probe.device)
        info["probe_dtype"] = str(probe.dtype)

    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
    else:
        print(f"torch={info['torch_version']} cuda={info['torch_cuda_version']}")
        print(f"cuda_available={info['cuda_available']} device_count={info['device_count']}")
        if info["cuda_available"]:
            print(f"device_name={info['device_name']}")
            print(f"device_capability={info['device_capability']}")
            print(f"probe_device={info['probe_device']} probe_dtype={info['probe_dtype']}")

    if args.require and not info["cuda_available"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
