#!/usr/bin/env python3
"""Read-only preflight for PointCNN's CUDA-only FPS custom operator.

This command inspects the sampling wrapper, source files, shared-library build
output, and the currently imported TensorFlow runtime. It never invokes a
compiler, downloads anything, creates a TensorFlow session, or executes an FPS
or GatherPoint kernel. A successful preflight is therefore never a pass for
FPS execution: a bounded CUDA custom-op run remains required.
"""

from __future__ import print_function

import argparse
import json
import sys
from pathlib import Path


SOURCE_FILES = ("tf_sampling.cpp", "tf_sampling_g.cu", "tf_sampling_compile.sh")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sampling-dir",
        required=True,
        help="Directory containing tf_sampling.py and the custom-op build output.",
    )
    parser.add_argument(
        "--source-dir",
        help="Optional directory containing the FPS C++/CUDA sources; defaults to --sampling-dir.",
    )
    parser.add_argument(
        "--library",
        default="tf_sampling_so.so",
        help="Shared-library filename or path (default: %(default)s).",
    )
    parser.add_argument(
        "--load-library",
        action="store_true",
        help="Ask TensorFlow to load the shared library; still does not execute an operator.",
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="Compatibility alias that explicitly skips TensorFlow shared-library loading.",
    )
    parser.add_argument(
        "--require-source",
        action="store_true",
        help="Treat missing source files as a blocking diagnostic condition.",
    )
    parser.add_argument(
        "--require-gpu",
        action="store_true",
        help="Compatibility flag; FPS always requires a discovered CUDA-capable GPU to proceed.",
    )
    parser.add_argument("--json", action="store_true", help="Emit structured JSON instead of text lines.")
    return parser


def message(result, level, text):
    result["messages"].append({"level": level, "message": text})


def resolve_library(sampling_dir, value):
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = sampling_dir / candidate
    return candidate.resolve()


def tensorflow_probe():
    """Import TensorFlow and inspect metadata only; never create a session."""
    try:
        import tensorflow as tf  # type: ignore
    except Exception as exc:  # Import errors are diagnostic output, not crashes.
        return {
            "available": False,
            "version": None,
            "cuda_build": None,
            "gpu_devices": [],
            "error": "{}: {}".format(type(exc).__name__, exc),
            "module": None,
        }

    devices = []
    device_error = None
    try:
        config = getattr(tf, "config", None)
        if config is not None and hasattr(config, "list_physical_devices"):
            devices = [str(device) for device in config.list_physical_devices("GPU")]
    except Exception as exc:  # Device enumeration can be unavailable on old TF builds.
        device_error = "{}: {}".format(type(exc).__name__, exc)

    if not devices:
        try:
            test_api = getattr(tf, "test", None)
            is_gpu_available = getattr(test_api, "is_gpu_available", None)
            if is_gpu_available is not None and is_gpu_available(cuda_only=True):
                devices = ["GPU (TensorFlow legacy discovery)"]
        except Exception as exc:
            device_error = "{}: {}".format(type(exc).__name__, exc)

    cuda_build = None
    try:
        cuda_build = bool(tf.test.is_built_with_cuda())
    except Exception:
        pass

    return {
        "available": True,
        "version": str(getattr(tf, "__version__", "unknown")),
        "cuda_build": cuda_build,
        "gpu_devices": devices,
        "error": device_error,
        "module": tf,
    }


def run(args):
    sampling_dir = Path(args.sampling_dir).expanduser().resolve()
    source_dir = Path(args.source_dir).expanduser().resolve() if args.source_dir else sampling_dir
    library = resolve_library(sampling_dir, args.library)
    wrapper = sampling_dir / "tf_sampling.py"

    result = {
        "sampling_dir": str(sampling_dir),
        "source_dir": str(source_dir),
        "wrapper": str(wrapper),
        "library": str(library),
        "source_files": {},
        "tensorflow": {
            "available": False,
            "version": None,
            "cuda_build": None,
            "gpu_devices": [],
            "error": None,
        },
        "library_load_requested": bool(args.load_library and not args.skip_load),
        "library_loaded": False,
        "kernel_execution": "NOT_RUN_REQUIRED",
        "status": "BLOCKED_REQUIRED_BACKEND",
        "messages": [],
    }
    blockers = []

    if not sampling_dir.is_dir():
        blockers.append("sampling directory is missing or is not a directory")
    if not wrapper.is_file():
        blockers.append("tf_sampling.py is missing; PointCNN cannot import the FPS wrapper")

    for filename in SOURCE_FILES:
        present = (source_dir / filename).is_file()
        result["source_files"][filename] = present
        if not present:
            message(result, "warning", "source/build recipe file is missing: {}".format(source_dir / filename))
    if args.require_source and not all(result["source_files"].values()):
        blockers.append("one or more required FPS source/build recipe files are missing")

    if not library.is_file():
        blockers.append("custom-op shared library is missing: {}".format(library))
    else:
        message(result, "info", "custom-op shared library exists; no compiler was invoked")

    tf_info = tensorflow_probe()
    result["tensorflow"] = {key: value for key, value in tf_info.items() if key != "module"}
    tf = tf_info["module"]
    if not tf_info["available"]:
        blockers.append("TensorFlow import failed")
        message(result, "error", "TensorFlow import failed: {}".format(tf_info["error"]))
    else:
        message(result, "info", "TensorFlow import succeeded: {}".format(tf_info["version"]))
        if tf_info["cuda_build"] is False:
            blockers.append("the imported TensorFlow build is not CUDA-enabled")
            message(result, "error", "TensorFlow reports no CUDA build support")
        if not tf_info["gpu_devices"]:
            blockers.append("TensorFlow did not discover a GPU")
            message(result, "error", "no GPU was discovered; FPS has no CPU fallback")
        else:
            message(result, "info", "TensorFlow discovered GPU device(s): {}".format(", ".join(tf_info["gpu_devices"])))
        if tf_info["error"]:
            message(result, "warning", "TensorFlow device metadata was partial: {}".format(tf_info["error"]))

    if args.load_library and args.skip_load:
        blockers.append("--load-library and --skip-load cannot be used together")
    elif args.load_library and tf is not None and library.is_file():
        try:
            tf.load_op_library(str(library))
            result["library_loaded"] = True
            message(result, "info", "TensorFlow loaded the shared library; no custom operator was executed")
        except Exception as exc:
            blockers.append("TensorFlow could not load the custom-op shared library")
            message(result, "error", "custom-op load failed: {}: {}".format(type(exc).__name__, exc))
    else:
        message(result, "warning", "shared-library load was not requested; pass --load-library for a load-only check")

    if blockers:
        result["status"] = "BLOCKED_REQUIRED_BACKEND"
        for blocker in blockers:
            message(result, "error", blocker)
    else:
        # Even a loadable library and visible GPU do not prove a GPU kernel ran.
        result["status"] = "PARTIAL_REQUIRED_BACKEND"
        message(
            result,
            "warning",
            "FPS/GatherPoint execution was not attempted. A bounded CUDA runtime smoke is still required; this is not a pass.",
        )
    message(
        result,
        "warning",
        "Required runtime boundary: the shipped segmentation settings use GPU-only FPS custom operators; CPU import is insufficient.",
    )
    return result, 2 if blockers else 0


def print_text(result):
    print("status: {}".format(result["status"]))
    print("sampling_dir: {}".format(result["sampling_dir"]))
    print("library: {}".format(result["library"]))
    print("tensorflow: {}".format(result["tensorflow"]["version"] or "unavailable"))
    print("gpu_devices: {}".format(", ".join(result["tensorflow"]["gpu_devices"]) or "none"))
    print("library_loaded: {}".format(result["library_loaded"]))
    print("kernel_execution: {}".format(result["kernel_execution"]))
    for item in result["messages"]:
        print("{}: {}".format(item["level"].upper(), item["message"]))


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.load_library and args.skip_load:
        parser.error("--load-library and --skip-load cannot be used together")
    result, return_code = run(args)
    if args.json:
        # The imported TensorFlow module is removed from the public result above.
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
