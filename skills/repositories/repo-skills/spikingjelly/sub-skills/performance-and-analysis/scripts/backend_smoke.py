#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
from typing import Any

import torch
from spikingjelly.activation_based import functional, neuron

VALID_BACKENDS = ("torch", "cupy", "triton")


def module_available(name: str) -> tuple[bool, str | None]:
    try:
        importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - environment dependent
        return False, f"{type(exc).__name__}: {exc}"
    return True, None


def default_device_for_backend(backend: str) -> str:
    if backend in {"cupy", "triton"}:
        return "cuda:0"
    return "cuda:0" if torch.cuda.is_available() else "cpu"


def run_backend(backend: str, device: str | None = None) -> dict[str, Any]:
    report: dict[str, Any] = {"backend": backend}
    if backend not in VALID_BACKENDS:
        return {"backend": backend, "status": "failed", "error": "unknown backend"}

    if backend in {"cupy", "triton"}:
        ok, reason = module_available(backend)
        if not ok:
            report.update(status="skipped", reason=reason)
            return report
        if not torch.cuda.is_available():
            report.update(status="skipped", reason="CUDA is not available")
            return report

    resolved_device = device or default_device_for_backend(backend)
    if backend in {"cupy", "triton"} and not str(resolved_device).startswith("cuda"):
        report.update(status="skipped", reason=f"{backend} backend requires CUDA")
        return report

    try:
        x = torch.randn(4, 2, 8, device=resolved_device)
        net = neuron.LIFNode(
            tau=2.0,
            step_mode="m",
            backend=backend,
            store_v_seq=True,
        ).to(resolved_device)
        with torch.no_grad():
            y = net(x)
        finite = bool(torch.isfinite(y).all().item())
        functional.reset_net(net)
        report.update(
            status="passed",
            device=str(y.device),
            shape=list(y.shape),
            dtype=str(y.dtype),
            finite=finite,
            spike_mean=float(y.float().mean().detach().cpu().item()),
        )
    except Exception as exc:  # pragma: no cover - smoke should expose real failures
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tiny SpikingJelly backend smoke for torch/CuPy/Triton LIFNode forwards."
    )
    parser.add_argument(
        "--backends",
        nargs="+",
        default=list(VALID_BACKENDS),
        choices=VALID_BACKENDS,
        help="backend names to test; unavailable optional backends are skipped",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="override device, for example cpu or cuda:0",
    )
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args()

    results = [run_backend(backend, args.device) for backend in args.backends]
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        for item in results:
            print(item)

    if any(item.get("status") == "failed" for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
