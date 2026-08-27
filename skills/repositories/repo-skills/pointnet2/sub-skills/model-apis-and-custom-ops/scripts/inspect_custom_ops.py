#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Inspect PointNet2 TensorFlow custom-op readiness without importing wrappers.

The source wrappers in tf_ops/* call tf.load_op_library at import time. This
script checks TensorFlow, expected .so files, optional direct load attempts,
and compiler/toolchain metadata so a user can distinguish TensorFlow readiness
from PointNet++ custom-op readiness.

Compatible with Python 2.7 and Python 3.x so it can run inside legacy TF1
inspection environments.
"""
from __future__ import print_function

import argparse
import json
import os
import shutil
import subprocess
import sys
import traceback

OP_SPECS = [
    {
        "id": "sampling",
        "op_dir": "sampling",
        "wrapper": "tf_ops/sampling/tf_sampling.py",
        "library": "tf_ops/sampling/tf_sampling_so.so",
        "compile_script": "tf_ops/sampling/tf_sampling_compile.sh",
        "sources": ["tf_sampling.cpp", "tf_sampling_g.cu"],
        "needs_cuda": True,
    },
    {
        "id": "grouping",
        "op_dir": "grouping",
        "wrapper": "tf_ops/grouping/tf_grouping.py",
        "library": "tf_ops/grouping/tf_grouping_so.so",
        "compile_script": "tf_ops/grouping/tf_grouping_compile.sh",
        "sources": ["tf_grouping.cpp", "tf_grouping_g.cu"],
        "needs_cuda": True,
    },
    {
        "id": "3d_interpolation",
        "op_dir": "3d_interpolation",
        "wrapper": "tf_ops/3d_interpolation/tf_interpolate.py",
        "library": "tf_ops/3d_interpolation/tf_interpolate_so.so",
        "compile_script": "tf_ops/3d_interpolation/tf_interpolate_compile.sh",
        "sources": ["tf_interpolate.cpp"],
        "needs_cuda": False,
    },
]


def _decode(data):
    if isinstance(data, bytes):
        return data.decode("utf-8", "replace")
    return data


def run_version(command, args=("--version",), timeout=5):
    path = shutil.which(command) if hasattr(shutil, "which") else None
    if path is None:
        # Python 2 fallback.
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            candidate = os.path.join(directory, command)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                path = candidate
                break
    result = {"command": command, "path": path, "available": bool(path)}
    if not path:
        return result
    try:
        proc = subprocess.Popen([path] + list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = proc.communicate()
        result.update({"returncode": proc.returncode, "output": _decode(out).strip().splitlines()[:5]})
    except Exception as exc:  # pragma: no cover - diagnostic path
        result.update({"returncode": None, "error": repr(exc)})
    return result


def _parents(path):
    path = os.path.abspath(path)
    while True:
        yield path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent


def find_repo_root(explicit):
    if explicit:
        root = os.path.abspath(os.path.expanduser(explicit))
        if not os.path.exists(root):
            raise SystemExit("repo root does not exist: %s" % root)
        return root

    starts = [os.getcwd(), os.path.abspath(__file__)]
    for start in starts:
        for candidate in _parents(start):
            if os.path.isdir(os.path.join(candidate, "tf_ops")) and os.path.isfile(os.path.join(candidate, "utils", "tf_util.py")):
                return candidate
    raise SystemExit("could not infer repo root; pass --repo-root /path/to/pointnet2")


def tensorflow_probe():
    probe = {"ok": False}
    try:
        import tensorflow as tf  # noqa: F401
        probe.update(
            {
                "ok": True,
                "version": getattr(tf, "__version__", "unknown"),
                "has_contrib": hasattr(tf, "contrib"),
                "has_load_op_library": hasattr(tf, "load_op_library"),
                "module_file": getattr(tf, "__file__", None),
            }
        )
        try:
            sysconfig = getattr(tf, "sysconfig", None)
            if sysconfig is not None:
                if hasattr(sysconfig, "get_include"):
                    probe["include"] = sysconfig.get_include()
                if hasattr(sysconfig, "get_lib"):
                    probe["lib"] = sysconfig.get_lib()
                if hasattr(sysconfig, "get_compile_flags"):
                    probe["compile_flags"] = list(sysconfig.get_compile_flags())
                if hasattr(sysconfig, "get_link_flags"):
                    probe["link_flags"] = list(sysconfig.get_link_flags())
                probe["cxx11_abi_flag"] = getattr(sysconfig, "CXX11_ABI_FLAG", None)
        except Exception as exc:
            probe["sysconfig_error"] = repr(exc)
        return probe
    except BaseException as exc:  # TensorFlow can raise non-Exception subclasses on import
        probe.update(
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback_tail": traceback.format_exc(limit=3).splitlines()[-6:],
            }
        )
        return probe


def op_file_probe(repo_root):
    rows = []
    for spec in OP_SPECS:
        lib = os.path.join(repo_root, spec["library"])
        wrapper = os.path.join(repo_root, spec["wrapper"])
        compile_script = os.path.join(repo_root, spec["compile_script"])
        source_files = [os.path.join(repo_root, "tf_ops", spec["op_dir"], src) for src in spec["sources"]]
        row = {
            "id": spec["id"],
            "library": lib,
            "library_exists": os.path.isfile(lib),
            "library_size": os.path.getsize(lib) if os.path.isfile(lib) else None,
            "wrapper": wrapper,
            "wrapper_exists": os.path.isfile(wrapper),
            "compile_script": compile_script,
            "compile_script_exists": os.path.isfile(compile_script),
            "sources_exist": dict((os.path.basename(src), os.path.isfile(src)) for src in source_files),
            "needs_cuda": spec["needs_cuda"],
        }
        rows.append(row)
    return rows


def try_load_libraries(tf_probe, op_rows):
    if not tf_probe.get("ok"):
        for row in op_rows:
            row["load_status"] = "skipped-no-tensorflow"
        return
    try:
        import tensorflow as tf
    except BaseException:
        for row in op_rows:
            row["load_status"] = "skipped-no-tensorflow"
        return
    if not hasattr(tf, "load_op_library"):
        for row in op_rows:
            row["load_status"] = "failed"
            row["load_error"] = "tensorflow module has no load_op_library"
        return
    for row in op_rows:
        if not row["library_exists"]:
            row["load_status"] = "missing-library"
            continue
        try:
            module = tf.load_op_library(row["library"])
            row["load_status"] = "loaded"
            row["loaded_module"] = repr(module)
        except BaseException as exc:
            row["load_status"] = "failed"
            row["load_error_type"] = type(exc).__name__
            row["load_error"] = str(exc)


def build_report(repo_root, try_load):
    tf_probe = tensorflow_probe()
    op_rows = op_file_probe(repo_root)
    if try_load:
        try_load_libraries(tf_probe, op_rows)
    return {
        "repo_root": repo_root,
        "python": sys.executable,
        "python_version": sys.version.replace("\n", " "),
        "tensorflow": tf_probe,
        "ops": op_rows,
        "toolchain": {
            "g++": run_version("g++"),
            "nvcc": run_version("nvcc"),
            "nvidia-smi": run_version("nvidia-smi", ("--query-gpu=name,driver_version", "--format=csv,noheader")),
        },
    }


def print_text(report, try_load):
    print("Repo root: %s" % report["repo_root"])
    print("Python: %s (%s)" % (report["python"], report["python_version"].split()[0]))
    tfp = report["tensorflow"]
    if tfp.get("ok"):
        print(
            "TensorFlow: OK version=%s has_contrib=%s load_op_library=%s"
            % (tfp.get("version"), tfp.get("has_contrib"), tfp.get("has_load_op_library"))
        )
        if not tfp.get("has_contrib"):
            print("  warning: tf.contrib is absent; source tf_util.py/model graph paths require TensorFlow 1.x semantics")
        if tfp.get("include"):
            print("  include: %s" % tfp.get("include"))
        if tfp.get("lib"):
            print("  lib: %s" % tfp.get("lib"))
        if tfp.get("cxx11_abi_flag") is not None:
            print("  CXX11_ABI_FLAG: %s" % tfp.get("cxx11_abi_flag"))
    else:
        print("TensorFlow: MISSING/FAILED %s: %s" % (tfp.get("error_type"), tfp.get("error")))

    print("\nExpected custom-op libraries:")
    for row in report["ops"]:
        status = "present" if row["library_exists"] else "missing"
        load = row.get("load_status", "not-attempted")
        print("- %s: %s :: %s" % (row["id"], status, row["library"]))
        print(
            "  wrapper_exists=%s compile_script_exists=%s needs_cuda=%s"
            % (row["wrapper_exists"], row["compile_script_exists"], row["needs_cuda"])
        )
        if try_load:
            if load == "loaded":
                print("  load: loaded")
            else:
                print("  load: %s" % load)
                if row.get("load_error"):
                    print("  load_error: %s: %s" % (row.get("load_error_type"), row.get("load_error")))

    print("\nToolchain:")
    for name in ["g++", "nvcc", "nvidia-smi"]:
        info = report["toolchain"][name]
        print("- %s: %s %s" % (name, "available" if info.get("available") else "missing", info.get("path") or ""))
        if info.get("output"):
            print("  %s" % info["output"][0])

    print("\nNext steps:")
    print("- If TensorFlow is OK but any library is missing, PointNet++ models are not custom-op ready; the CPU baseline may still build.")
    print("- If a library exists but load fails, rebuild against the active TensorFlow include/link flags and matching C++ ABI.")
    print("- Original source compile scripts hard-code CUDA 8 and Python 2.7 TF paths; adapt before running.")


def requirement_failures(report, requirements, try_load):
    failures = []
    if "tensorflow" in requirements and not report["tensorflow"].get("ok"):
        failures.append("required TensorFlow import failed")
    if "custom-ops" in requirements:
        missing = [row["id"] for row in report["ops"] if not row["library_exists"]]
        if missing:
            failures.append("missing custom-op libraries: " + ", ".join(missing))
        if try_load:
            failed_loads = [row["id"] for row in report["ops"] if row.get("load_status") != "loaded"]
            if failed_loads:
                failures.append("custom-op load did not succeed for: " + ", ".join(failed_loads))
    if "toolchain" in requirements:
        if not report["toolchain"]["g++"].get("available"):
            failures.append("required g++ is missing")
        if not report["toolchain"]["nvcc"].get("available"):
            failures.append("required nvcc is missing")
    return failures


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Path to the pointnet2 checkout. If omitted, search upward from cwd/script.")
    parser.add_argument("--try-load", action="store_true", help="Attempt tf.load_op_library for present .so files.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    parser.add_argument(
        "--require",
        action="append",
        choices=["tensorflow", "custom-ops", "toolchain"],
        default=[],
        help="Fail nonzero if the named readiness condition is not met. Can be repeated.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    repo_root = find_repo_root(args.repo_root)
    report = build_report(repo_root, args.try_load)
    failures = requirement_failures(report, args.require, args.try_load)
    report["requirements"] = args.require
    report["requirement_failures"] = failures

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report, args.try_load)
        if failures:
            print("\nRequirement failures:")
            for failure in failures:
                print("- %s" % failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
