#!/usr/bin/env python3
"""Run safe PandasAI CLI diagnostics without real credentials.

Examples:
  python sub-skills/cli-and-project-ops/scripts/pai_cli_smoke.py --show-help
  python sub-skills/cli-and-project-ops/scripts/pai_cli_smoke.py --check-api-key PAI-59ca2c4a-7998-4195-81d1-5c597f998867
  python sub-skills/cli-and-project-ops/scripts/pai_cli_smoke.py --isolated-login-smoke
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe PandasAI CLI diagnostics")
    parser.add_argument("--show-help", action="store_true", help="invoke pai --help and pai dataset --help through Click")
    parser.add_argument("--check-api-key", help="validate one API key format without writing .env")
    parser.add_argument("--isolated-login-smoke", action="store_true", help="run login in a temporary isolated filesystem with a fake valid key")
    args = parser.parse_args()

    report: dict[str, Any] = {"ok": True, "help": None, "api_key": None, "login_smoke": None}

    try:
        from click.testing import CliRunner
        from pandasai.cli.main import cli, validate_api_key
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "stage": "import", "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return 1

    runner = CliRunner()

    if args.show_help:
        root_help = runner.invoke(cli, ["--help"])
        dataset_help = runner.invoke(cli, ["dataset", "--help"])
        report["help"] = {
            "root_exit_code": root_help.exit_code,
            "dataset_exit_code": dataset_help.exit_code,
            "root_has_login": "login" in root_help.output,
            "dataset_has_create": "create" in dataset_help.output,
        }
        report["ok"] = report["ok"] and root_help.exit_code == 0 and dataset_help.exit_code == 0

    if args.check_api_key is not None:
        report["api_key"] = {"value_supplied": True, "valid": validate_api_key(args.check_api_key)}

    if args.isolated_login_smoke:
        fake_key = "PAI-59ca2c4a-7998-4195-81d1-5c597f998867"
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["login", fake_key])
            try:
                env_content = open(".env", "r", encoding="utf-8").read()
            except FileNotFoundError:
                env_content = ""
            report["login_smoke"] = {
                "exit_code": result.exit_code,
                "success_message": "Successfully authenticated" in result.output,
                "env_contains_key": f"PANDABI_API_KEY={fake_key}" in env_content,
            }
            report["ok"] = report["ok"] and result.exit_code == 0 and report["login_smoke"]["env_contains_key"]

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
