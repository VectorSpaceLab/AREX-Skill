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
"""Safely parse an Airflow Dag file and report discovered Dag ids."""

from __future__ import annotations

import argparse
import inspect
import os
import sys
from pathlib import Path
from textwrap import indent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import-check one Airflow Dag file with DagBag and report discovery errors.",
    )
    parser.add_argument("dag_file", help="Path to the Dag Python file to validate.")
    parser.add_argument(
        "--expect-dag-id",
        action="append",
        default=[],
        help="Dag id expected in the parsed file. May be supplied multiple times.",
    )
    parser.add_argument(
        "--list-dags",
        action="store_true",
        help="Print discovered Dag ids on success.",
    )
    parser.add_argument(
        "--repo-root",
        help="Optional project root to prepend to sys.path for Dags that import current-checkout modules.",
    )
    parser.add_argument(
        "--no-safe-mode",
        action="store_true",
        help="Disable Airflow's Dag discovery safe-mode heuristic for this validation run.",
    )
    return parser.parse_args()


def normalize_path(path_value: str, label: str) -> Path:
    path = Path(path_value).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"{label} does not exist: {path}")
    return path


def import_dag_bag_class():
    try:
        from airflow.dag_processing.dagbag import DagBag
    except Exception as error:
        raise SystemExit(
            "Could not import Airflow DagBag. Run this helper in an environment with Airflow installed.\n"
            f"Import error: {type(error).__name__}: {error}"
        ) from error
    return DagBag


def format_import_errors(import_errors: dict[str, str]) -> str:
    formatted = []
    for location, message in sorted(import_errors.items()):
        formatted.append(f"- {location}\n{indent(message, '  ')}")
    return "\n".join(formatted)


def main() -> int:
    args = parse_args()
    dag_file = normalize_path(args.dag_file, "Dag file")
    if not dag_file.is_file():
        raise SystemExit(f"Dag file is not a file: {dag_file}")

    if args.repo_root:
        repo_root = normalize_path(args.repo_root, "Repo root")
        if not repo_root.is_dir():
            raise SystemExit(f"Repo root is not a directory: {repo_root}")
        sys.path.insert(0, os.fspath(repo_root))

    sys.path.insert(0, os.fspath(dag_file.parent))
    DagBag = import_dag_bag_class()

    dag_bag_kwargs = {"dag_folder": os.fspath(dag_file), "safe_mode": not args.no_safe_mode}
    signature = inspect.signature(DagBag)
    if "include_examples" in signature.parameters:
        dag_bag_kwargs["include_examples"] = False
    dag_bag = DagBag(**dag_bag_kwargs)
    if dag_bag.import_errors:
        print("Dag import failed:", file=sys.stderr)
        print(format_import_errors(dag_bag.import_errors), file=sys.stderr)
        return 1

    discovered_dag_ids = sorted(dag_bag.dags)
    if not discovered_dag_ids:
        print(
            "No Dags were discovered. Ensure the file creates a top-level Dag object or calls a @dag-decorated function.",
            file=sys.stderr,
        )
        return 1

    missing_dag_ids = sorted(set(args.expect_dag_id) - set(discovered_dag_ids))
    if missing_dag_ids:
        print(
            "Expected Dag ids were not discovered: " + ", ".join(missing_dag_ids),
            file=sys.stderr,
        )
        print("Discovered Dag ids: " + ", ".join(discovered_dag_ids), file=sys.stderr)
        return 1

    if args.list_dags:
        for dag_id in discovered_dag_ids:
            print(dag_id)
    else:
        print(f"Validated {dag_file.name}: {len(discovered_dag_ids)} Dag(s) discovered.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
