#!/usr/bin/env python3
"""Run a deterministic PandasAI chat smoke without provider credentials.

The smoke uses pandasai.llm.fake.FakeLLM and generated code that calls
execute_sql_query, matching PandasAI's code validator requirements.

Examples:
  python sub-skills/conversational-analysis/scripts/offline_chat_smoke.py
  python sub-skills/conversational-analysis/scripts/offline_chat_smoke.py --table-name sales --expect 3
"""

from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a no-credential PandasAI chat smoke")
    parser.add_argument("--table-name", default="table_a", help="registered table name for the DataFrame")
    parser.add_argument("--expect", type=int, default=2, help="expected row count")
    args = parser.parse_args()

    try:
        import pandasai as pai
        from pandasai.llm.fake import FakeLLM
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "stage": "import", "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return 1

    code = (
        f"df = execute_sql_query('SELECT COUNT(*) AS total FROM {args.table_name}')\n"
        "result = {'type': 'number', 'value': int(df['total'].iloc[0])}"
    )

    try:
        pai.config.set({"llm": FakeLLM(code), "save_logs": False, "verbose": False})
        df = pai.DataFrame({"a": list(range(args.expect))}, _table_name=args.table_name)
        response = df.chat("How many rows are in the table?")
        ok = response.type == "number" and response.value == args.expect
        report = {
            "ok": ok,
            "response_class": type(response).__name__,
            "response_type": response.type,
            "value": response.value,
            "expected": args.expect,
            "last_code_executed": response.last_code_executed,
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if ok else 1
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "stage": "chat", "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
