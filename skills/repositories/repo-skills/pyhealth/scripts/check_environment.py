#!/usr/bin/env python3
"""Read-only PyHealth, optional-extra, and device probe.

Usage: python check_environment.py [--json]
It never downloads data, model weights, mappings, or corpora.
"""
import argparse
import importlib
import importlib.metadata
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args()
    result = {"distribution": None, "imports": {}, "optional": {}, "torch": {}}
    try:
        result["distribution"] = importlib.metadata.version("pyhealth")
    except importlib.metadata.PackageNotFoundError:
        result["distribution"] = "not-installed"
    for name in ("pyhealth", "torch", "numpy", "sklearn"):
        try:
            module = importlib.import_module(name)
            result["imports"][name] = getattr(module, "__version__", "ok")
        except Exception as exc:
            result["imports"][name] = f"error: {type(exc).__name__}: {exc}"
    for name in ("torch_geometric", "nltk", "rapidfuzz", "rouge_score"):
        try:
            importlib.import_module(name)
            result["optional"][name] = "available"
        except Exception as exc:
            result["optional"][name] = f"unavailable: {type(exc).__name__}: {exc}"
    try:
        import torch
        result["torch"] = {"version": torch.__version__, "cuda": bool(torch.cuda.is_available())}
        if torch.cuda.is_available():
            result["torch"]["device"] = torch.cuda.get_device_name(0)
    except Exception as exc:
        result["torch"] = {"error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, indent=2) if args.json else result)
    return 0 if result["distribution"] != "not-installed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
