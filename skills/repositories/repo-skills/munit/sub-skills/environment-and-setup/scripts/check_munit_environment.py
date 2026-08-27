#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Safe MUNIT environment checker.

This helper imports dependencies and performs static repository checks. It does
not run training, inference, downloads, model construction, or CUDA tensor
allocation. It is intentionally compatible with Python 2.7/3.x so it can run in
legacy MUNIT environments.
"""
from __future__ import print_function

import argparse
import glob
import importlib
import os
import re
import sys
import traceback


LEGACY_TARGETS = {
    "python": "2.7 or 3.6",
    "torch": "0.4.1",
    "torchvision": "0.2.x (0.2.1 preferred)",
    "cuda": "9.x (docs use 9.1)",
    "cudnn": "7.x",
}


class Reporter(object):
    def __init__(self):
        self.failures = 0
        self.warnings = 0

    def ok(self, title, detail=""):
        self._emit("OK", title, detail)

    def warn(self, title, detail=""):
        self.warnings += 1
        self._emit("WARN", title, detail)

    def fail(self, title, detail=""):
        self.failures += 1
        self._emit("FAIL", title, detail)

    def info(self, title, detail=""):
        self._emit("INFO", title, detail)

    def _emit(self, level, title, detail):
        if detail:
            print("[{0}] {1}: {2}".format(level, title, detail))
        else:
            print("[{0}] {1}".format(level, title))


def import_module(name):
    return importlib.import_module(name)


def module_version(module):
    for attr in ("__version__", "version"):
        value = getattr(module, attr, None)
        if isinstance(value, str):
            return value
    return "unknown"


def parse_version_tuple(text):
    nums = re.findall(r"\d+", text or "")[:3]
    while len(nums) < 3:
        nums.append("0")
    try:
        return tuple(int(x) for x in nums)
    except Exception:
        return (0, 0, 0)


def check_python(rep):
    ver = sys.version_info
    desc = "{0}.{1}.{2}".format(ver[0], ver[1], ver[2])
    if (ver[0] == 2 and ver[1] == 7) or (ver[0] == 3 and ver[1] == 6):
        rep.ok("Python version", desc)
    else:
        rep.warn(
            "Python version",
            "running {0}; MUNIT documented target is {1}".format(desc, LEGACY_TARGETS["python"]),
        )


def check_required_imports(rep):
    modules = [
        ("torch", "PyTorch core"),
        ("torchvision", "TorchVision transforms/utils"),
        ("yaml", "PyYAML config parser"),
        ("PIL.Image", "Pillow image loader"),
        ("tensorboardX", "tensorboardX training logger"),
        ("tensorboard", "tensorboard package"),
        ("numpy", "NumPy utilities"),
    ]
    loaded = {}
    for name, purpose in modules:
        try:
            mod = import_module(name)
            loaded[name] = mod
            root_mod = mod
            if "." in name:
                root_mod = sys.modules.get(name.split(".")[0], mod)
            rep.ok("import {0}".format(name), "{0}; version {1}".format(purpose, module_version(root_mod)))
        except Exception as exc:
            rep.fail("import {0}".format(name), "{0}: {1}".format(exc.__class__.__name__, exc))
    try:
        scipy = import_module("scipy")
        rep.ok("optional import scipy", "needed only for test_batch metric options; version {0}".format(module_version(scipy)))
    except Exception as exc:
        rep.warn("optional import scipy", "needed only for test_batch metric options: {0}".format(exc))
    return loaded


def check_torch_compat(rep, loaded):
    torch = loaded.get("torch")
    if torch is None:
        return
    torch_ver = module_version(torch)
    if torch_ver.startswith("0.4.1"):
        rep.ok("PyTorch legacy version", torch_ver)
    else:
        rep.warn(
            "PyTorch legacy version",
            "running {0}; MUNIT target is {1}".format(torch_ver, LEGACY_TARGETS["torch"]),
        )

    try:
        from torch.utils.serialization import load_lua  # noqa: F401
        rep.ok("torch.utils.serialization.load_lua", "available")
    except Exception as exc:
        rep.fail(
            "torch.utils.serialization.load_lua",
            "missing ({0}); unmodified MUNIT utils.py imports it at module import time".format(exc),
        )

    cuda_compiled = getattr(getattr(torch, "version", None), "cuda", None)
    if cuda_compiled:
        rep.info("PyTorch compiled CUDA", str(cuda_compiled))
        parsed = parse_version_tuple(str(cuda_compiled))
        if parsed and parsed[0] >= 11:
            rep.warn("CUDA version", "compiled CUDA {0}; legacy target is {1}".format(cuda_compiled, LEGACY_TARGETS["cuda"]))
    else:
        rep.warn("PyTorch compiled CUDA", "not reported; execution scripts require CUDA unless ported")

    cudnn = getattr(getattr(torch.backends, "cudnn", None), "version", None)
    if callable(cudnn):
        try:
            cudnn_ver = cudnn()
            if cudnn_ver:
                rep.info("cuDNN version", str(cudnn_ver))
            else:
                rep.warn("cuDNN version", "not available from torch.backends.cudnn")
        except Exception as exc:
            rep.warn("cuDNN version", str(exc))


def check_torchvision_compat(rep, loaded):
    tv = loaded.get("torchvision")
    if tv is None:
        return
    tv_ver = module_version(tv)
    if tv_ver.startswith("0.2"):
        rep.ok("TorchVision legacy version", tv_ver)
    else:
        rep.warn(
            "TorchVision legacy version",
            "running {0}; target paired with PyTorch 0.4.1 is {1}".format(tv_ver, LEGACY_TARGETS["torchvision"]),
        )


def check_yaml_compat(rep, loaded):
    yaml_mod = loaded.get("yaml")
    if yaml_mod is None:
        return
    yver = module_version(yaml_mod)
    parsed = parse_version_tuple(yver)
    if parsed >= (6, 0, 0):
        rep.warn("PyYAML Loader compatibility", "version {0} may make yaml.load(stream) fail without Loader".format(yver))
    elif parsed >= (5, 1, 0):
        rep.warn("PyYAML Loader compatibility", "version {0} may warn for yaml.load(stream) without Loader".format(yver))
    else:
        rep.ok("PyYAML Loader compatibility", "version {0}".format(yver))


def check_cuda_runtime(rep, loaded, expect_cuda):
    if not expect_cuda:
        rep.info("CUDA runtime probe", "skipped; pass --expect-cuda to check availability without tensor allocation")
        return
    torch = loaded.get("torch")
    if torch is None:
        rep.fail("CUDA runtime probe", "PyTorch import failed")
        return
    try:
        available = torch.cuda.is_available()
    except Exception as exc:
        rep.fail("torch.cuda.is_available", "{0}: {1}".format(exc.__class__.__name__, exc))
        return
    if not available:
        rep.fail("CUDA availability", "torch.cuda.is_available() is False; MUNIT execution scripts call .cuda()")
        return
    rep.ok("CUDA availability", "torch reports CUDA available")
    try:
        count = torch.cuda.device_count()
        rep.info("CUDA device count", str(count))
    except Exception as exc:
        rep.warn("CUDA device count", str(exc))
        count = 0
    cuda_compiled = getattr(getattr(torch, "version", None), "cuda", None)
    for idx in range(int(count or 0)):
        try:
            name = torch.cuda.get_device_name(idx)
        except Exception:
            name = "unknown"
        try:
            cap = torch.cuda.get_device_capability(idx)
            rep.info("CUDA device {0}".format(idx), "{0}; compute capability {1}.{2}".format(name, cap[0], cap[1]))
            if cuda_compiled and parse_version_tuple(str(cuda_compiled))[0] < 11 and cap[0] >= 8:
                rep.warn(
                    "modern GPU with legacy CUDA",
                    "device compute capability {0}.{1} is unlikely to work with CUDA {2}/PyTorch 0.4.1".format(cap[0], cap[1], cuda_compiled),
                )
        except Exception as exc:
            rep.warn("CUDA device {0} capability".format(idx), str(exc))


def read_text(path):
    try:
        with open(path, "rb") as fh:
            data = fh.read()
        try:
            return data.decode("utf-8")
        except Exception:
            return data.decode("latin-1")
    except Exception:
        return None


def check_repo_static(rep, repo_root, loaded):
    if not repo_root:
        rep.info("repository static checks", "skipped; pass --repo-root to inspect files")
        return
    root = os.path.abspath(repo_root)
    if not os.path.isdir(root):
        rep.fail("repo root", "not a directory: {0}".format(root))
        return
    rep.ok("repo root", root)
    required = ["README.md", "USAGE.md", "TUTORIAL.md", "Dockerfile", "train.py", "test.py", "test_batch.py", "trainer.py", "networks.py", "data.py", "utils.py"]
    for rel in required:
        path = os.path.join(root, rel)
        if os.path.exists(path):
            rep.ok("file {0}".format(rel), "present")
        else:
            rep.warn("file {0}".format(rel), "missing from supplied repo root")

    utils_text = read_text(os.path.join(root, "utils.py")) or ""
    if "torch.utils.serialization" in utils_text and "load_lua" in utils_text:
        rep.info("utils.py load_lua dependency", "present; modern PyTorch import will fail unless load_lua exists")
    else:
        rep.warn("utils.py load_lua dependency", "not found; checkout may be patched or not MUNIT-compatible")

    cuda_hits = []
    for rel in ["train.py", "test.py", "test_batch.py", "trainer.py", "networks.py", "utils.py"]:
        text = read_text(os.path.join(root, rel)) or ""
        if ".cuda(" in text or ".cuda()" in text or "torch.cuda" in text:
            cuda_hits.append(rel)
    if cuda_hits:
        rep.info("static CUDA-only paths", ", ".join(sorted(set(cuda_hits))))
    else:
        rep.warn("static CUDA-only paths", "none found; checkout may be patched")

    yaml_mod = loaded.get("yaml")
    config_dir = os.path.join(root, "configs")
    config_paths = sorted(glob.glob(os.path.join(config_dir, "*.yaml")))
    if not config_paths:
        rep.warn("config YAML files", "none found under supplied repo root")
    elif yaml_mod is None:
        rep.warn("config YAML parse", "skipped because PyYAML import failed")
    else:
        bad = []
        for path in config_paths:
            try:
                text = read_text(path)
                if hasattr(yaml_mod, "safe_load"):
                    yaml_mod.safe_load(text)
                else:
                    yaml_mod.load(text)
            except Exception as exc:
                bad.append("{0}: {1}".format(os.path.basename(path), exc))
        if bad:
            rep.fail("config YAML parse", "; ".join(bad))
        else:
            rep.ok("config YAML parse", "{0} files parsed with safe loader".format(len(config_paths)))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Safe dependency/static checker for legacy NVlabs/MUNIT environments.")
    parser.add_argument("--repo-root", default=None, help="Optional MUNIT checkout root for static file/config checks.")
    parser.add_argument("--expect-cuda", action="store_true", help="Probe CUDA availability/device metadata without allocating tensors.")
    parser.add_argument("--show-tracebacks", action="store_true", help="Print tracebacks for unexpected checker errors.")
    args = parser.parse_args(argv)

    rep = Reporter()
    rep.info("legacy targets", ", ".join(["{0}={1}".format(k, v) for k, v in sorted(LEGACY_TARGETS.items())]))
    try:
        check_python(rep)
        loaded = check_required_imports(rep)
        check_torch_compat(rep, loaded)
        check_torchvision_compat(rep, loaded)
        check_yaml_compat(rep, loaded)
        check_cuda_runtime(rep, loaded, args.expect_cuda)
        check_repo_static(rep, args.repo_root, loaded)
    except Exception as exc:
        rep.fail("checker internal error", "{0}: {1}".format(exc.__class__.__name__, exc))
        if args.show_tracebacks:
            traceback.print_exc()
    rep.info("summary", "{0} failure(s), {1} warning(s)".format(rep.failures, rep.warnings))
    return 2 if rep.failures else 0


if __name__ == "__main__":
    sys.exit(main())
