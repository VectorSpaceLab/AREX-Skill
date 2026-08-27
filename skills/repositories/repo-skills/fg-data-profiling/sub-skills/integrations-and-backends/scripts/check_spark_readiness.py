#!/usr/bin/env python3
"""Report fg-data-profiling Spark backend readiness without installing anything.

Examples:
  python check_spark_readiness.py
  python check_spark_readiness.py --try-session
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], timeout: int = 20) -> dict[str, object]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {
            "command": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except FileNotFoundError:
        return {"command": cmd, "returncode": 127, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired:
        return {"command": cmd, "returncode": 124, "stdout": "", "stderr": "timed out"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Spark readiness for fg-data-profiling.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--try-session", action="store_true", help="Try a tiny local SparkSession if pyspark and Java are present.")
    args = parser.parse_args()

    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "java": shutil.which("java"),
        "pyspark_present": importlib.util.find_spec("pyspark") is not None,
        "spark_local_ip": os.environ.get("SPARK_LOCAL_IP"),
        "spark_local_dirs": os.environ.get("SPARK_LOCAL_DIRS"),
        "session": None,
    }

    report["java_version"] = _run(["java", "-version"], timeout=10) if report["java"] else {"returncode": 127, "stderr": "command not found"}

    if args.try_session and report["pyspark_present"] and report["java"]:
        try:
            from pyspark.sql import SparkSession

            spark = (
                SparkSession.builder.master("local[1]")
                .appName("fg-data-profiling-readiness")
                .config("spark.sql.ansi.enabled", "false")
                .config("spark.driver.host", "127.0.0.1")
                .config("spark.driver.bindAddress", "127.0.0.1")
                .getOrCreate()
            )
            try:
                frame = spark.createDataFrame([(1, "a"), (2, "b")], ["n", "label"])
                report["session"] = {
                    "ok": True,
                    "spark_version": spark.version,
                    "row_count": frame.count(),
                }
            finally:
                spark.stop()
        except Exception as exc:  # noqa: BLE001 - readiness reporting
            report["session"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    elif args.try_session:
        report["session"] = {"ok": False, "reason": "pyspark or java missing"}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print(f"Java: {report['java'] or 'missing'}")
        print(f"PySpark present: {report['pyspark_present']}")
        print(f"SPARK_LOCAL_IP: {report['spark_local_ip'] or 'unset'}")
        print(f"SPARK_LOCAL_DIRS: {report['spark_local_dirs'] or 'unset'}")
        print(f"java -version: {report['java_version']}")
        if report["session"] is not None:
            print(f"Session: {report['session']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
