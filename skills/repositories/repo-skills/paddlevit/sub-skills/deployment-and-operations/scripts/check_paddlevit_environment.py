#!/usr/bin/env python3
"""Report Paddle/PaddleViT runtime facts without changing the environment.

This probe never installs packages, downloads files, writes output files, or
modifies shell environment variables. It deliberately reports capability
observations separately: import, CUDA compilation, visible devices, and a tiny
CUDA forward are not interchangeable claims.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from typing import Any, Dict


def _error(exc: BaseException) -> Dict[str, str]:
    """Return a concise, path-free error record."""
    first_line = str(exc).splitlines()[0] if str(exc) else "no detail"
    return {"type": type(exc).__name__, "detail": first_line[:500]}


def _probe_paddle(run_cuda_smoke: bool) -> Dict[str, Any]:
    """Probe Paddle import, backend visibility, and optionally one tiny layer."""
    result: Dict[str, Any] = {"import": {"ok": False}}
    try:
        import paddle  # type: ignore

        result["import"] = {"ok": True, "version": getattr(paddle, "__version__", "unknown")}
    except Exception as exc:  # Import errors include backend loader failures.
        result["import"] = {"ok": False, "error": _error(exc)}
        return result

    import paddle  # type: ignore  # imported above; kept local for type/runtime clarity

    compiled = False
    try:
        compiled = bool(paddle.is_compiled_with_cuda())
        result["cuda_compiled"] = compiled
    except Exception as exc:
        result["cuda_compiled"] = {"ok": False, "error": _error(exc)}

    try:
        result["device"] = str(paddle.get_device())
    except Exception as exc:
        result["device"] = {"ok": False, "error": _error(exc)}

    try:
        count = int(paddle.device.cuda.device_count()) if compiled else 0
        result["cuda_device_count"] = count
    except Exception as exc:
        result["cuda_device_count"] = {"ok": False, "error": _error(exc)}
        count = 0

    result["cuda_smoke"] = {"requested": bool(run_cuda_smoke)}
    if run_cuda_smoke and compiled and count > 0:
        try:
            paddle.set_device("gpu:0")
            x = paddle.ones([2, 4], dtype="float32")
            layer = paddle.nn.Linear(4, 3)
            y = layer(x)
            result["cuda_smoke"] = {
                "requested": True,
                "ok": True,
                "shape": list(y.shape),
                "place": str(y.place),
            }
        except Exception as exc:
            result["cuda_smoke"] = {"requested": True, "ok": False, "error": _error(exc)}
    elif run_cuda_smoke:
        result["cuda_smoke"] = {
            "requested": True,
            "ok": False,
            "skipped": True,
            "reason": "CUDA is not compiled or no CUDA device is visible",
        }
    return result


def main() -> int:
    """Run the read-only environment probe."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--no-cuda-smoke",
        action="store_true",
        help="only inspect CUDA metadata; do not run the tiny CUDA layer smoke",
    )
    args = parser.parse_args()

    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "paddle": _probe_paddle(not args.no_cuda_smoke),
        "side_effects": "none: no network, downloads, writes, or environment mutation",
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("PaddleViT environment probe (read-only)")
        print(f"Python: {report['python']} | Platform: {report['platform']}")
        paddle_report = report["paddle"]
        print(f"Paddle import: {paddle_report['import']}")
        for key in ("cuda_compiled", "device", "cuda_device_count", "cuda_smoke"):
            if key in paddle_report:
                print(f"{key}: {paddle_report[key]}")
        print(report["side_effects"])

    import_result = report["paddle"]["import"]
    smoke = report["paddle"].get("cuda_smoke", {})
    if not import_result.get("ok"):
        return 2
    if args.no_cuda_smoke:
        return 0
    if report["paddle"].get("cuda_compiled") and report["paddle"].get("cuda_device_count", 0):
        return 0 if smoke.get("ok") else 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
