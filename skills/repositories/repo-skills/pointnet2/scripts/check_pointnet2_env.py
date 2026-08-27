#!/usr/bin/env python
"""Shared readiness check for the legacy charlesq34/pointnet2 repository.

The script is intentionally read-only and deterministic: it inspects an explicit
repo root, imports only dependency packages, and never imports the source
loaders that can trigger dataset downloads. Custom TensorFlow ops are only
loaded when --try-load-custom-ops is supplied.
"""
from __future__ import print_function

import argparse
import json
import os
import platform
import subprocess
import sys

EXPECTED_SOURCE_FILES = [
    "README.md",
    "train.py",
    "train_multi_gpu.py",
    "evaluate.py",
    "modelnet_dataset.py",
    "modelnet_h5_dataset.py",
    os.path.join("models", "pointnet2_cls_ssg.py"),
    os.path.join("models", "pointnet2_cls_msg.py"),
    os.path.join("models", "pointnet2_part_seg.py"),
    os.path.join("models", "pointnet2_part_seg_msg_one_hot.py"),
    os.path.join("models", "pointnet2_sem_seg.py"),
    os.path.join("models", "pointnet_cls_basic.py"),
    os.path.join("utils", "tf_util.py"),
    os.path.join("utils", "pointnet_util.py"),
    os.path.join("tf_ops", "sampling", "tf_sampling.py"),
    os.path.join("tf_ops", "grouping", "tf_grouping.py"),
    os.path.join("tf_ops", "3d_interpolation", "tf_interpolate.py"),
    os.path.join("part_seg", "train.py"),
    os.path.join("scannet", "train.py"),
]

CUSTOM_OPS = [
    {
        "id": "sampling",
        "so": os.path.join("tf_ops", "sampling", "tf_sampling_so.so"),
        "wrapper": os.path.join("tf_ops", "sampling", "tf_sampling.py"),
    },
    {
        "id": "grouping",
        "so": os.path.join("tf_ops", "grouping", "tf_grouping_so.so"),
        "wrapper": os.path.join("tf_ops", "grouping", "tf_grouping.py"),
    },
    {
        "id": "3d_interpolation",
        "so": os.path.join("tf_ops", "3d_interpolation", "tf_interpolate_so.so"),
        "wrapper": os.path.join("tf_ops", "3d_interpolation", "tf_interpolate.py"),
    },
]

DATASET_PATHS = {
    "modelnet_h5": os.path.join("data", "modelnet40_ply_hdf5_2048"),
    "modelnet_normal": os.path.join("data", "modelnet40_normal_resampled"),
    "shapenetpart_normal": os.path.join("data", "shapenetcore_partanno_segmentation_benchmark_v0_normal"),
    "scannet_pickles": os.path.join("data", "scannet_data_pointnet2"),
}

IMPORT_MODULES = ["numpy", "h5py", "scipy", "sklearn", "matplotlib", "PIL", "plyfile"]


def norm_repo_root(path):
    root = os.path.abspath(path)
    return root


def rel_exists(root, rel_path):
    return os.path.exists(os.path.join(root, rel_path))


def which(executable):
    path = os.environ.get("PATH", "")
    suffixes = [""]
    if os.name == "nt":
        suffixes = os.environ.get("PATHEXT", ".EXE;.BAT;.CMD").split(os.pathsep)
    for directory in path.split(os.pathsep):
        if not directory:
            continue
        for suffix in suffixes:
            candidate = os.path.join(directory, executable + suffix)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
    return None


def run_version_command(command):
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
    except Exception as exc:  # pragma: no cover - host dependent
        return {"available": False, "error": "%s: %s" % (exc.__class__.__name__, exc)}
    text = out or err or b""
    if not isinstance(text, str):
        try:
            text = text.decode("utf-8", "replace")
        except TypeError:  # Python 2 fallback
            text = text.decode("utf-8", "replace")
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    return {"available": proc.returncode == 0, "returncode": proc.returncode, "summary": first_line}


def import_probe(module_name):
    try:
        module = __import__(module_name)
    except Exception as exc:
        return {
            "available": False,
            "errorType": exc.__class__.__name__,
            "error": str(exc),
        }
    version = getattr(module, "__version__", None)
    if version is None and module_name == "PIL":
        version = getattr(module, "PILLOW_VERSION", None)
    return {"available": True, "version": version}


def tensorflow_probe(skip_tensorflow):
    if skip_tensorflow:
        return {"checked": False, "available": None, "reason": "skipped by --skip-tensorflow"}
    probe = import_probe("tensorflow")
    probe["checked"] = True
    if not probe.get("available"):
        probe["tf1Compatible"] = False
        probe["hasTfContrib"] = False
        return probe
    import tensorflow as tf  # noqa: E402
    version = getattr(tf, "__version__", "")
    has_tf_contrib = hasattr(tf, "contrib")
    probe["version"] = version
    probe["hasTfContrib"] = bool(has_tf_contrib)
    probe["tf1Compatible"] = bool(version.startswith("1.") and has_tf_contrib)
    try:
        probe["builtWithCuda"] = bool(tf.test.is_built_with_cuda())
    except Exception:
        probe["builtWithCuda"] = None
    try:
        probe["cxx11AbiFlag"] = getattr(tf.sysconfig, "CXX11_ABI_FLAG")
    except Exception:
        probe["cxx11AbiFlag"] = None
    return probe


def inspect_custom_ops(root, tf_probe, try_load):
    results = []
    tf_module = None
    if try_load:
        if not tf_probe.get("available"):
            tf_probe = tensorflow_probe(False)
        if tf_probe.get("available"):
            import tensorflow as tf  # noqa: E402
            tf_module = tf
    for item in CUSTOM_OPS:
        so_path = os.path.join(root, item["so"])
        wrapper_path = os.path.join(root, item["wrapper"])
        result = {
            "id": item["id"],
            "soRelativePath": item["so"],
            "wrapperRelativePath": item["wrapper"],
            "soExists": os.path.exists(so_path),
            "wrapperExists": os.path.exists(wrapper_path),
            "loadAttempted": False,
        }
        if try_load:
            result["loadAttempted"] = True
            if not result["soExists"]:
                result["loaded"] = False
                result["loadError"] = "shared library is missing"
            elif tf_module is None:
                result["loaded"] = False
                result["loadError"] = "TensorFlow is not importable"
            else:
                try:
                    tf_module.load_op_library(so_path)
                    result["loaded"] = True
                except Exception as exc:
                    result["loaded"] = False
                    result["loadErrorType"] = exc.__class__.__name__
                    result["loadError"] = str(exc)
        results.append(result)
    return results


def build_report(args):
    root = norm_repo_root(args.repo_root)
    missing_source = [path for path in EXPECTED_SOURCE_FILES if not rel_exists(root, path)]
    dataset_status = {}
    for name, rel_path in DATASET_PATHS.items():
        dataset_status[name] = {"relativePath": rel_path, "exists": rel_exists(root, rel_path)}

    imports = {}
    for module_name in IMPORT_MODULES:
        imports[module_name] = import_probe(module_name)
    tf = tensorflow_probe(args.skip_tensorflow)
    imports["tensorflow"] = tf

    tools = {
        "python": {"executable": sys.executable, "version": sys.version.split()[0]},
        "platform": platform.platform(),
        "g++": {"path": which("g++")},
        "nvcc": {"path": which("nvcc")},
        "nvidia-smi": {"path": which("nvidia-smi")},
    }
    if tools["g++"]["path"]:
        tools["g++"].update(run_version_command([tools["g++"]["path"], "--version"]))
    if tools["nvcc"]["path"]:
        tools["nvcc"].update(run_version_command([tools["nvcc"]["path"], "--version"]))
    if tools["nvidia-smi"]["path"]:
        tools["nvidia-smi"].update(run_version_command([tools["nvidia-smi"]["path"], "--query-gpu=name,driver_version", "--format=csv,noheader"]))

    custom_ops = inspect_custom_ops(root, tf, args.try_load_custom_ops)

    return {
        "schemaVersion": 1,
        "repo": "pointnet2",
        "repoRoot": root,
        "sourceLayout": {
            "expectedFileCount": len(EXPECTED_SOURCE_FILES),
            "missingExpectedFiles": missing_source,
            "ok": len(missing_source) == 0,
        },
        "tools": tools,
        "imports": imports,
        "customOps": custom_ops,
        "datasets": dataset_status,
        "notes": [
            "This check does not import pointnet2 source loaders, so it cannot trigger ModelNet download side effects.",
            "Custom TensorFlow ops are loaded only when --try-load-custom-ops is supplied.",
            "Dataset path checks only report presence; use workflow validators for schema validation.",
        ],
    }


def requirement_failures(report, requirements):
    failures = []
    if not report["sourceLayout"]["ok"]:
        failures.append("missing expected source files: %s" % ", ".join(report["sourceLayout"]["missingExpectedFiles"]))

    reqs = set(requirements or [])
    tf = report["imports"]["tensorflow"]
    if "tensorflow" in reqs and not tf.get("available"):
        failures.append("TensorFlow is not importable")
    if "tf1" in reqs and not tf.get("tf1Compatible"):
        failures.append("TensorFlow 1.x with tf.contrib is not available")
    if "custom-ops" in reqs:
        missing = [item["id"] for item in report["customOps"] if not item.get("soExists")]
        if missing:
            failures.append("missing custom-op shared libraries: %s" % ", ".join(missing))
        loaded_failures = [item["id"] for item in report["customOps"] if item.get("loadAttempted") and not item.get("loaded")]
        if loaded_failures:
            failures.append("custom-op load failures: %s" % ", ".join(loaded_failures))
    if "modelnet-h5" in reqs and not report["datasets"]["modelnet_h5"]["exists"]:
        failures.append("ModelNet HDF5 directory is missing")
    if "shapenetpart" in reqs and not report["datasets"]["shapenetpart_normal"]["exists"]:
        failures.append("ShapeNetPart normal directory is missing")
    if "scannet-pickles" in reqs and not report["datasets"]["scannet_pickles"]["exists"]:
        failures.append("ScanNet pickle directory is missing")
    return failures


def print_text(report, failures):
    print("pointnet2 environment check")
    print("repo root: %s" % report["repoRoot"])
    print("source layout: %s" % ("ok" if report["sourceLayout"]["ok"] else "missing files"))
    if report["sourceLayout"]["missingExpectedFiles"]:
        for path in report["sourceLayout"]["missingExpectedFiles"]:
            print("  missing: %s" % path)
    print("python: %s (%s)" % (report["tools"]["python"]["version"], report["tools"]["python"]["executable"]))
    tf = report["imports"]["tensorflow"]
    if tf.get("checked") is False:
        print("tensorflow: skipped")
    elif tf.get("available"):
        print("tensorflow: %s tf1Compatible=%s tf.contrib=%s" % (tf.get("version"), tf.get("tf1Compatible"), tf.get("hasTfContrib")))
    else:
        print("tensorflow: unavailable (%s)" % tf.get("error", "unknown error"))
    for name in ["numpy", "h5py", "scipy", "sklearn", "matplotlib", "PIL", "plyfile"]:
        probe = report["imports"].get(name, {})
        print("%s: %s%s" % (name, "available" if probe.get("available") else "missing", " %s" % probe.get("version") if probe.get("version") else ""))
    for tool in ["g++", "nvcc", "nvidia-smi"]:
        info = report["tools"].get(tool, {})
        print("%s: %s" % (tool, info.get("path") or "not found"))
    for item in report["customOps"]:
        status = "present" if item["soExists"] else "missing"
        if item.get("loadAttempted"):
            status += ", loaded" if item.get("loaded") else ", load failed"
        print("custom-op %s: %s (%s)" % (item["id"], status, item["soRelativePath"]))
    for name, info in sorted(report["datasets"].items()):
        print("dataset %s: %s (%s)" % (name, "present" if info["exists"] else "missing", info["relativePath"]))
    if failures:
        print("FAILURES:")
        for failure in failures:
            print("  - %s" % failure)
    else:
        print("requirements: ok")


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Read-only pointnet2 source/dependency/backend readiness check.")
    parser.add_argument("--repo-root", required=True, help="Explicit path to a pointnet2 checkout to inspect.")
    parser.add_argument(
        "--require",
        action="append",
        choices=["tensorflow", "tf1", "custom-ops", "modelnet-h5", "shapenetpart", "scannet-pickles"],
        help="Requirement to enforce. May be supplied multiple times.",
    )
    parser.add_argument("--try-load-custom-ops", action="store_true", help="Attempt tf.load_op_library on present custom-op .so files.")
    parser.add_argument("--skip-tensorflow", action="store_true", help="Skip importing TensorFlow unless custom-op loading is requested.")
    parser.add_argument("--json", action="store_true", help="Emit the full JSON report instead of text.")
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    report = build_report(args)
    failures = requirement_failures(report, args.require)
    report["requirements"] = {"requested": args.require or [], "ok": len(failures) == 0, "failures": failures}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report, failures)
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
