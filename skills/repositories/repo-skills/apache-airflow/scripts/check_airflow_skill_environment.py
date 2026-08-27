#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Check installed Airflow packages and bundled helper availability."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from pathlib import Path

DISTRIBUTIONS = [
    "apache-airflow",
    "apache-airflow-core",
    "apache-airflow-task-sdk",
    "apache-airflow-ctl",
    "apache-airflow-providers-standard",
]
IMPORTS = ["airflow", "airflow.sdk", "airflowctl", "airflow.providers.standard"]
HELPERS = [
    "sub-skills/authoring-task-sdk/scripts/validate_dag_file.py",
    "sub-skills/operations-cli-api/scripts/inspect_airflow_cli.py",
    "sub-skills/providers-extensions/scripts/check_provider_metadata.py",
    "sub-skills/deployment-helm-docker/scripts/render_helm_values_summary.py",
    "sub-skills/contribution-tooling/scripts/select_test_command.py",
]


def check_distribution(name: str) -> dict[str, object]:
    try:
        return {"ok": True, "version": metadata.version(name)}
    except metadata.PackageNotFoundError:
        return {"ok": False, "error": "not installed"}


def check_import(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "module": getattr(module, "__name__", name)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to the apache-airflow skill directory.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skill_root = args.skill_root.resolve()
    helper_results = {helper: (skill_root / helper).is_file() for helper in HELPERS}
    result = {
        "distributions": {name: check_distribution(name) for name in DISTRIBUTIONS},
        "imports": {name: check_import(name) for name in IMPORTS},
        "helpers": helper_results,
    }
    ok = all(item["ok"] for item in result["distributions"].values()) and all(
        item["ok"] for item in result["imports"].values()
    ) and all(helper_results.values())
    result["ok"] = ok
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Airflow skill environment:", "ok" if ok else "needs attention")
        for name, info in result["distributions"].items():
            status = info.get("version") if info["ok"] else info.get("error")
            print(f"distribution {name}: {status}")
        for name, info in result["imports"].items():
            status = "ok" if info["ok"] else info.get("error")
            print(f"import {name}: {status}")
        missing = [helper for helper, exists in helper_results.items() if not exists]
        if missing:
            print("missing helpers:", ", ".join(missing))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
