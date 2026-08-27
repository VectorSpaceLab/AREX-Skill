#!/usr/bin/env python3
"""Check a Python environment for ProLIF usage prerequisites."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from typing import Any


def module_status(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - depends on user env
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    return {"ok": True, "version": str(version) if version is not None else None}


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-plotting",
        action="store_true",
        help="Also check optional plotting/tutorial backends used by ProLIF plots.",
    )
    args = parser.parse_args()

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "modules": {},
        "distributions": {},
    }

    required_modules = ["prolif", "MDAnalysis", "rdkit", "pandas", "numpy", "scipy"]
    optional_modules = ["matplotlib", "py3Dmol", "pyvis", "seaborn"] if args.include_plotting else []

    for name in required_modules + optional_modules:
        report["modules"][name] = module_status(name)

    for name in ["prolif", "MDAnalysis", "rdkit", "pandas", "numpy", "scipy", "gemmi"]:
        report["distributions"][name] = dist_version(name)

    prolif_status = report["modules"].get("prolif", {})
    if prolif_status.get("ok"):
        import prolif as plf

        report["prolif_version"] = getattr(plf, "__version__", None)
        try:
            report["available_interactions"] = plf.Fingerprint.list_available(
                show_bridged=True
            )
        except Exception as exc:  # pragma: no cover - depends on installed package
            report["available_interactions_error"] = f"{type(exc).__name__}: {exc}"

    ok = all(report["modules"][name].get("ok") for name in required_modules)
    report["ok_for_base_prolif"] = bool(ok)
    if args.include_plotting:
        report["ok_for_plotting_imports"] = all(
            report["modules"][name].get("ok") for name in optional_modules
        )

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
