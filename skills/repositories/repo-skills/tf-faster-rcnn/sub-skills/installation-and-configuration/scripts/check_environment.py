#!/usr/bin/env python3
"""Safe tf-faster-rcnn environment inspector.

This script only reads local files and imports local modules. It does not
download datasets, fetch checkpoints, build extensions, or run training.

Example:
    python scripts/check_environment.py --repo-root /path/to/tf-faster-rcnn
"""

import argparse
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


REQUIRED_PATHS = [
    "README.md",
    "lib/setup.py",
    "lib/Makefile",
    "lib/model/config.py",
    "lib/model/nms_wrapper.py",
    "lib/layer_utils/generate_anchors.py",
    "lib/nms/py_cpu_nms.py",
    "tools/demo.py",
    "tools/trainval_net.py",
    "tools/test_net.py",
    "experiments/cfgs",
    "experiments/scripts",
    "data/scripts/fetch_faster_rcnn_models.sh",
    "docker/Dockerfile.cuda-8.0",
    "docker/Dockerfile.cuda-7.5",
]

REQUIRED_MODULES = [
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("easydict", "easydict"),
    ("yaml", "PyYAML"),
    ("Cython", "Cython"),
    ("cv2", "opencv-python-headless"),
    ("PIL", "Pillow"),
    ("tensorflow", "tensorflow"),
]

OPTIONAL_MODULES = [
    ("pycocotools", "pycocotools"),
    ("matplotlib", "matplotlib"),
]


def version_tuple(text):
    parts = []
    for chunk in str(text).split("."):
        match = re.match(r"(\d+)", chunk)
        if not match:
            break
        parts.append(int(match.group(1)))
        if len(parts) >= 2:
            break
    while len(parts) < 2:
        parts.append(0)
    return tuple(parts)


def import_module_info(import_name, dist_name=None):
    try:
        module = importlib.import_module(import_name)
    except Exception as exc:
        return {"ok": False, "error": "{}: {}".format(type(exc).__name__, exc)}

    version = getattr(module, "__version__", None)
    if version is None and dist_name:
        try:
            import pkg_resources
            version = pkg_resources.get_distribution(dist_name).version
        except Exception:
            version = None

    return {"ok": True, "version": version}


def check_modules(module_specs):
    results = []
    missing = []
    for import_name, dist_name in module_specs:
        info = import_module_info(import_name, dist_name)
        info["import_name"] = import_name
        info["distribution"] = dist_name
        results.append(info)
        if not info["ok"]:
            missing.append("{}: {}".format(import_name, info["error"]))
    return results, missing


def check_layout(repo_root):
    missing = []
    present = []
    for rel in REQUIRED_PATHS:
        path = repo_root / rel
        if path.exists():
            present.append(rel)
        else:
            missing.append(rel)

    presets = []
    cfg_dir = repo_root / "experiments" / "cfgs"
    if cfg_dir.is_dir():
        presets = sorted(p.name for p in cfg_dir.glob("*.yml"))

    return {"present": present, "missing": missing, "presets": presets}


def inspect_setup_py(repo_root):
    info = {"exists": False, "arch_flag": None, "uses_cuda_home": False}
    setup_path = repo_root / "lib" / "setup.py"
    if not setup_path.is_file():
        return info
    info["exists"] = True
    text = setup_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"-arch=(sm_[0-9]+)", text)
    if match:
        info["arch_flag"] = match.group(1)
    info["uses_cuda_home"] = "CUDAHOME" in text
    return info


def inspect_tensorflow():
    info = {
        "ok": False,
        "version": None,
        "major": None,
        "contrib_slim": False,
        "contrib_slim_error": None,
        "protobuf_version": None,
        "protobuf_ok": None,
        "cuda_built": None,
        "cuda_available": None,
        "error": None,
    }

    try:
        tf = importlib.import_module("tensorflow")
    except Exception as exc:
        info["error"] = "{}: {}".format(type(exc).__name__, exc)
        return info

    info["version"] = getattr(tf, "__version__", None)
    try:
        info["major"] = int(str(info["version"]).split(".")[0])
    except Exception:
        info["major"] = None

    try:
        importlib.import_module("tensorflow.contrib.slim")
        info["contrib_slim"] = True
    except Exception as exc:
        info["contrib_slim_error"] = "{}: {}".format(type(exc).__name__, exc)

    try:
        import pkg_resources
        info["protobuf_version"] = pkg_resources.get_distribution("protobuf").version
    except Exception:
        try:
            protobuf_module = importlib.import_module("google.protobuf")
            info["protobuf_version"] = getattr(protobuf_module, "__version__", None)
        except Exception:
            info["protobuf_version"] = None

    if info["protobuf_version"] is not None:
        info["protobuf_ok"] = version_tuple(info["protobuf_version"]) < (4, 0)

    try:
        info["cuda_built"] = bool(getattr(tf.test, "is_built_with_cuda", lambda: False)())
    except Exception:
        info["cuda_built"] = None

    try:
        info["cuda_available"] = bool(getattr(tf.test, "is_gpu_available", lambda **kwargs: False)(cuda_only=True))
    except Exception:
        info["cuda_available"] = None

    info["ok"] = info["major"] == 1 and info["contrib_slim"] and info["protobuf_ok"] is not False
    return info


def inspect_config(repo_root):
    lib_root = repo_root / "lib"
    sys.path.insert(0, str(lib_root))
    try:
        config_module = importlib.import_module("model.config")
    finally:
        if sys.path and sys.path[0] == str(lib_root):
            sys.path.pop(0)

    cfg = config_module.cfg
    return {
        "ok": True,
        "use_gpu_nms": cfg.USE_GPU_NMS,
        "test_mode": cfg.TEST.MODE,
        "train_scales": list(cfg.TRAIN.SCALES),
        "test_scales": list(cfg.TEST.SCALES),
        "anchor_scales": list(cfg.ANCHOR_SCALES),
        "anchor_ratios": list(cfg.ANCHOR_RATIOS),
        "pooling_mode": cfg.POOLING_MODE,
        "exp_dir": cfg.EXP_DIR,
        "snapshot_prefix": cfg.TRAIN.SNAPSHOT_PREFIX,
    }


def smoke_generate_anchors(repo_root):
    lib_root = repo_root / "lib"
    sys.path.insert(0, str(lib_root))
    try:
        from layer_utils.generate_anchors import generate_anchors
        anchors = generate_anchors()
    finally:
        if sys.path and sys.path[0] == str(lib_root):
            sys.path.pop(0)
    shape = tuple(int(dim) for dim in anchors.shape)
    return {"ok": shape == (9, 4), "shape": shape}


def smoke_py_cpu_nms(repo_root):
    import numpy as np

    lib_root = repo_root / "lib"
    sys.path.insert(0, str(lib_root))
    try:
        from nms.py_cpu_nms import py_cpu_nms
        fixture = np.array(
            [
                [10.0, 10.0, 20.0, 20.0, 0.9],
                [11.0, 11.0, 21.0, 21.0, 0.8],
                [50.0, 50.0, 60.0, 60.0, 0.7],
            ],
            dtype=np.float32,
        )
        keep = py_cpu_nms(fixture, 0.3)
    finally:
        if sys.path and sys.path[0] == str(lib_root):
            sys.path.pop(0)
    keep = [int(item) for item in keep]
    return {"ok": keep == [0, 2], "keep": keep}


def inspect_native_wrapper(repo_root):
    lib_root = repo_root / "lib"
    sys.path.insert(0, str(lib_root))
    try:
        importlib.import_module("model.nms_wrapper")
        return {"ok": True, "error": None}
    except Exception as exc:
        return {"ok": False, "error": "{}: {}".format(type(exc).__name__, exc)}
    finally:
        if sys.path and sys.path[0] == str(lib_root):
            sys.path.pop(0)


def inspect_cuda():
    info = {
        "CUDAHOME": os.environ.get("CUDAHOME"),
        "CUDA_HOME": os.environ.get("CUDA_HOME"),
        "nvcc": None,
        "nvcc_version": None,
        "include_dir": None,
        "lib64_dir": None,
    }

    candidates = []
    for env_name in ("CUDAHOME", "CUDA_HOME"):
        root = os.environ.get(env_name)
        if root:
            candidates.append(Path(root) / "bin" / "nvcc")
    which_nvcc = shutil.which("nvcc")
    if which_nvcc:
        candidates.append(Path(which_nvcc))

    for candidate in candidates:
        if candidate.is_file():
            info["nvcc"] = str(candidate)
            break

    if info["nvcc"]:
        proc = subprocess.run([info["nvcc"], "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        info["nvcc_version"] = (proc.stdout.strip() or proc.stderr.strip())[:1000]

    cuda_root = info["CUDAHOME"] or info["CUDA_HOME"]
    if cuda_root:
        root_path = Path(cuda_root)
        include_dir = root_path / "include"
        lib64_dir = root_path / "lib64"
        if include_dir.is_dir():
            info["include_dir"] = str(include_dir)
        if lib64_dir.is_dir():
            info["lib64_dir"] = str(lib64_dir)

    return info


def inspect_presets(repo_root):
    import yaml

    cfg_dir = repo_root / "experiments" / "cfgs"
    presets = []
    if not cfg_dir.is_dir():
        return presets

    for path in sorted(cfg_dir.glob("*.yml")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            train = data.get("TRAIN", {}) or {}
            test = data.get("TEST", {}) or {}
            inherited = "<inherited>"
            presets.append(
                {
                    "file": path.name,
                    "exp_dir": data.get("EXP_DIR", inherited),
                    "snapshot_prefix": train.get("SNAPSHOT_PREFIX", inherited),
                    "train_scales": train.get("SCALES", inherited),
                    "test_scales": test.get("SCALES", inherited),
                    "anchor_scales": data.get("ANCHOR_SCALES", inherited),
                    "test_rpn_post_nms_top_n": test.get("RPN_POST_NMS_TOP_N", inherited),
                    "double_bias": train.get("DOUBLE_BIAS", inherited),
                }
            )
        except Exception as exc:
            presets.append({"file": path.name, "error": "{}: {}".format(type(exc).__name__, exc)})

    return presets


def print_text(report):
    print("tf-faster-rcnn environment check")
    print("repo root:", report["repo_root"])
    print("status:", report["status"])

    print("\n[dependencies]")
    for item in report["required_modules"]:
        if item["ok"]:
            print("  OK  {import_name}: {version}".format(**item))
        else:
            print("  FAIL {import_name}: {error}".format(**item))

    if report["optional_modules"]:
        print("\n[optional dependencies]")
        for item in report["optional_modules"]:
            if item["ok"]:
                print("  OK  {import_name}: {version}".format(**item))
            else:
                print("  WARN {import_name}: {error}".format(**item))

    print("\n[tensorflow]")
    tf_info = report["tensorflow"]
    if tf_info.get("error"):
        print("  FAIL", tf_info["error"])
    else:
        print("  version:", tf_info.get("version"))
        print("  contrib.slim:", "ok" if tf_info.get("contrib_slim") else tf_info.get("contrib_slim_error"))
        print("  protobuf:", tf_info.get("protobuf_version"))
        print("  built_with_cuda:", tf_info.get("cuda_built"))
        print("  gpu_available:", tf_info.get("cuda_available"))

    print("\n[config defaults]")
    cfg = report["config"]
    if not cfg.get("ok"):
        print("  FAIL could not import model.config")
        print("  ", cfg.get("error"))
    else:
        print("  USE_GPU_NMS:", cfg["use_gpu_nms"])
        print("  TEST.MODE:", cfg["test_mode"])
        print("  TRAIN.SCALES:", cfg["train_scales"])
        print("  TEST.SCALES:", cfg["test_scales"])
        print("  ANCHOR_SCALES:", cfg["anchor_scales"])
        print("  ANCHOR_RATIOS:", cfg["anchor_ratios"])
        print("  POOLING_MODE:", cfg["pooling_mode"])
        print("  EXP_DIR:", cfg["exp_dir"])
        print("  SNAPSHOT_PREFIX:", cfg["snapshot_prefix"])

    print("\n[pure utility smoke]")
    anchors = report["generate_anchors"]
    print("  generate_anchors:", "ok" if anchors["ok"] else "FAIL", "shape=", anchors["shape"])
    nms = report["py_cpu_nms"]
    print("  py_cpu_nms:", "ok" if nms["ok"] else "FAIL", "keep=", nms["keep"])

    print("\n[native wrapper readiness]")
    wrapper = report["native_wrapper"]
    if wrapper["ok"]:
        print("  model.nms_wrapper: ok")
    else:
        print("  WARN model.nms_wrapper:", wrapper["error"])

    print("\n[cuda / nvcc]")
    cuda = report["cuda"]
    print("  CUDAHOME:", cuda.get("CUDAHOME") or "unset")
    print("  CUDA_HOME:", cuda.get("CUDA_HOME") or "unset")
    print("  nvcc:", cuda.get("nvcc") or "not found")
    if cuda.get("nvcc_version"):
        print("  nvcc --version:", cuda.get("nvcc_version"))
    print("  include dir:", cuda.get("include_dir") or "not found")
    print("  lib64 dir:", cuda.get("lib64_dir") or "not found")

    print("\n[layout]")
    layout = report["layout"]
    if layout["missing"]:
        print("  FAIL missing paths:")
        for path in layout["missing"]:
            print("    -", path)
    else:
        print("  OK all required paths present")

    print("  experiment presets:")
    for preset in report["presets"]:
        if "error" in preset:
            print("    - {file}: {error}".format(**preset))
        else:
            print(
                "    - {file}: EXP_DIR={exp_dir}, SNAPSHOT_PREFIX={snapshot_prefix}, "
                "TRAIN.SCALES={train_scales}, ANCHOR_SCALES={anchor_scales}".format(**preset)
            )

    print("\n[setup.py notes]")
    setup = report["setup_py"]
    print("  exists:", setup["exists"])
    print("  arch_flag:", setup["arch_flag"] or "not found")
    print("  uses_cuda_home:", setup["uses_cuda_home"])

    print("\n[result]")
    if report["failures"]:
        print("  FAIL")
        for failure in report["failures"]:
            print("    -", failure)
    elif report["warnings"]:
        print("  WARN")
        for warning in report["warnings"]:
            print("    -", warning)
    else:
        print("  OK")


def main():
    parser = argparse.ArgumentParser(description="Inspect tf-faster-rcnn dependencies, config defaults, CUDA readiness, and source-tree layout.")
    parser.add_argument("--repo-root", default=".", help="Path to the tf-faster-rcnn repository root.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    report = {
        "repo_root": str(repo_root),
        "required_modules": [],
        "optional_modules": [],
        "tensorflow": {},
        "config": {"ok": False},
        "generate_anchors": {"ok": False, "shape": None},
        "py_cpu_nms": {"ok": False, "keep": None},
        "native_wrapper": {"ok": False, "error": None},
        "cuda": {},
        "layout": {"present": [], "missing": [], "presets": []},
        "setup_py": {"exists": False, "arch_flag": None, "uses_cuda_home": False},
        "presets": [],
        "warnings": [],
        "failures": [],
        "status": "OK",
    }

    if not repo_root.is_dir():
        report["status"] = "FAIL"
        report["failures"].append("repo root does not exist or is not a directory")
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_text(report)
        return 1

    report["required_modules"], required_missing = check_modules(REQUIRED_MODULES)
    report["optional_modules"], optional_missing = check_modules(OPTIONAL_MODULES)
    for item in optional_missing:
        report["warnings"].append(item)

    tf_info = inspect_tensorflow()
    report["tensorflow"] = tf_info
    if tf_info.get("error"):
        report["failures"].append("tensorflow: {}".format(tf_info["error"]))
    else:
        if tf_info.get("major") != 1:
            report["failures"].append("TensorFlow major version must be 1 for this repository; found {}".format(tf_info.get("version")))
        if not tf_info.get("contrib_slim"):
            report["failures"].append("tensorflow.contrib.slim is unavailable: {}".format(tf_info.get("contrib_slim_error")))
        if tf_info.get("protobuf_ok") is False:
            report["failures"].append("protobuf {} is too new for the TensorFlow 1.x inspection path".format(tf_info.get("protobuf_version")))
        if tf_info.get("protobuf_version") is None:
            report["warnings"].append("protobuf version could not be determined")

    try:
        report["config"] = inspect_config(repo_root)
    except Exception as exc:
        report["config"] = {"ok": False, "error": "{}: {}".format(type(exc).__name__, exc)}
        report["failures"].append("could not import model.config: {}".format(report["config"]["error"]))

    try:
        report["generate_anchors"] = smoke_generate_anchors(repo_root)
        if not report["generate_anchors"]["ok"]:
            report["failures"].append("generate_anchors shape check failed; expected (9, 4) but got {}".format(report["generate_anchors"]["shape"]))
    except Exception as exc:
        report["failures"].append("generate_anchors smoke failed: {}: {}".format(type(exc).__name__, exc))

    try:
        report["py_cpu_nms"] = smoke_py_cpu_nms(repo_root)
        if not report["py_cpu_nms"]["ok"]:
            report["failures"].append("py_cpu_nms smoke failed; expected [0, 2] but got {}".format(report["py_cpu_nms"]["keep"]))
    except Exception as exc:
        report["failures"].append("py_cpu_nms smoke failed: {}: {}".format(type(exc).__name__, exc))

    try:
        report["native_wrapper"] = inspect_native_wrapper(repo_root)
        if not report["native_wrapper"]["ok"]:
            report["warnings"].append("model.nms_wrapper is not importable yet: {}".format(report["native_wrapper"]["error"]))
    except Exception as exc:
        report["warnings"].append("model.nms_wrapper check failed unexpectedly: {}: {}".format(type(exc).__name__, exc))

    report["cuda"] = inspect_cuda()
    if not report["cuda"].get("nvcc"):
        report["warnings"].append("nvcc was not found; lib/setup.py build_ext --inplace is blocked")
    if report["cuda"].get("CUDA_HOME") and not report["cuda"].get("CUDAHOME"):
        report["warnings"].append("CUDA_HOME is set but lib/setup.py reads CUDAHOME; export CUDAHOME too or rely on nvcc in PATH")
    if (report["cuda"].get("CUDAHOME") or report["cuda"].get("CUDA_HOME")) and not (report["cuda"].get("include_dir") and report["cuda"].get("lib64_dir")):
        report["warnings"].append("CUDA include/lib64 directories are incomplete under the configured CUDA root")

    report["layout"] = check_layout(repo_root)
    if report["layout"]["missing"]:
        report["failures"].append("missing required source-tree paths: {}".format(", ".join(report["layout"]["missing"])))

    report["setup_py"] = inspect_setup_py(repo_root)
    if not report["setup_py"]["exists"]:
        report["failures"].append("lib/setup.py is missing")
    if report["setup_py"]["arch_flag"]:
        report["warnings"].append("lib/setup.py hardcodes -arch={} and may need a local GPU-specific edit".format(report["setup_py"]["arch_flag"]))
    else:
        report["warnings"].append("could not extract the CUDA arch flag from lib/setup.py")
    if not report["setup_py"]["uses_cuda_home"]:
        report["warnings"].append("lib/setup.py did not contain a CUDAHOME lookup")

    try:
        report["presets"] = inspect_presets(repo_root)
    except Exception as exc:
        report["warnings"].append("could not inspect experiment presets: {}: {}".format(type(exc).__name__, exc))
        report["presets"] = []

    # Required module failures are treated as hard failures.
    for item in report["required_modules"]:
        if not item["ok"]:
            report["failures"].append("{}: {}".format(item["import_name"], item["error"]))

    if report["failures"]:
        report["status"] = "FAIL"
    elif report["warnings"]:
        report["status"] = "WARN"
    else:
        report["status"] = "OK"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
