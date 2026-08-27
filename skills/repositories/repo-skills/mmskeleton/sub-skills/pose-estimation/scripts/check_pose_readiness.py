#!/usr/bin/env python3
"""Report optional mmskeleton pose-estimation import readiness.

This checker is deliberately side-effect free: it imports package metadata and
capability modules only. It never downloads checkpoints, reads configs, opens
media, allocates a model, or invokes a detector.
"""
from __future__ import print_function

import argparse
import importlib
import re
import sys


_CUDA_DEVICE = re.compile(r"^cuda(?::([0-9]+))?$")


def _parser():
    parser = argparse.ArgumentParser(
        description=(
            "Report torch/CUDA, MMCV custom-op, and MMDetection API "
            "readiness without downloading or running inference."
        )
    )
    parser.add_argument(
        "--device",
        default="auto",
        metavar="DEVICE",
        help="device to report: auto, cpu, cuda, or cuda:N (default: auto)",
    )
    parser.add_argument(
        "--require-detector",
        action="store_true",
        help=(
            "return nonzero when the requested detector readiness gate is "
            "absent; otherwise the report is informational"
        ),
    )
    return parser


def _device_request(value):
    value = str(value).strip().lower()
    if value in ("auto", "cpu"):
        return value, None
    match = _CUDA_DEVICE.match(value)
    if match:
        index = None if match.group(1) is None else int(match.group(1))
        return "cuda", index
    raise ValueError("device must be auto, cpu, cuda, or cuda:N")


def _import(name):
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # optional binary packages can fail at import time
        return None, type(exc).__name__


def _yes(value):
    return "yes" if value else "no"


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        device_kind, device_index = _device_request(args.device)
    except ValueError as exc:
        parser.error(str(exc))

    print("pose-readiness: no-download, no-inference")
    print("requested_device: {}".format(args.device))

    torch, torch_error = _import("torch")
    torch_ok = torch is not None
    if torch_ok:
        cuda_build = getattr(getattr(torch, "version", None), "cuda", None)
        print("torch: available (version={})".format(
            getattr(torch, "__version__", "unknown")))
        print("torch_cuda_build: {}".format(cuda_build or "none"))
        try:
            cuda_available = bool(torch.cuda.is_available())
            cuda_count = int(torch.cuda.device_count()) if cuda_available else 0
        except Exception as exc:
            cuda_available = False
            cuda_count = 0
            print("cuda_probe: error ({})".format(type(exc).__name__))
        print("cuda_available: {}".format(_yes(cuda_available)))
        print("cuda_device_count: {}".format(cuda_count))
        if cuda_available:
            try:
                selected = 0 if device_index is None else device_index
                if selected >= cuda_count:
                    print("cuda_requested_index: unavailable ({})".format(
                        selected))
                else:
                    print("cuda_requested_index: {}".format(selected))
                    print("cuda_device_name: {}".format(
                        torch.cuda.get_device_name(selected)))
            except Exception as exc:
                print("cuda_device_probe: error ({})".format(
                    type(exc).__name__))
    else:
        cuda_available = False
        cuda_count = 0
        print("torch: unavailable ({})".format(torch_error))
        print("torch_cuda_build: unavailable")
        print("cuda_available: no")
        print("cuda_device_count: 0")

    mmcv, mmcv_error = _import("mmcv")
    mmcv_ok = mmcv is not None
    if mmcv_ok:
        print("mmcv: available (version={})".format(
            getattr(mmcv, "__version__", "unknown")))
    else:
        print("mmcv: unavailable ({})".format(mmcv_error))

    mmcv_ext, mmcv_ext_error = _import("mmcv._ext")
    mmcv_ext_ok = mmcv_ext is not None
    if mmcv_ext_ok:
        print("mmcv._ext: available")
    else:
        print("mmcv._ext: unavailable ({})".format(mmcv_ext_error))

    mmdet_apis, mmdet_error = _import("mmdet.apis")
    required_apis = (
        "init_detector",
        "inference_detector",
    )
    api_ok = mmdet_apis is not None and all(
        hasattr(mmdet_apis, name) for name in required_apis
    )
    if api_ok:
        print("mmdet.apis: available (init_detector, inference_detector)")
    elif mmdet_apis is not None:
        missing = [name for name in required_apis
                   if not hasattr(mmdet_apis, name)]
        print("mmdet.apis: incomplete (missing={})".format(
            ",".join(missing)))
    else:
        print("mmdet.apis: unavailable ({})".format(mmdet_error))

    # Pose inference has CUDA assumptions.  CPU must never satisfy the CUDA
    # gate; auto may resolve to CUDA when a valid CUDA device is available.
    cuda_ready = device_kind in ("auto", "cuda") and cuda_available and cuda_count > 0 and (
        device_index is None or device_index < cuda_count
    )
    print("cuda_ready: {}".format(_yes(cuda_ready)))
    detector_ready = torch_ok and mmcv_ok and mmcv_ext_ok and api_ok and cuda_ready
    print("detector_import_gate: {}".format("ready" if detector_ready else "absent"))
    if device_kind == "cpu":
        print("device_note: CPU selected; pose inference code has CUDA assumptions")
    elif device_kind == "auto" and not cuda_available:
        print("device_note: auto resolved to CPU; pose inference code has CUDA assumptions")

    # Informational mode intentionally succeeds even when optional packages are absent.
    if args.require_detector and not detector_ready:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
