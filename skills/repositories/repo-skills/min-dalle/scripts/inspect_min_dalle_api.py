#!/usr/bin/env python3
"""
Inspect an installed min-dalle environment without constructing MinDalle.

The helper prints distribution versions, dependency presence, public signatures,
and optional CUDA visibility. It does not download tokenizer/model assets or
load .pt weights.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from importlib import metadata


def version_or_error(dist: str) -> str:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return "missing"


def collect(check_cuda: bool) -> dict:
    result: dict = {
        "distributions": {
            "min-dalle": version_or_error("min-dalle"),
            "torch": version_or_error("torch"),
            "numpy": version_or_error("numpy"),
            "pillow": version_or_error("pillow"),
            "requests": version_or_error("requests"),
            "emoji": version_or_error("emoji"),
            "typing-extensions": version_or_error("typing-extensions"),
        },
        "imports": {},
        "signatures": {},
        "cuda": {"checked": False},
    }
    try:
        import min_dalle
        from min_dalle import MinDalle
        from min_dalle.text_tokenizer import TextTokenizer
    except Exception as exc:  # broad to report dependency import failures clearly
        result["imports"]["min_dalle"] = {"ok": False, "error": repr(exc)}
        return result

    result["imports"]["min_dalle"] = {"ok": True, "module": getattr(min_dalle, "__name__", "min_dalle")}
    for name in [
        "__init__",
        "generate_raw_image_stream",
        "generate_image_stream",
        "generate_images_stream",
        "generate_image",
        "generate_images",
        "image_grid_from_tokens",
    ]:
        result["signatures"][f"MinDalle.{name}"] = str(inspect.signature(getattr(MinDalle, name)))
    result["signatures"]["TextTokenizer.__init__"] = str(inspect.signature(TextTokenizer.__init__))
    result["signatures"]["TextTokenizer.tokenize"] = str(inspect.signature(TextTokenizer.tokenize))

    if check_cuda:
        try:
            import torch

            cuda = {
                "checked": True,
                "torch_version": torch.__version__,
                "torch_cuda_version": torch.version.cuda,
                "is_available": bool(torch.cuda.is_available()),
                "device_count": int(torch.cuda.device_count()),
            }
            if torch.cuda.is_available():
                cuda["device_0_name"] = torch.cuda.get_device_name(0)
                cuda["device_0_capability"] = list(torch.cuda.get_device_capability(0))
                torch.empty((1,), device="cuda")
                cuda["tiny_allocation"] = "passed"
            result["cuda"] = cuda
        except Exception as exc:
            result["cuda"] = {"checked": True, "error": repr(exc)}
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect min-dalle package metadata and public signatures without model downloads.")
    parser.add_argument("--check-cuda", action="store_true", help="Also inspect torch.cuda and allocate a tiny tensor if available.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args(argv)
    result = collect(check_cuda=args.check_cuda)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result["imports"].get("min_dalle", {}).get("ok"):
            print("min_dalle import failed; install package dependencies before running generation", file=sys.stderr)
            return 2
        print("inspection passed without constructing MinDalle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
