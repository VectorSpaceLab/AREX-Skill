#!/usr/bin/env python3
"""Probe a DoWhy environment for core and optional imports.

This script is intentionally read-only. It reports whether the core DoWhy
package and selected optional integrations are importable in the active Python
environment. It does not depend on the repository checkout location.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from importlib import import_module, metadata, util
from typing import Any

DEFAULT_OPTIONAL_MODULES = [
    "pydot",
    "pygraphviz",
    "matplotlib",
    "econml",
    "causalml",
    "tabpfn",
    "torch",
    "torchvision",
    "pytorch_lightning",
    "pymc3",
    "causallearn",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON report instead of human-readable text.",
    )
    parser.add_argument(
        "--import-optional",
        action="store_true",
        help="Import optional modules instead of only checking whether they are discoverable.",
    )
    parser.add_argument(
        "--strict-optional",
        action="store_true",
        help="Return a non-zero status if any requested optional module is missing.",
    )
    parser.add_argument(
        "--modules",
        default=",".join(DEFAULT_OPTIONAL_MODULES),
        help="Comma-separated optional module names to probe.",
    )
    return parser.parse_args()


def _check_core() -> dict[str, Any]:
    result: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dowhy": {"available": False},
        "gcm": {"available": False},
        "api": {"available": False},
        "CausalModel": {"available": False},
    }
    try:
        result["dowhy"]["version"] = metadata.version("dowhy")
    except metadata.PackageNotFoundError:
        result["dowhy"]["version"] = None

    try:
        import dowhy

        result["dowhy"].update({"available": True, "module": dowhy.__name__})
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["dowhy"]["error"] = f"{type(exc).__name__}: {exc}"
        return result

    try:
        from dowhy import CausalModel

        result["CausalModel"].update({"available": True, "name": CausalModel.__name__})
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["CausalModel"]["error"] = f"{type(exc).__name__}: {exc}"

    try:
        import dowhy.api  # noqa: F401

        result["api"].update({"available": True})
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["api"]["error"] = f"{type(exc).__name__}: {exc}"

    try:
        from dowhy import gcm

        result["gcm"].update({"available": True, "module": gcm.__name__})
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["gcm"]["error"] = f"{type(exc).__name__}: {exc}"

    return result


def _probe_optional(module_name: str, import_optional: bool) -> dict[str, Any]:
    record: dict[str, Any] = {"module": module_name}
    spec = util.find_spec(module_name)
    if spec is None:
        record["available"] = False
        record["error"] = "module not found"
        return record

    record["available"] = True
    if not import_optional:
        record["checked_by"] = "find_spec"
        return record

    try:
        import_module(module_name)
        record["checked_by"] = "import"
    except Exception as exc:  # pragma: no cover - diagnostic path
        record["available"] = False
        record["error"] = f"{type(exc).__name__}: {exc}"
    return record


def main() -> int:
    args = parse_args()
    module_names = [name.strip() for name in args.modules.split(",") if name.strip()]

    core = _check_core()
    optional = [_probe_optional(name, args.import_optional) for name in module_names]

    core_ok = all(core[key].get("available") for key in ("dowhy", "gcm", "api", "CausalModel"))
    optional_missing = [item["module"] for item in optional if not item.get("available", False)]

    report = {
        "core_ok": core_ok,
        "core": core,
        "optional": optional,
        "optional_missing": optional_missing,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("DoWhy environment probe")
        print(f"python={core['python']}")
        print(f"dowhy_version={core['dowhy'].get('version')}")
        print(f"core_ok={core_ok}")
        for key in ("dowhy", "CausalModel", "api", "gcm"):
            item = core[key]
            status = "ok" if item.get("available") else f"missing: {item.get('error')}"
            print(f"{key}={status}")
        if optional_missing:
            print("optional_missing=" + ", ".join(optional_missing))
        else:
            print("optional_missing=none")

    if not core_ok:
        return 2
    if args.strict_optional and optional_missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
