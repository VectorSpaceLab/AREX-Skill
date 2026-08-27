#!/usr/bin/env python3
"""Read-only PaddleViT environment probe.

Reports framework/dependency imports and, when requested, a tiny backend
allocation. It never downloads data, imports the source checkout, or mutates
an environment. Use `--help` for options.
"""
from __future__ import annotations

import argparse
import importlib
import json
from typing import Any


def probe(device: str) -> dict[str, Any]:
    result: dict[str, Any] = {"device_requested": device, "imports": {}, "backend": {}}
    modules = {
        "paddle": "paddle",
        "yacs": "yacs",
        "yaml": "yaml",
        "PIL": "PIL",
        "cv2": "cv2",
        "scipy": "scipy",
        "pycocotools": "pycocotools",
        "lmdb": "lmdb",
    }
    for label, module_name in modules.items():
        try:
            module = importlib.import_module(module_name)
            result["imports"][label] = {
                "ok": True,
                "version": getattr(module, "__version__", None),
            }
        except Exception as exc:  # diagnostic output should remain useful
            result["imports"][label] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    try:
        import paddle

        result["paddle_version"] = paddle.__version__
        result["compiled_with_cuda"] = bool(paddle.is_compiled_with_cuda())
        if device:
            paddle.set_device(device)
            x = paddle.ones([1, 2], dtype="float32")
            result["backend"] = {
                "device": paddle.get_device(),
                "shape": list(x.shape),
                "place": str(x.place),
            }
    except Exception as exc:
        result["backend"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="", help="Optional Paddle device, e.g. cpu or gpu:0")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    result = probe(args.device)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"paddle={result.get('paddle_version', 'unavailable')}")
        print(f"compiled_with_cuda={result.get('compiled_with_cuda', False)}")
        for name, item in result["imports"].items():
            print(f"{name}: {'ok' if item['ok'] else 'missing'}")
        if result.get("backend"):
            print(f"backend: {json.dumps(result['backend'], sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
