#!/usr/bin/env python3
"""Safely check DVC importability, console help, version, and optional backends.

Example:
  python scripts/check_dvc_install.py --scheme s3 --check-cli
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Backend:
    extra: str
    distributions: tuple[str, ...]
    imports: tuple[str, ...]


BACKENDS = {
    "azure": Backend("azure", ("dvc-azure",), ("dvc_azure",)),
    "gdrive": Backend("gdrive", ("dvc-gdrive",), ("dvc_gdrive",)),
    "gs": Backend("gs", ("dvc-gs",), ("dvc_gs",)),
    "hdfs": Backend("hdfs", ("dvc-hdfs",), ("dvc_hdfs",)),
    "oss": Backend("oss", ("dvc-oss",), ("dvc_oss",)),
    "s3": Backend("s3", ("dvc-s3",), ("dvc_s3",)),
    "ssh": Backend("ssh", ("dvc-ssh",), ("dvc_ssh",)),
    "webdav": Backend("webdav", ("dvc-webdav",), ("dvc_webdav",)),
    "webdavs": Backend("webdav", ("dvc-webdav",), ("dvc_webdav",)),
    "webhdfs": Backend("webhdfs", ("dvc-webhdfs",), ("dvc_webhdfs",)),
}


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_ok(name: str) -> bool:
    try:
        importlib.import_module(name)
    except Exception:
        return False
    return True


def backend_report(scheme: str) -> dict:
    normalized = scheme.split(":", 1)[0].lower()
    backend = BACKENDS.get(normalized)
    if not backend:
        return {
            "scheme": scheme,
            "known_optional_backend": False,
            "message": "Core DVC may handle this scheme directly, or this skill has no optional-extra mapping for it.",
        }
    distributions = {name: dist_version(name) for name in backend.distributions}
    imports = {name: import_ok(name) for name in backend.imports}
    installed = any(distributions.values()) or any(imports.values())
    return {
        "scheme": scheme,
        "known_optional_backend": True,
        "extra": backend.extra,
        "installed": installed,
        "distributions": distributions,
        "imports": imports,
        "install_hint": None if installed else f"pip install 'dvc[{backend.extra}]'",
    }


def run_cli_help() -> dict:
    executable = shutil.which("dvc")
    if not executable:
        return {"found": False, "returncode": None, "first_line": None}
    proc = subprocess.run(
        [executable, "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    first_line = (proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr) else ""
    return {"found": True, "path": executable, "returncode": proc.returncode, "first_line": first_line}


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely check DVC import, CLI, and optional backend availability.")
    parser.add_argument("--scheme", action="append", default=[], help="Optional remote scheme or URL to inspect, such as s3 or gs://bucket/path.")
    parser.add_argument("--check-cli", action="store_true", help="Run `dvc --help` if the console script is on PATH.")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation; use 0 for compact output.")
    args = parser.parse_args()

    result = {
        "python": sys.version.split()[0],
        "dvc_distribution_version": dist_version("dvc"),
        "dvc_import_ok": import_ok("dvc"),
        "cli": run_cli_help() if args.check_cli else "skipped",
        "backends": [backend_report(scheme) for scheme in args.scheme],
    }
    print(json.dumps(result, indent=None if args.indent == 0 else args.indent, sort_keys=True))
    return 0 if result["dvc_import_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
