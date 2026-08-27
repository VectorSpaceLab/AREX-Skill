#!/usr/bin/env python3
"""Run a local PandasAI semantic-layer create/load/chat smoke.

This creates a temporary project directory, writes a tiny CSV, creates a local
semantic dataset, loads it, queries it with FakeLLM, prints JSON, and cleans up.
No network, database, provider credentials, or Docker daemon are required.

Example:
  python sub-skills/semantic-layer/scripts/create_local_dataset_smoke.py
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local PandasAI semantic-layer smoke test")
    parser.add_argument("--keep-temp", action="store_true", help="do not delete the temporary project directory")
    parser.add_argument("--expect-total", type=int, default=25, help="expected revenue total")
    args = parser.parse_args()

    temp_dir = Path(tempfile.mkdtemp(prefix="pandasai-semantic-smoke-"))
    original_cwd = Path.cwd()
    report: dict[str, Any] = {"ok": False, "temp_dir": str(temp_dir), "expected_total": args.expect_total}

    try:
        os.chdir(temp_dir)
        Path("sales.csv").write_text("region,revenue\nEU,10\nUS,15\n", encoding="utf-8")

        import pandasai as pai
        from pandasai.llm.fake import FakeLLM

        raw = pai.read_csv("sales.csv")
        created = pai.create(
            "demo-org/sales-data",
            raw,
            description="tiny sales dataset",
            columns=[
                {"name": "region", "type": "string", "description": "Sales region"},
                {"name": "revenue", "type": "integer", "description": "Revenue"},
            ],
        )
        loaded = pai.load("demo-org/sales-data")
        table_name = loaded.schema.name
        code = (
            f"df = execute_sql_query('SELECT SUM(revenue) AS total FROM {table_name}')\n"
            "result = {'type': 'number', 'value': int(df['total'].iloc[0])}"
        )
        pai.config.set({"llm": FakeLLM(code), "save_logs": False, "verbose": False})
        response = loaded.chat("What is total revenue?")

        schema_path = temp_dir / "datasets" / "demo-org" / "sales-data" / "schema.yaml"
        data_path = temp_dir / "datasets" / "demo-org" / "sales-data" / "data.parquet"
        ok = response.type == "number" and response.value == args.expect_total and schema_path.exists() and data_path.exists()
        report.update(
            {
                "ok": ok,
                "created_schema_name": created.schema.name,
                "loaded_schema_name": loaded.schema.name,
                "schema_path_exists": schema_path.exists(),
                "data_path_exists": data_path.exists(),
                "response_type": response.type,
                "response_value": response.value,
                "last_code_executed": response.last_code_executed,
            }
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if ok else 1
    except Exception as exc:  # noqa: BLE001
        report.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1
    finally:
        os.chdir(original_cwd)
        if not args.keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
