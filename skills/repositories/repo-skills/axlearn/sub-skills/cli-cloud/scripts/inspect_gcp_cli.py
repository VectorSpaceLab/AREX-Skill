#!/usr/bin/env python3
"""Inspect AXLearn's GCP CLI tree and config search paths.

This helper is safe to run from any directory. It writes only a temporary dummy
config file so AXLearn can build the GCP help tree without real credentials.
It prints the current GCP config search paths, then tries the root and GCP help trees.

Example:
    python scripts/inspect_gcp_cli.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


_DUMMY_CONFIG = """[gcp.\"skill-dummy:us-central1-a\"]
project = \"skill-dummy\"
env_id = \"us-central1-a\"
zone = \"us-central1-a\"
network = \"projects/skill-dummy/global/networks/default\"
subnetwork = \"projects/skill-dummy/regions/us-central1/subnetworks/default\"
service_account_email = \"ml-training@skill-dummy.iam.gserviceaccount.com\"
permanent_bucket = \"skill-dummy-permanent\"
private_bucket = \"skill-dummy-private\"
ttl_bucket = \"skill-dummy-ttl\"
"""


def _normalize_cmd(cmd: list[str]) -> list[str]:
    if cmd and cmd[0] == "axlearn" and shutil.which("axlearn") is None:
        return [sys.executable, "-c", "import axlearn.cli; axlearn.cli.main()", *cmd[1:]]
    return cmd


def _run_help(cmd: list[str]) -> int:
    actual = _normalize_cmd(cmd)
    print(f"\n$ {' '.join(cmd)}")
    with tempfile.TemporaryDirectory(prefix="axlearn-cli-help-") as tmp:
        # Add a sentinel .git directory so AXLearn's repo-root search does not
        # walk up into an unrelated parent repository such as /tmp.
        (Path(tmp) / ".git").mkdir(exist_ok=True)
        config_dir = Path(tmp) / ".axlearn"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / ".axlearn.config").write_text(_DUMMY_CONFIG, encoding="utf-8")
        proc = subprocess.run(actual, text=True, capture_output=True, cwd=tmp)
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


def main() -> int:
    from axlearn.cloud.common.config import _config_search_paths
    from axlearn.cloud.gcp.config import CONFIG_NAMESPACE, default_env_id, default_project, default_zone

    print(f"config namespace={CONFIG_NAMESPACE}")
    print(f"config search paths={list(_config_search_paths())}")
    print(f"default_project={default_project()}")
    print(f"default_zone={default_zone()}")
    print(f"default_env_id={default_env_id()}")

    # The help commands are safe and exercise the installed console entry point.
    rc1 = _run_help(["axlearn", "--help"])
    rc2 = _run_help(["axlearn", "gcp", "--help"])
    return 0 if rc1 == 0 and rc2 == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
