#!/usr/bin/env python3
"""Check an installed X-AnyLabeling runtime without launching the GUI.

The helper reports package identity, CLI availability, conversion task count,
ONNX Runtime providers, and optionally the no-download model registry count. It
is safe for CPU/headless environments and does not load model weights.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from importlib import metadata
from pathlib import Path
from typing import Any, Dict


def run_command(command: list[str], timeout: int = 20) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:  # pragma: no cover - defensive reporting
        return {"command": command, "returncode": None, "error": str(exc)}


def inspect_model_registry(work_dir: str | None) -> Dict[str, Any]:
    # Import lazily so basic checks still work if Qt-heavy modules have issues.
    from anylabeling import config as xal_config
    from anylabeling.services.auto_labeling.model_manager import ModelManager

    temp_dir_obj = None
    if work_dir is None:
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="xanylabeling-registry-")
        work_dir = temp_dir_obj.name

    try:
        xal_config.set_work_directory(work_dir)
        xal_config.current_config_file = os.path.join(work_dir, ".xanylabelingrc")
        manager = ModelManager()
        configs = manager.get_model_configs()
        type_counts = Counter(str(item.get("type", "")) for item in configs)
        names = [str(item.get("name", "")) for item in configs]
        duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
        return {
            "status": "ok",
            "count": len(configs),
            "type_count": len(type_counts),
            "top_types": type_counts.most_common(20),
            "duplicate_names": duplicates,
            "custom_name_examples": {
                "valid_custom_yolo_1": ModelManager.is_valid_custom_model_name("custom_yolo-1.0"),
                "invalid_path_segment": ModelManager.is_valid_custom_model_name("../bad"),
            },
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    finally:
        if temp_dir_obj is not None:
            temp_dir_obj.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an installed X-AnyLabeling runtime safely.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human summary.")
    parser.add_argument("--show-model-registry", action="store_true", help="Inspect model configs without loading weights.")
    parser.add_argument("--work-dir", help="Temporary or project work directory for config-backed registry inspection.")
    parser.add_argument("--xanylabeling-bin", default="xanylabeling", help="CLI executable to check.")
    args = parser.parse_args()

    report: Dict[str, Any] = {"python": sys.version, "executable": sys.executable}

    try:
        import anylabeling
        import anylabeling.app_info as app_info
        from anylabeling.views.common import converter

        report["package"] = {
            "distribution": "x-anylabeling-cvhub",
            "distribution_version": metadata.version("x-anylabeling-cvhub"),
            "app_version": app_info.__version__,
            "import_ok": True,
            "module_file": str(Path(anylabeling.__file__).name),
        }
        report["conversion_tasks"] = len(converter.SUPPORTED_TASKS)
    except Exception as exc:
        report["package"] = {"import_ok": False, "error": str(exc)}

    cli_path = shutil.which(args.xanylabeling_bin) or args.xanylabeling_bin
    report["cli"] = {
        "path": cli_path,
        "version": run_command([cli_path, "version"]),
        "convert_list": run_command([cli_path, "convert"]),
    }

    try:
        import onnxruntime as ort

        report["onnxruntime"] = {
            "version": getattr(ort, "__version__", None),
            "providers": ort.get_available_providers(),
        }
    except Exception as exc:
        report["onnxruntime"] = {"error": str(exc)}

    if args.show_model_registry:
        report["model_registry"] = inspect_model_registry(args.work_dir)

    ok = bool(report.get("package", {}).get("import_ok"))
    ok = ok and report.get("cli", {}).get("version", {}).get("returncode") == 0
    ok = ok and report.get("cli", {}).get("convert_list", {}).get("returncode") == 0
    if args.show_model_registry:
        ok = ok and report.get("model_registry", {}).get("status") == "ok"
    report["status"] = "ok" if ok else "error"

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        pkg = report.get("package", {})
        print(f"package: {pkg.get('distribution')} {pkg.get('distribution_version')} app={pkg.get('app_version')}")
        print(f"conversion tasks: {report.get('conversion_tasks')}")
        print(f"cli version rc: {report['cli']['version'].get('returncode')}")
        print(f"cli convert rc: {report['cli']['convert_list'].get('returncode')}")
        ort = report.get("onnxruntime", {})
        print(f"onnxruntime providers: {', '.join(ort.get('providers', [])) if 'providers' in ort else ort.get('error')}")
        if args.show_model_registry:
            registry = report.get("model_registry", {})
            print(f"model registry: {registry.get('status')} count={registry.get('count')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
