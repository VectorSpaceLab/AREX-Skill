#!/usr/bin/env python3
"""Read-only VoxFormer environment and native-readiness checker.

This script deliberately does not install packages, build extensions, download
files, run project CLIs, or print repository/environment paths in normal
output. It reports observations; use --strict when a calling check needs a
non-zero exit for an unmet core gate.
"""

from __future__ import print_function

import argparse
import contextlib
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, Iterable, Optional, Tuple

try:
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover - for older Python 3.8 patches
    import importlib_metadata  # type: ignore


EXPECTED = {
    "torch": "1.9.1",
    "torchvision": "0.10.1",
    "mmcv-full": "1.4.0",
    "mmdet": "2.14.0",
    "mmsegmentation": "0.14.1",
    "mmdetection3d": "0.17.1",
    "timm": "0.6.13",
}

# Distribution names have changed across old editable-install metadata.
DIST_CANDIDATES = {
    "mmdetection3d": ("mmdetection3d", "mmdet3d"),
}


def quiet_import(module_name: str) -> Tuple[bool, Optional[str]]:
    """Import a module while hiding incidental legacy import output."""
    sink = open(os.devnull, "w")
    try:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            importlib.import_module(module_name)
        return True, None
    except Exception as exc:  # report type only; messages can contain paths
        return False, type(exc).__name__
    finally:
        sink.close()


def distribution_version(name: str) -> Optional[str]:
    names: Iterable[str] = DIST_CANDIDATES.get(name, (name,))
    for candidate in names:
        try:
            return importlib_metadata.version(candidate)
        except importlib_metadata.PackageNotFoundError:
            continue
        except Exception:
            return None
    return None


def base_version(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.split("+", 1)[0]


def version_status(actual: Optional[str], expected: str) -> str:
    if actual is None:
        return "MISSING"
    if base_version(actual) == expected:
        return "OK"
    return "MISMATCH"


def tool_version(executable: str) -> Optional[str]:
    """Return one redacted version line without exposing executable paths."""
    command = shutil.which(executable)
    if not command:
        return None
    try:
        result = subprocess.run(
            [command, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=4,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "available"
    line = (result.stdout or "").splitlines()
    if not line:
        return "available"
    # Tool banners occasionally include an installation prefix. Keep only a
    # human-readable version signal and redact path-shaped tokens.
    cleaned = re.sub(r"(?:[A-Za-z]:[\\/]|/)[^\s]+", "<path>", line[0])
    return cleaned[:160]


def add_package_records(records: Dict[str, Any]) -> None:
    for name, expected in EXPECTED.items():
        actual = distribution_version(name)
        records["packages"][name] = {
            "status": version_status(actual, expected),
            "expected": expected,
            "installed": actual,
        }


def add_import_record(records: Dict[str, Any], label: str, module: str) -> bool:
    ok, error_type = quiet_import(module)
    records["imports"][label] = {
        "status": "READY" if ok else "FAILED",
        "module": module,
    }
    if error_type:
        records["imports"][label]["error_type"] = error_type
    return ok


def add_torch_records(records: Dict[str, Any]) -> Optional[Any]:
    try:
        sink = open(os.devnull, "w")
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            torch = importlib.import_module("torch")
        sink.close()
    except Exception as exc:
        records["backend"] = {
            "status": "FAILED",
            "torch_import": "FAILED",
            "error_type": type(exc).__name__,
        }
        return None

    cuda_available = False
    device_count = 0
    capabilities = []
    try:
        cuda_available = bool(torch.cuda.is_available())
        if cuda_available:
            device_count = int(torch.cuda.device_count())
            for index in range(device_count):
                major, minor = torch.cuda.get_device_capability(index)
                capabilities.append("{}.{}".format(major, minor))
    except Exception as exc:
        records["backend"] = {
            "status": "FAILED",
            "torch_import": "READY",
            "torch": getattr(torch, "__version__", None),
            "torch_cuda_runtime": getattr(getattr(torch, "version", None), "cuda", None),
            "cuda_available": "ERROR",
            "error_type": type(exc).__name__,
        }
        return torch

    cuda_home = None
    try:
        from torch.utils.cpp_extension import CUDA_HOME
        cuda_home = bool(CUDA_HOME)
    except Exception:
        cuda_home = False

    records["backend"] = {
        "status": "READY" if cuda_available else "CPU_ONLY",
        "torch_import": "READY",
        "torch": getattr(torch, "__version__", None),
        "torch_cuda_runtime": getattr(getattr(torch, "version", None), "cuda", None),
        "cuda_available": cuda_available,
        "cuda_device_count": device_count,
        "device_capabilities": capabilities,
        "cuda_home_configured": cuda_home,
        "cuda_model_substitute": "none",
    }
    return torch


def add_toolchain_records(records: Dict[str, Any]) -> None:
    records["toolchain"] = {}
    for executable in ("nvcc", "gcc", "g++", "ninja"):
        value = tool_version(executable)
        records["toolchain"][executable] = {
            "status": "AVAILABLE" if value else "MISSING",
            "version": value,
        }


def source_placeholder_state(repo_root: Path) -> str:
    source_file = repo_root / "projects" / "mmdet3d_plugin" / "voxformer" / "modules" / "multi_scale_deformable_attn_3D_custom_function.py"
    try:
        text = source_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "SOURCE_NOT_FOUND"
    placeholder = "/" + "path/to/directory_containing_so_file"
    if "raise NotImplementedError" in text and placeholder in text:
        return "BLOCKED_PLACEHOLDER"
    return "PATH_RESOLUTION_NOT_DETECTED"


def add_project_records(records: Dict[str, Any], repo_root: Path) -> None:
    state = source_placeholder_state(repo_root)
    records["project"] = {
        "custom_wrapper": state,
        "unmodified_placeholder_import_claim": "never_claim_ready",
    }

    if state == "BLOCKED_PLACEHOLDER":
        records["project"]["plugin_import"] = "BLOCKED_PLACEHOLDER"
        return
    if state == "SOURCE_NOT_FOUND":
        records["project"]["plugin_import"] = "SOURCE_NOT_FOUND"
        return

    root_text = str(repo_root)
    inserted = False
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
        inserted = True
    try:
        ok, error_type = quiet_import("projects.mmdet3d_plugin")
        records["project"]["plugin_import"] = "READY" if ok else "FAILED"
        if error_type:
            records["project"]["plugin_import_error_type"] = error_type
    finally:
        if inserted:
            try:
                sys.path.remove(root_text)
            except ValueError:
                pass


def add_deform_records(records: Dict[str, Any], repo_root: Path) -> None:
    extension_dir = repo_root / "deform_attn_3d"
    record: Dict[str, Any] = {
        "status": "NOT_FOUND",
        "source_build": "not_run",
        "cpu_substitute": "none",
    }
    if extension_dir.is_dir():
        artifacts = list(extension_dir.glob("deform3dattn_custom_cn*.so"))
        record["artifact_present"] = bool(artifacts)
        if artifacts:
            extension_text = str(extension_dir)
            inserted = False
            if extension_text not in sys.path:
                sys.path.insert(0, extension_text)
                inserted = True
            try:
                ok, error_type = quiet_import("deform3dattn_custom_cn")
                record["status"] = "READY" if ok else "FAILED"
                if ok:
                    module = sys.modules.get("deform3dattn_custom_cn")
                    symbols = (
                        hasattr(module, "ms_deform_attn_forward"),
                        hasattr(module, "ms_deform_attn_backward"),
                    ) if module is not None else (False, False)
                    record["forward_symbol"] = symbols[0]
                    record["backward_symbol"] = symbols[1]
                    if not all(symbols):
                        record["status"] = "FAILED"
                elif error_type:
                    record["error_type"] = error_type
            finally:
                if inserted:
                    try:
                        sys.path.remove(extension_text)
                    except ValueError:
                        pass
        else:
            record["status"] = "MISSING_ARTIFACT"
    records["deform3d"] = record


def render_text(records: Dict[str, Any]) -> str:
    lines = ["VoxFormer environment check (read-only)"]
    lines.append("Packages:")
    for name, item in records["packages"].items():
        installed = item["installed"] or "not installed"
        lines.append("  {:16} {:10} installed={} expected={}".format(
            name + ":", item["status"], installed, item["expected"]))

    backend = records["backend"]
    lines.append("Backend:")
    lines.append("  status={} torch={} torch_cuda_runtime={} cuda_available={} devices={} capabilities={} cuda_home_configured={}".format(
        backend.get("status"), backend.get("torch"), backend.get("torch_cuda_runtime"),
        backend.get("cuda_available"), backend.get("cuda_device_count", 0),
        ",".join(backend.get("device_capabilities", [])) or "none",
        backend.get("cuda_home_configured", False)))

    lines.append("Imports:")
    for label, item in records["imports"].items():
        suffix = " error_type={}".format(item["error_type"]) if "error_type" in item else ""
        lines.append("  {:22} {}{}".format(label + ":", item["status"], suffix))

    lines.append("Toolchain:")
    for name, item in records["toolchain"].items():
        version = item["version"] or "not found"
        lines.append("  {:8} {:10} {}".format(name + ":", item["status"], version))

    project = records["project"]
    lines.append("Project plugin:")
    lines.append("  custom_wrapper={} plugin_import={}".format(
        project["custom_wrapper"], project["plugin_import"]))
    if "plugin_import_error_type" in project:
        lines.append("  plugin_import_error_type={}".format(project["plugin_import_error_type"]))

    deform = records["deform3d"]
    lines.append("Deform3D extension:")
    lines.append("  status={} artifact_present={} source_build={} cpu_substitute={}".format(
        deform["status"], deform.get("artifact_present", False),
        deform["source_build"], deform["cpu_substitute"]))
    if "forward_symbol" in deform:
        lines.append("  symbols forward={} backward={}".format(
            deform["forward_symbol"], deform["backward_symbol"]))
    if "error_type" in deform:
        lines.append("  import_error_type={}".format(deform["error_type"]))

    lines.append("Note: CPU-only or placeholder-blocked results are reported honestly; no build or repair was attempted.")
    return "\n".join(lines)


def strict_failures(records: Dict[str, Any], require_deform3d: bool) -> list:
    failures = []
    for name, item in records["packages"].items():
        if item["status"] != "OK":
            failures.append("package:" + name)
    for label in ("torch", "mmcv", "mmdet", "mmseg", "mmdet3d", "mmdet3d.ops"):
        item = records["imports"].get(label)
        if item is not None and item["status"] != "READY":
            failures.append("import:" + label)
    if records["backend"].get("status") != "READY":
        failures.append("backend:cuda")
    if records["project"].get("plugin_import") != "READY":
        failures.append("project:plugin")
    if require_deform3d and records["deform3d"].get("status") != "READY":
        failures.append("deform3d:extension")
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report VoxFormer package, CUDA, import, and native readiness without modifying the environment."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="VoxFormer checkout to inspect (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable status instead of the normal summary.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when a core CUDA/plugin readiness gate is unmet.",
    )
    parser.add_argument(
        "--require-deform3d",
        action="store_true",
        help="with --strict, require the custom deform3D extension and symbols.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records: Dict[str, Any] = {
        "packages": {},
        "imports": {},
    }
    repo_root = Path(args.repo_root).resolve()

    add_package_records(records)
    torch = add_torch_records(records)
    # Keep these imports independent: a missing torch should not hide which
    # OpenMMLab layer is absent. The module labels are stable and path-free.
    add_import_record(records, "torch", "torch") if torch is None else records["imports"].update({
        "torch": {"status": "READY", "module": "torch"}
    })
    add_import_record(records, "mmcv", "mmcv")
    add_import_record(records, "mmcv.ops", "mmcv.ops.multi_scale_deform_attn")
    add_import_record(records, "mmdet", "mmdet")
    add_import_record(records, "mmseg", "mmseg")
    add_import_record(records, "mmdet3d", "mmdet3d")
    add_import_record(records, "mmdet3d.ops", "mmdet3d.ops")
    add_import_record(records, "timm", "timm")
    add_toolchain_records(records)
    add_project_records(records, repo_root)
    add_deform_records(records, repo_root)

    if args.json:
        print(json.dumps(records, sort_keys=True, indent=2))
    else:
        print(render_text(records))

    if args.strict and strict_failures(records, args.require_deform3d):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
