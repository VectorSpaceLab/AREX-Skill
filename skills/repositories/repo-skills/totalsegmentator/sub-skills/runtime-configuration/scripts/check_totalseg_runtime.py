#!/usr/bin/env python3
"""Safe TotalSegmentator runtime diagnostic.

This helper imports TotalSegmentator metadata, the safe task registry, config path
helpers when available, and PyTorch backend visibility when installed. It never
downloads model weights, validates licenses against the network, writes config,
or runs segmentation.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


LICENSE_PATTERN = re.compile(r"^aca_.{14}$")
GPU_INDEX_PATTERN = re.compile(r"^gpu:(\d+)$")
VALID_DEVICES = {"cpu", "gpu", "mps"}


def _path_status(path: Path, show_paths: bool) -> Dict[str, Any]:
    status: Dict[str, Any] = {
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
    }
    if show_paths:
        status["path"] = str(path)
    else:
        status["path_redacted"] = True
        status["name"] = path.name
    return status


def _read_config(config_file: Path) -> Optional[Dict[str, Any]]:
    if not config_file.exists():
        return None
    try:
        config = json.loads(config_file.read_text())
    except Exception as exc:  # noqa: BLE001 - diagnostics should report parser failures.
        return {"read_error": f"{type(exc).__name__}: {exc}"}

    safe_config: Dict[str, Any] = {}
    for key in ("totalseg_id", "send_usage_stats", "prediction_counter", "statistics_disclaimer_shown"):
        if key in config:
            safe_config[key] = config[key]

    license_number = config.get("license_number")
    safe_config["license_number_present"] = bool(license_number)
    safe_config["license_number_shape_valid"] = bool(
        isinstance(license_number, str) and LICENSE_PATTERN.match(license_number)
    )
    return safe_config


def _metadata_version(distribution: str) -> Optional[str]:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _fallback_totalseg_dir() -> Path:
    if "TOTALSEG_HOME_DIR" in os.environ:
        return Path(os.environ["TOTALSEG_HOME_DIR"])
    home_path = Path("/tmp") if str(Path.home()) == "/" else Path.home()
    return home_path / ".totalsegmentator"


def _fallback_weights_dir() -> Path:
    if "TOTALSEG_WEIGHTS_PATH" in os.environ:
        return Path(os.environ["TOTALSEG_WEIGHTS_PATH"])
    return _fallback_totalseg_dir() / "nnunet/results"


def _device_request_status(device: str, torch_module: Any) -> Dict[str, Any]:
    status: Dict[str, Any] = {"requested": device, "valid_string": False}

    match = GPU_INDEX_PATTERN.match(device)
    if device in VALID_DEVICES or match:
        status["valid_string"] = True
    else:
        status["error"] = "invalid device string; expected cpu, gpu, gpu:N, or mps"
        return status

    if torch_module is None:
        status["availability"] = "torch unavailable"
        return status

    cuda_available = bool(torch_module.cuda.is_available())
    cuda_count = int(torch_module.cuda.device_count()) if cuda_available else 0
    status["cuda_available"] = cuda_available
    status["cuda_device_count"] = cuda_count

    mps_backend = getattr(torch_module.backends, "mps", None)
    mps_available = bool(mps_backend and torch_module.backends.mps.is_available())
    status["mps_available"] = mps_available

    if device == "cpu":
        status["would_resolve_to"] = "cpu"
    elif device == "mps":
        status["would_resolve_to"] = "mps" if mps_available else "mps_requested_but_unavailable_or_unverified"
    elif device == "gpu":
        status["would_resolve_to"] = "cuda:0" if cuda_available and cuda_count > 0 else "cpu_fallback"
    elif match:
        index = int(match.group(1))
        status["gpu_index"] = index
        status["would_resolve_to"] = f"cuda:{index}" if cuda_available and index < cuda_count else "cpu_fallback"

    return status


def _import_registry() -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    result: Dict[str, Any] = {
        "distribution": "TotalSegmentator",
        "distribution_version": _metadata_version("TotalSegmentator"),
    }

    try:
        from totalsegmentator.registry import (
            get_task_classes,
            list_tasks,
            requires_license,
            task_modality,
            task_registry,
        )
    except Exception as exc:  # noqa: BLE001 - import diagnostics are the point.
        result["registry_import_status"] = "failed"
        result["registry_import_error"] = f"{type(exc).__name__}: {exc}"
        return result, None

    registry = task_registry()
    tasks = list_tasks()
    result.update(
        {
            "registry_import_status": "ok",
            "registry_task_count": len(registry.get("tasks", {})),
            "licensed_task_count": sum(1 for task in tasks if task.get("license_required")),
            "known_reference_counts": {
                "total_classes": len(get_task_classes("total")),
                "total_mr_classes": len(get_task_classes("total_mr")),
            },
        }
    )

    helpers = {
        "get_task_classes": get_task_classes,
        "requires_license": requires_license,
        "task_modality": task_modality,
        "registry": registry,
    }
    return result, helpers


def _resolve_runtime_paths() -> Tuple[Dict[str, Any], Path, Path]:
    try:
        from totalsegmentator.config import get_totalseg_dir, get_weights_dir
    except Exception as exc:  # noqa: BLE001 - fallback path reporting is still useful.
        return (
            {
                "config_helper_status": "failed",
                "config_helper_error": f"{type(exc).__name__}: {exc}",
                "path_resolution": "fallback_from_documented_environment_rules",
            },
            _fallback_totalseg_dir(),
            _fallback_weights_dir(),
        )

    return (
        {"config_helper_status": "ok", "path_resolution": "totalsegmentator.config"},
        Path(get_totalseg_dir()),
        Path(get_weights_dir()),
    )


def _build_report(args: argparse.Namespace) -> Dict[str, Any]:
    report, registry_helpers = _import_registry()

    torch_module = None
    try:
        import torch
    except Exception as exc:  # noqa: BLE001 - optional backend report.
        report["torch"] = {"import_status": "failed", "import_error": f"{type(exc).__name__}: {exc}"}
    else:
        torch_module = torch
        mps_backend = getattr(torch.backends, "mps", None)
        report["torch"] = {
            "import_status": "ok",
            "version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "mps_available": bool(mps_backend and torch.backends.mps.is_available()),
        }

    report["device_request"] = _device_request_status(args.device, torch_module)

    path_resolution, home_dir, weights_dir = _resolve_runtime_paths()
    report.update(path_resolution)
    config_file = home_dir / "config.json"
    report["environment"] = {
        "TOTALSEG_HOME_DIR_set": "TOTALSEG_HOME_DIR" in os.environ,
        "TOTALSEG_WEIGHTS_PATH_set": "TOTALSEG_WEIGHTS_PATH" in os.environ,
    }
    report["paths"] = {
        "totalseg_home": _path_status(home_dir, args.show_paths),
        "weights_dir": _path_status(weights_dir, args.show_paths),
        "config_file": _path_status(config_file, args.show_paths),
    }
    report["config_summary"] = _read_config(config_file)

    if args.task:
        if registry_helpers is None:
            report["task"] = {
                "name": args.task,
                "known": None,
                "error": "task validation unavailable because registry import failed",
            }
        else:
            tasks = registry_helpers["registry"].get("tasks", {})
            task_info = tasks.get(args.task)
            if task_info is None:
                report["task"] = {
                    "name": args.task,
                    "known": False,
                    "valid_tasks_sample": sorted(tasks)[:10],
                    "valid_task_count": len(tasks),
                }
            else:
                task_summary = {
                    "name": args.task,
                    "known": True,
                    "modality": registry_helpers["task_modality"](args.task),
                    "license_required": registry_helpers["requires_license"](args.task),
                    "num_classes": len(registry_helpers["get_task_classes"](args.task)),
                }
                if args.offline:
                    config_summary = report.get("config_summary") or {}
                    task_summary["offline_license_shape_ok"] = bool(
                        (not task_summary["license_required"]) or config_summary.get("license_number_shape_valid")
                    )
                    task_summary["weights_dir_exists"] = weights_dir.exists()
                report["task"] = task_summary

    report["runtime_ready"] = bool(
        report.get("registry_import_status") == "ok"
        and report.get("torch", {}).get("import_status") == "ok"
        and report.get("config_helper_status") == "ok"
    )
    return report


def _print_text(report: Dict[str, Any]) -> None:
    print("TotalSegmentator runtime diagnostic")
    print(f"distribution_version={report.get('distribution_version') or 'unknown'}")
    print(f"registry_import_status={report.get('registry_import_status')}")
    if report.get("registry_import_error"):
        print(f"registry_import_error={report['registry_import_error']}")

    print(f"config_helper_status={report.get('config_helper_status')}")
    if report.get("config_helper_error"):
        print(f"config_helper_error={report['config_helper_error']}")

    if report.get("registry_import_status") == "ok":
        print(f"registry_task_count={report.get('registry_task_count')}")
        print(f"licensed_task_count={report.get('licensed_task_count')}")
        counts = report.get("known_reference_counts", {})
        print(f"total_classes={counts.get('total_classes')}")
        print(f"total_mr_classes={counts.get('total_mr_classes')}")

    torch_info = report.get("torch", {})
    print(f"torch_status={torch_info.get('import_status')}")
    if torch_info.get("import_status") == "ok":
        print(f"torch_version={torch_info.get('version')}")
        print(f"cuda_available={torch_info.get('cuda_available')}")
        print(f"cuda_device_count={torch_info.get('cuda_device_count')}")
        print(f"mps_available={torch_info.get('mps_available')}")
    elif torch_info.get("import_error"):
        print(f"torch_error={torch_info.get('import_error')}")

    device = report.get("device_request", {})
    print(f"device_requested={device.get('requested')}")
    print(f"device_valid={device.get('valid_string')}")
    print(f"device_would_resolve_to={device.get('would_resolve_to', device.get('availability', device.get('error')))}")

    environment = report.get("environment", {})
    print(f"TOTALSEG_HOME_DIR_set={environment.get('TOTALSEG_HOME_DIR_set')}")
    print(f"TOTALSEG_WEIGHTS_PATH_set={environment.get('TOTALSEG_WEIGHTS_PATH_set')}")

    for key, status in (report.get("paths") or {}).items():
        print(f"{key}=" + json.dumps(status, sort_keys=True))

    config = report.get("config_summary")
    print("config_summary=" + json.dumps(config, sort_keys=True))

    if "task" in report:
        print("task=" + json.dumps(report["task"], sort_keys=True))

    print(f"runtime_ready={report.get('runtime_ready')}")


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect TotalSegmentator package, registry, config, weights path, "
            "task license flag, and PyTorch backend visibility without downloading weights or running models."
        )
    )
    parser.add_argument("--task", help="Optional task name to validate against the safe registry.")
    parser.add_argument(
        "--device",
        default="gpu",
        help="Requested device string to evaluate without running inference: cpu, gpu, gpu:N, or mps. Default: gpu.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="For --task checks, also report local offline readiness hints for license shape and weights directory existence.",
    )
    parser.add_argument(
        "--show-paths",
        action="store_true",
        help="Include absolute TotalSegmentator config/weights paths. Omit for redacted, share-safe diagnostics.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    report = _build_report(args)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)

    if not report.get("device_request", {}).get("valid_string", False):
        return 2
    if report.get("task", {}).get("known") is False:
        return 2
    if report.get("registry_import_status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
