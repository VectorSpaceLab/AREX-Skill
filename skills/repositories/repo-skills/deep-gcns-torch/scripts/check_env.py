#!/usr/bin/env python3
"""Check the portable PyTorch/PyG dependency and optional CUDA contract.

This helper is read-only, safe from any working directory, and does not import
or require the original DeepGCNs checkout. It is useful before a real workflow.
"""
from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe PyTorch, PyG extensions, and optional CUDA.")
    parser.add_argument("--cuda", action="store_true", help="fail unless CUDA is available and a tiny allocation succeeds")
    parser.add_argument("--json", action="store_true", help="emit a JSON result")
    args = parser.parse_args(argv)
    result: dict[str, object] = {"imports": {}, "cuda": {"requested": args.cuda}}
    try:
        import torch
        result["torch"] = torch.__version__
        result["cuda"] = {
            "requested": args.cuda,
            "available": bool(torch.cuda.is_available()),
            "count": int(torch.cuda.device_count()),
            "runtime": torch.version.cuda,
        }
        for name in ("torch_geometric", "torch_scatter", "torch_cluster"):
            try:
                module = __import__(name)
                result["imports"][name] = getattr(module, "__version__", "ok")
            except Exception as exc:  # pragma: no cover - environment dependent
                result["imports"][name] = f"FAIL: {type(exc).__name__}: {exc}"
                raise RuntimeError(f"{name} import failed: {exc}") from exc
        if args.cuda:
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")
            tensor = torch.ones((2, 2), device="cuda")
            result["cuda"]["device"] = torch.cuda.get_device_name(0)
            result["cuda"]["capability"] = torch.cuda.get_device_capability(0)
            result["cuda"]["tiny_allocation"] = bool(torch.isfinite(tensor).all().item())
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        if args.json:
            print(json.dumps(result, sort_keys=True, default=str))
        else:
            print(f"ENV_CHECK_FAILED: {result['error']}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, sort_keys=True, default=str))
    else:
        print("OK environment check")
        print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
