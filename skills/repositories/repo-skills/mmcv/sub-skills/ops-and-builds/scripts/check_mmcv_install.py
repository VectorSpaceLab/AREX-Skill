#!/usr/bin/env python3
"""Inspect an MMCV installation without relying on a source checkout."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import platform
import re
import sys
from typing import Any, Optional


def _safe_version(distribution: str) -> Optional[str]:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _status(label: str, value: Any) -> None:
    print(f"{label}: {value}")


def _sanitize(text: str) -> str:
    text = re.sub(r"[A-Za-z]:\\[^\s:'\"]+", "<path>", text)
    text = re.sub(r"/(?:[^\s:'\"]+/)*[^\s:'\"]+", "<path>", text)
    return text


def _format_exception(exc: BaseException) -> str:
    return _sanitize(f"{type(exc).__name__}: {exc}")


def _import_module(name: str) -> tuple[Optional[Any], Optional[str]]:
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # noqa: BLE001 - diagnostic should report any import failure.
        return None, _format_exception(exc)


def _collect_torch() -> tuple[Optional[Any], bool]:
    torch, error = _import_module("torch")
    if torch is None:
        _status("torch import", f"failed ({error})")
        return None, False

    _status("torch import", "ok")
    _status("torch version", getattr(torch, "__version__", "unknown"))
    _status("torch cuda runtime", getattr(getattr(torch, "version", None), "cuda", None))

    cuda_available = False
    try:
        cuda_available = bool(torch.cuda.is_available())
    except Exception as exc:  # noqa: BLE001 - CUDA probing can fail on broken installs.
        _status("torch cuda available", f"probe failed ({_format_exception(exc)})")
    else:
        _status("torch cuda available", cuda_available)

    if cuda_available:
        try:
            _status("torch cuda device count", torch.cuda.device_count())
        except Exception as exc:  # noqa: BLE001
            _status("torch cuda device count", f"probe failed ({_format_exception(exc)})")
        try:
            names = [torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count())]
            _status("torch cuda devices", ", ".join(names) if names else "none")
        except Exception as exc:  # noqa: BLE001
            _status("torch cuda devices", f"probe failed ({_format_exception(exc)})")

    return torch, cuda_available


def _run_box_iou_smoke(torch: Any) -> bool:
    try:
        import numpy as np
        from mmcv.ops import box_iou_rotated

        boxes1 = torch.from_numpy(
            np.asarray(
                [
                    [1.0, 1.0, 3.0, 4.0, 0.5],
                    [2.0, 2.0, 3.0, 4.0, 0.6],
                    [7.0, 7.0, 8.0, 8.0, 0.4],
                ],
                dtype=np.float32,
            )
        )
        boxes2 = torch.from_numpy(
            np.asarray(
                [
                    [0.0, 2.0, 2.0, 5.0, 0.3],
                    [2.0, 1.0, 3.0, 3.0, 0.5],
                    [5.0, 5.0, 6.0, 7.0, 0.4],
                ],
                dtype=np.float32,
            )
        )
        result = box_iou_rotated(boxes1, boxes2)
        _status("box_iou_rotated cpu smoke", f"ok shape={tuple(result.shape)}")
        return True
    except Exception as exc:  # noqa: BLE001 - report native op failures cleanly.
        _status("box_iou_rotated cpu smoke", f"failed ({_format_exception(exc)})")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect an installed MMCV package, report ops/CUDA facts, and "
            "optionally require compiled ops or CUDA availability."
        )
    )
    parser.add_argument(
        "--require-ops",
        action="store_true",
        help="Exit nonzero if mmcv.ops cannot be imported or the CPU ops smoke test fails.",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Exit nonzero if PyTorch CUDA is unavailable.",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Only import mmcv.ops; do not run the box_iou_rotated smoke check.",
    )
    args = parser.parse_args()

    failures: list[str] = []

    _status("python", sys.version.replace("\n", " "))
    _status("platform", platform.platform())
    _status("distribution mmcv", _safe_version("mmcv") or "not installed")
    _status("distribution mmcv-lite", _safe_version("mmcv-lite") or "not installed")

    mmcv, mmcv_error = _import_module("mmcv")
    if mmcv is None:
        _status("mmcv import", f"failed ({mmcv_error})")
    else:
        _status("mmcv import", "ok")
        _status("mmcv version", getattr(mmcv, "__version__", "unknown"))

    torch, cuda_available = _collect_torch()
    if args.require_cuda and not cuda_available:
        failures.append("--require-cuda requested but torch.cuda.is_available() is false")

    ops_imported = False
    if mmcv is not None:
        ops, ops_error = _import_module("mmcv.ops")
        if ops is None:
            _status("mmcv.ops import", f"failed ({ops_error})")
            _status("compiled ops interpretation", "missing or unloadable mmcv._ext; expected for mmcv-lite")
        else:
            ops_imported = True
            _status("mmcv.ops import", "ok")
            info_names = ["get_compiler_version", "get_compiling_cuda_version"]
            if all(hasattr(ops, name) for name in info_names):
                try:
                    _status("mmcv compiler", ops.get_compiler_version())
                except Exception as exc:  # noqa: BLE001
                    _status("mmcv compiler", f"probe failed ({_format_exception(exc)})")
                try:
                    _status("mmcv cuda compiler", ops.get_compiling_cuda_version())
                except Exception as exc:  # noqa: BLE001
                    _status("mmcv cuda compiler", f"probe failed ({_format_exception(exc)})")

    smoke_ok = True
    if ops_imported and not args.skip_smoke:
        if torch is None:
            smoke_ok = False
            _status("box_iou_rotated cpu smoke", "skipped because torch import failed")
        else:
            smoke_ok = _run_box_iou_smoke(torch)
    elif not ops_imported:
        smoke_ok = False

    if args.require_ops:
        if not ops_imported:
            failures.append("--require-ops requested but mmcv.ops import failed")
        elif not args.skip_smoke and not smoke_ok:
            failures.append("--require-ops requested but box_iou_rotated smoke check failed")

    if failures:
        print("result: failed")
        for failure in failures:
            print(f"failure: {failure}")
        return 1

    print("result: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
