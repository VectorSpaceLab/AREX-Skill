#!/usr/bin/env python3
"""Read-only pyproj import, version, data-directory, and network diagnostic.

The default mode does not create directories, set pyproj configuration, fetch
network resources, or write files. It intentionally reports no process
executable path so its output can be shared without exposing launcher details.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
from pathlib import Path
from typing import Any


_ENV_NAMES = (
    "PROJ_DATA",
    "PROJ_LIB",
    "PROJ_NETWORK",
    "PROJ_CURL_CA_BUNDLE",
    "CURL_CA_BUNDLE",
    "SSL_CERT_FILE",
)


def _path_status(value: str | None) -> dict[str, Any]:
    """Describe path entries without changing them."""
    if not value:
        return {"value": value, "entries": []}
    entries = []
    for raw_entry in value.split(os.pathsep):
        path = Path(raw_entry).expanduser()
        entries.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "is_dir": path.is_dir(),
                "has_proj_db": (path / "proj.db").is_file(),
            }
        )
    return {"value": value, "entries": entries}


def _build_report() -> tuple[dict[str, Any], int]:
    """Import pyproj and collect only read-only observations."""
    report: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "environment": {
            name: _path_status(os.environ.get(name))
            if name in ("PROJ_DATA", "PROJ_LIB")
            else os.environ.get(name)
            for name in _ENV_NAMES
            if name in os.environ
        },
    }
    try:
        import pyproj
        from pyproj import datadir, network
    except Exception as error:  # pragma: no cover - depends on native runtime
        report["status"] = "import-error"
        report["error"] = f"{type(error).__name__}: {error}"
        return report, 1

    report.update(
        {
            "status": "ok",
            "pyproj_version": pyproj.__version__,
            "proj_runtime_version": pyproj.__proj_version__,
            "proj_compiled_version": pyproj.__proj_compiled_version__,
            "versions_match": pyproj.__proj_version__ == pyproj.__proj_compiled_version__,
            "network_enabled": None,
        }
    )
    try:
        report["network_enabled"] = network.is_network_enabled()
    except Exception as error:  # pragma: no cover - native-runtime dependent
        report["network_error"] = f"{type(error).__name__}: {error}"

    try:
        data_dir = datadir.get_data_dir()
    except Exception as error:  # DataDirError or a native data failure
        report["data_dir_error"] = f"{type(error).__name__}: {error}"
        data_dir = None
    report["data_dir"] = data_dir
    report["data_dir_entries"] = _path_status(data_dir)

    # False is deliberate: do not create the user directory during diagnosis.
    try:
        user_dir = datadir.get_user_data_dir(False)
        report["user_data_dir"] = user_dir
        report["user_data_dir_exists"] = Path(user_dir).is_dir()
    except Exception as error:  # pragma: no cover - native-runtime dependent
        report["user_data_dir_error"] = f"{type(error).__name__}: {error}"

    if report.get("data_dir_error") or not report.get("versions_match", False):
        return report, 2
    return report, 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only pyproj/PROJ import, version, data-directory, and "
            "network diagnostic; no downloads or directory creation."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON object instead of human-readable key/value lines.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report, status = _build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for key, value in report.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, sort_keys=True)
            print(f"{key}: {value}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
