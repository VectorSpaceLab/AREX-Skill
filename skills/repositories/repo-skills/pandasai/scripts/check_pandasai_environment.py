#!/usr/bin/env python3
"""Check a PandasAI runtime environment.

This helper is bundled with the PandasAI repo skill. It validates imports,
version metadata, optional extension availability, CLI importability, and an
optional deterministic offline chat smoke that does not require provider keys.

Examples:
  python scripts/check_pandasai_environment.py
  python scripts/check_pandasai_environment.py --chat-smoke
  python scripts/check_pandasai_environment.py --optional pandasai_litellm pandasai_docker
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import sys
from typing import Any


def _try_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"name": name, "ok": True, "module": getattr(module, "__name__", name)}
    except Exception as exc:  # noqa: BLE001 - diagnostic tool reports concise failures
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _chat_smoke(table_name: str, expected: int) -> dict[str, Any]:
    try:
        import pandasai as pai
        from pandasai.llm.fake import FakeLLM

        code = (
            f"df = execute_sql_query('SELECT COUNT(*) AS total FROM {table_name}')\n"
            "result = {'type': 'number', 'value': int(df['total'].iloc[0])}"
        )
        pai.config.set({"llm": FakeLLM(code)})
        df = pai.DataFrame({"a": list(range(expected))}, _table_name=table_name)
        response = df.chat("count rows")
        ok = getattr(response, "type", None) == "number" and response.value == expected
        return {
            "ok": ok,
            "response_class": type(response).__name__,
            "response_type": getattr(response, "type", None),
            "value": getattr(response, "value", None),
            "last_code_executed": getattr(response, "last_code_executed", None),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a PandasAI runtime environment")
    parser.add_argument("--chat-smoke", action="store_true", help="run a deterministic FakeLLM chat smoke")
    parser.add_argument("--table-name", default="table_a", help="table name for --chat-smoke")
    parser.add_argument("--expect", type=int, default=2, help="expected row count for --chat-smoke")
    parser.add_argument(
        "--optional",
        nargs="*",
        default=[],
        help="optional extension import names to probe, e.g. pandasai_litellm pandasai_docker",
    )
    args = parser.parse_args()

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "required_imports": [],
        "optional_imports": [],
        "distribution": {},
        "cli": {},
        "chat_smoke": None,
    }

    for name in ["pandasai", "pandas", "duckdb", "sqlglot", "pydantic"]:
        report["required_imports"].append(_try_import(name))

    try:
        report["distribution"] = {"name": "pandasai", "version": metadata.version("pandasai")}
    except Exception as exc:  # noqa: BLE001
        report["distribution"] = {"name": "pandasai", "ok": False, "error": f"{type(exc).__name__}: {exc}"}

    report["cli"] = {"pai_on_path": shutil.which("pai") is not None}
    report["cli"]["import"] = _try_import("pandasai.cli.main")

    for name in args.optional:
        report["optional_imports"].append(_try_import(name))

    if args.chat_smoke:
        report["chat_smoke"] = _chat_smoke(args.table_name, args.expect)

    ok = all(item["ok"] for item in report["required_imports"])
    ok = ok and report["cli"]["import"].get("ok", False)
    if args.chat_smoke:
        ok = ok and bool(report["chat_smoke"] and report["chat_smoke"].get("ok"))

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
