#!/usr/bin/env python3
"""Check PySyft package imports, metadata, and safe CLI help."""
from __future__ import annotations
import argparse
import importlib
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version

DISTS = [
    ("syft-client", "syft_client"),
    ("syft-rds", "syft_rds"),
    ("syft-dataset", "syft_datasets"),
    ("syft-job", "syft_job"),
    ("syft-permissions", "syft_permissions"),
    ("syft-perms", "syft_perms"),
    ("syft-bg", "syft_bg"),
    ("syft-enclave", "syft_enclaves"),
    ("syft-restrict", "syft_restrict"),
    ("syft-migration", "syft_migration"),
    ("syft-notebook-ui", "syft_notebook_ui"),
]


def main() -> int:
    argparse.ArgumentParser(description="Check PySyft package imports, metadata, and safe CLI help").parse_args()
    ok = True
    for dist, module in DISTS:
        try:
            dist_version = version(dist)
            importlib.import_module(module)
            print(f"OK {dist}=={dist_version} imports as {module}")
        except PackageNotFoundError:
            print(f"FAIL {dist} is not installed")
            ok = False
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {dist}/{module}: {exc}")
            ok = False
    proc = subprocess.run([sys.executable, "-m", "syft_job.runner_main", "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
    print(("OK" if proc.returncode == 0 else "FAIL") + " python -m syft_job.runner_main --help")
    ok = ok and proc.returncode == 0
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
