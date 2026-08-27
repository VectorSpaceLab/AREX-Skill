#!/usr/bin/env python3
"""Inspect CUDA FPS build prerequisites without compiling or downloading.

The diagnostic is read-only by default. It checks the sampling wrapper and
build inputs, compiler/toolkit visibility, TensorFlow ABI paths, and source
markers. ``--check-load`` is an explicit opt-in that asks TensorFlow to load an
existing ``tf_sampling_so.so``; it does not run a session or a GPU kernel.
"""

from __future__ import print_function

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys


_EXPECTED_FILES = (
    "tf_sampling.py",
    "tf_sampling.cpp",
    "tf_sampling_g.cu",
    "tf_sampling_compile.sh",
)


def _run_version(command):
    try:
        completed = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        output, _ = completed.communicate(timeout=5)
        lines = output.strip().splitlines()
        return {
            "present": completed.returncode == 0,
            "version": lines[0] if lines else "",
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {"present": False, "version": str(exc).splitlines()[0]}


def _read_text(path):
    try:
        with open(path, "r") as handle:
            return handle.read()
    except (IOError, OSError):
        return ""


def _tensorflow_probe():
    try:
        import tensorflow as tf
    except Exception as exc:  # pragma: no cover - host dependent
        return {
            "imported": False,
            "version": None,
            "graph_mode": None,
            "legacy_apis": False,
            "include_dir": None,
            "lib_dir": None,
            "error": str(exc).splitlines()[0],
        }

    executing_eagerly = getattr(tf, "executing_eagerly", None)
    if executing_eagerly is not None:
        try:
            graph_mode = not bool(executing_eagerly())
        except Exception:
            graph_mode = None
    else:
        graph_mode = str(getattr(tf, "__version__", "")).startswith("1.")

    legacy_apis = all(
        (
            hasattr(tf, "contrib"),
            hasattr(tf, "layers"),
            hasattr(tf, "load_op_library"),
            graph_mode is True,
        )
    )
    sysconfig = getattr(tf, "sysconfig", None)
    get_include = getattr(sysconfig, "get_include", None)
    get_lib = getattr(sysconfig, "get_lib", None)
    try:
        include_dir = get_include() if get_include else None
    except Exception:
        include_dir = None
    try:
        lib_dir = get_lib() if get_lib else None
    except Exception:
        lib_dir = None
    return {
        "imported": True,
        "version": getattr(tf, "__version__", "unknown"),
        "graph_mode": graph_mode,
        "legacy_apis": legacy_apis,
        "include_dir": include_dir,
        "lib_dir": lib_dir,
    }


def _sanitize(message, sampling_dir, library):
    text = str(message).splitlines()[0] if str(message) else "unknown load error"
    for value, replacement in (
        (os.path.abspath(sampling_dir), "<sampling-dir>"),
        (os.path.abspath(library), "<sampling-library>"),
    ):
        text = text.replace(value, replacement)
    return text[:500]


def _build_command(sampling_dir, cuda_root, tf_probe):
    sampling = shlex.quote(os.path.abspath(sampling_dir))
    cuda = shlex.quote(cuda_root) if cuda_root else '"${CUDA_ROOT}"'
    include_dir = tf_probe.get("include_dir") or "<tensorflow-include-dir>"
    lib_dir = tf_probe.get("lib_dir") or "<tensorflow-lib-dir>"
    include = shlex.quote(include_dir)
    lib = shlex.quote(lib_dir)
    return "\n".join(
        [
            "# Printed for review only; this diagnostic never executes it.",
            "TF_INC=%s" % include,
            "TF_LIB=%s" % lib,
            "CUDA_ROOT=%s" % cuda,
            "SAMPLING_DIR=%s" % sampling,
            '"$CUDA_ROOT/bin/nvcc" "$SAMPLING_DIR/tf_sampling_g.cu" '
            '-o "$SAMPLING_DIR/tf_sampling_g.cu.o" -c -O2 '
            '-DGOOGLE_CUDA=1 -x cu -Xcompiler -fPIC',
            'g++ -std=c++11 "$SAMPLING_DIR/tf_sampling.cpp" '
            '"$SAMPLING_DIR/tf_sampling_g.cu.o" -o "$SAMPLING_DIR/tf_sampling_so.so" '
            '-shared -fPIC -L"$TF_LIB" -ltensorflow_framework '
            '-I "$TF_INC/external/nsync/public" -I "$TF_INC" '
            '-I "$CUDA_ROOT/include" -lcudart -L"$CUDA_ROOT/lib64" -O2 '
            '-D_GLIBCXX_USE_CXX11_ABI=0',
        ]
    )


def _path_status(path):
    return {"path": path, "present": bool(path and os.path.exists(path))}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Inspect legacy PointCNN CUDA FPS sources and build prerequisites "
            "without compiling, downloading, training, or running a session."
        )
    )
    parser.add_argument(
        "--sampling-dir",
        default=".",
        help="directory containing the sampling wrapper and build sources (default: .)",
    )
    parser.add_argument(
        "--cuda-root",
        help="CUDA toolkit root to inspect; otherwise use CUDA_ROOT, CUDA_HOME, or PATH",
    )
    parser.add_argument(
        "--check-load",
        action="store_true",
        help="explicitly load an existing tf_sampling_so.so, but do not execute a kernel",
    )
    parser.add_argument(
        "--show-build-command",
        action="store_true",
        help="print a quoted manual build recipe; never execute it",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero when a required prerequisite or requested load is missing",
    )
    parser.add_argument("--json", action="store_true", help="emit one JSON object")
    args = parser.parse_args(argv)

    sampling_dir = os.path.abspath(args.sampling_dir)
    library = os.path.join(sampling_dir, "tf_sampling_so.so")
    file_paths = {
        filename: os.path.join(sampling_dir, filename) for filename in _EXPECTED_FILES
    }
    source_text = "\n".join(_read_text(path) for path in file_paths.values())

    cuda_root = (
        args.cuda_root
        or os.environ.get("CUDA_ROOT")
        or os.environ.get("CUDA_HOME")
    )
    nvcc = os.path.join(cuda_root, "bin", "nvcc") if cuda_root else shutil.which("nvcc")
    gxx = shutil.which("g++") or shutil.which("c++")
    tf_probe = _tensorflow_probe()

    cuda_include = os.path.join(cuda_root, "include") if cuda_root else None
    cuda_lib = os.path.join(cuda_root, "lib64") if cuda_root else None
    result = {
        "status": "inspect-only",
        "sampling_dir": args.sampling_dir,
        "files": {
            filename: os.path.isfile(path) for filename, path in file_paths.items()
        },
        "shared_library": os.path.isfile(library),
        "toolkit_paths": {
            "cuda_root": _path_status(cuda_root),
            "cuda_include": _path_status(cuda_include),
            "cuda_lib64": _path_status(cuda_lib),
        },
        "nvcc": _run_version([nvcc, "--version"])
        if nvcc
        else {"present": False, "version": "not found"},
        "cxx": _run_version([gxx, "--version"])
        if gxx
        else {"present": False, "version": "not found"},
        "tensorflow": tf_probe,
        "tensorflow_paths": {
            "include": _path_status(tf_probe.get("include_dir")),
            "lib": _path_status(tf_probe.get("lib_dir")),
        },
        "source_markers": {
            "gpu_kernels": "DEVICE_GPU" in source_text,
            "google_cuda": "GOOGLE_CUDA" in source_text,
            "legacy_abi_zero": "_GLIBCXX_USE_CXX11_ABI=0" in source_text,
            "hardcoded_cuda_path": "/usr/local/cuda" in source_text,
            "expected_library_name": "tf_sampling_so.so" in source_text,
        },
        "load": "not-requested",
        "notes": [
            "No compiler, downloader, training job, or TensorFlow session was invoked.",
            "A loaded shared library is not proof that a GPU kernel executes successfully.",
            "FPS remains BLOCKED_REQUIRED_BACKEND until a bounded GPU operator session passes.",
        ],
    }

    if args.check_load:
        if not os.path.isfile(library):
            result["load"] = "missing-library"
        elif not tf_probe["imported"] or not tf_probe["legacy_apis"]:
            result["load"] = "tensorflow-unavailable"
        else:
            try:
                import tensorflow as tf

                tf.load_op_library(library)
                result["load"] = "loaded"
            except Exception as exc:  # pragma: no cover - host/library dependent
                result["load"] = "failed"
                result["notes"].append(
                    "Shared-library load failed: %s"
                    % _sanitize(exc, sampling_dir, library)
                )

    if args.show_build_command:
        result["manual_build_command"] = _build_command(
            sampling_dir, cuda_root, tf_probe
        )

    missing_files = [
        name for name, present in result["files"].items() if not present
    ]
    strict_failures = []
    if missing_files:
        strict_failures.append("missing source files: %s" % ", ".join(missing_files))
    if not result["nvcc"]["present"]:
        strict_failures.append("nvcc is unavailable")
    if not result["cxx"]["present"]:
        strict_failures.append("a C++ compiler is unavailable")
    if not tf_probe["imported"]:
        strict_failures.append("TensorFlow cannot be imported")
    elif not tf_probe["legacy_apis"]:
        strict_failures.append("TensorFlow 1.x graph-mode APIs are not ready")
    if not result["source_markers"]["gpu_kernels"]:
        strict_failures.append("GPU kernel registration marker DEVICE_GPU is absent")
    if args.check_load and result["load"] != "loaded":
        strict_failures.append("requested shared-library load did not pass")

    result["strict_failures"] = strict_failures
    if strict_failures:
        result["status"] = "blocked"
    else:
        result["status"] = "ready-to-review"

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("status: %s" % result["status"])
        print("sampling_dir: %s" % result["sampling_dir"])
        print("shared_library: %s" % result["shared_library"])
        print("nvcc: %s (%s)" % (result["nvcc"]["present"], result["nvcc"]["version"]))
        print("cxx: %s (%s)" % (result["cxx"]["present"], result["cxx"]["version"]))
        print("tensorflow: %s" % result["tensorflow"])
        print("tensorflow_paths: %s" % result["tensorflow_paths"])
        print("toolkit_paths: %s" % result["toolkit_paths"])
        print("source_markers: %s" % result["source_markers"])
        print("load: %s" % result["load"])
        for note in result["notes"]:
            print("note: %s" % note)
        for failure in strict_failures:
            print("strict-failure: %s" % failure)
        if args.show_build_command:
            print("manual-build-command:")
            print(result["manual_build_command"])

    return 2 if args.strict and strict_failures else 0


if __name__ == "__main__":
    sys.exit(main())
