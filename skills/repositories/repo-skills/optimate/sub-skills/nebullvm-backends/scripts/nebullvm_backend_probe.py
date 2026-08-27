#!/usr/bin/env python3
"""Safe selector/device probe for NebullVM backend support.

Example:
  python scripts/nebullvm_backend_probe.py --frameworks torch --backends onnx --compilers all
"""

from __future__ import annotations

import argparse
import importlib
import json
from importlib import metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frameworks", nargs="*", default=["torch"], help="Frameworks to request from the selector")
    parser.add_argument("--backends", nargs="*", default=["all"], help="Backends to request from the selector")
    parser.add_argument("--compilers", nargs="*", default=["all"], help="Compilers to request from the selector")
    parser.add_argument("--check-device", default="cuda", help="Device string to parse with check_device")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    report = {"imports": {}, "selectors": {}, "device": None}
    try:
        import nebullvm
        from nebullvm.installers.auto_installer import (
            select_compilers_to_install,
            select_frameworks_to_install,
        )
        from nebullvm.tools.data import DataManager
        from nebullvm.tools.utils import check_device

        report["imports"]["nebullvm"] = {
            "status": "ok",
            "version": metadata.version("nebullvm"),
            "file": getattr(nebullvm, "__file__", None),
        }
        frameworks_arg = args.frameworks[0] if len(args.frameworks) == 1 and args.frameworks[0] == "all" else args.frameworks
        backends_arg = args.backends[0] if len(args.backends) == 1 and args.backends[0] == "all" else args.backends
        compilers_arg = args.compilers[0] if len(args.compilers) == 1 and args.compilers[0] == "all" else args.compilers
        framework_list = select_frameworks_to_install(frameworks_arg, backends_arg)
        compiler_list = select_compilers_to_install(compilers_arg, framework_list)
        report["selectors"]["frameworks"] = framework_list
        report["selectors"]["compilers"] = compiler_list
        report["device"] = {
            "requested": args.check_device,
            "parsed": check_device(args.check_device).to_torch_format(),
        }
        report["data_manager_example"] = len(DataManager([((0,), None)]))
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
