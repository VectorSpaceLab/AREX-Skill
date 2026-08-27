#!/usr/bin/env python3
"""Safe Feast environment diagnostic.

Checks installed Feast importability, CLI availability, and optional backend
imports without contacting external services or mutating feature repositories.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict


EXTRA_IMPORTS = {
    "redis": ["redis"],
    "snowflake": ["snowflake.connector"],
    "postgres": ["psycopg"],
    "mysql": ["pymysql"],
    "bigquery": ["google.cloud.bigquery"],
    "gcp": ["google.cloud.bigquery", "google.cloud.storage"],
    "aws": ["boto3"],
    "grpcio": ["grpc"],
    "rag": ["transformers", "sentence_transformers"],
    "milvus": ["pymilvus"],
    "qdrant": ["qdrant_client"],
    "faiss": ["faiss"],
    "mlflow": ["mlflow"],
    "openlineage": ["openlineage"],
    "duckdb": ["ibis", "duckdb"],
    "spark": ["pyspark"],
    "ray": ["ray"],
}


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def import_check(module: str) -> CheckResult:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostic should report all import failures
        return CheckResult(module, False, f"{type(exc).__name__}: {exc}")
    version = getattr(imported, "__version__", None)
    return CheckResult(module, True, f"imported" + (f" version={version}" if version else ""))


def run_cli(timeout: int) -> CheckResult:
    executable = shutil.which("feast")
    if not executable:
        return CheckResult("feast-cli", False, "feast executable not found on PATH")
    try:
        completed = subprocess.run(
            [executable, "version"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult("feast-cli", False, f"{type(exc).__name__}: {exc}")
    output = (completed.stdout or completed.stderr).strip().replace("\n", " ")
    return CheckResult("feast-cli", completed.returncode == 0, output or f"exit={completed.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check installed Feast and optional backend imports safely.")
    parser.add_argument("--extra", action="append", default=[], help="Optional Feast extra/backend name to check, e.g. redis, snowflake, rag. Repeatable.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--no-cli", action="store_true", help="Skip Feast CLI version check.")
    parser.add_argument("--timeout", type=int, default=10, help="CLI subprocess timeout in seconds.")
    args = parser.parse_args()

    results = [import_check("feast")]
    if not args.no_cli:
        results.append(run_cli(args.timeout))

    unknown_extras = []
    for extra in args.extra:
        modules = EXTRA_IMPORTS.get(extra)
        if not modules:
            unknown_extras.append(extra)
            results.append(CheckResult(f"extra:{extra}", False, "unknown extra alias in diagnostic script"))
            continue
        for module in modules:
            results.append(import_check(module))

    if args.json:
        print(json.dumps({"ok": all(r.ok for r in results), "results": [asdict(r) for r in results], "unknown_extras": unknown_extras}, indent=2))
    else:
        for result in results:
            status = "OK" if result.ok else "FAIL"
            print(f"[{status}] {result.name}: {result.detail}")
        if unknown_extras:
            print("Known extra aliases:", ", ".join(sorted(EXTRA_IMPORTS)))

    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
