#!/usr/bin/env python3
"""Run a safe PandasAI Sandbox contract smoke.

The default smoke uses a tiny in-memory Sandbox subclass and does not require
Docker. Use --check-docker-extension to report whether the optional Docker
extension can be imported.

Examples:
  python sub-skills/sandbox-and-security/scripts/sandbox_contract_smoke.py
  python sub-skills/sandbox-and-security/scripts/sandbox_contract_smoke.py --check-docker-extension
"""

from __future__ import annotations

import argparse
import importlib
import json
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the PandasAI Sandbox contract")
    parser.add_argument("--check-docker-extension", action="store_true", help="also probe optional pandasai_docker import")
    parser.add_argument("--require-docker", action="store_true", help="fail if --check-docker-extension cannot import pandasai_docker")
    args = parser.parse_args()

    report: dict[str, Any] = {"ok": False, "docker_extension": None}

    try:
        from pandasai.sandbox import Sandbox
    except Exception as exc:  # noqa: BLE001
        report.update({"stage": "import", "error": f"{type(exc).__name__}: {exc}"})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    class SandboxImpl(Sandbox):
        def start(self):
            self._started = True

        def stop(self):
            self._started = False

        def _exec_code(self, code: str, environment: dict) -> dict:
            exec_globals = environment.copy()
            exec(code, exec_globals)
            return exec_globals

        def transfer_file(self, csv_data, filename="file.csv"):
            return {"filename": filename, "bytes": len(csv_data) if hasattr(csv_data, "__len__") else None}

    try:
        sandbox = SandboxImpl()
        before = sandbox._started
        result = sandbox.execute("answer = 40 + 2", {})
        after_execute = sandbox._started
        sandbox.stop()
        after_stop = sandbox._started
        queries = sandbox._extract_sql_queries_from_code(
            "query = 'SELECT * FROM users'\nexecute_sql_query('SELECT id FROM orders')"
        )
        compiled = sandbox._compile_code("x = 1\ny = 2\nresult = x + y")
        transfer = sandbox.transfer_file("a,b\n1,2", "tiny.csv")

        report.update(
            {
                "contract": {
                    "started_before_execute": before,
                    "started_after_execute": after_execute,
                    "started_after_stop": after_stop,
                    "answer": result.get("answer"),
                    "queries": queries,
                    "compiled_type": type(compiled).__name__,
                    "transfer": transfer,
                }
            }
        )
    except Exception as exc:  # noqa: BLE001
        report.update({"stage": "contract", "error": f"{type(exc).__name__}: {exc}"})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    docker_ok = True
    if args.check_docker_extension or args.require_docker:
        try:
            module = importlib.import_module("pandasai_docker")
            report["docker_extension"] = {"ok": True, "module": module.__name__}
        except Exception as exc:  # noqa: BLE001
            docker_ok = False
            report["docker_extension"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    ok = (
        report["contract"]["started_before_execute"] is False
        and report["contract"]["started_after_execute"] is True
        and report["contract"]["started_after_stop"] is False
        and report["contract"]["answer"] == 42
        and report["contract"]["queries"] == ["SELECT * FROM users", "SELECT id FROM orders"]
        and (docker_ok or not args.require_docker)
    )
    report["ok"] = ok
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
