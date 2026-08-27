#!/usr/bin/env python3
"""Validate Open Wearables MCP configuration without calling the backend API.

The checker is safe by default: it reads local config/package metadata and, when
possible, imports the MCP package to verify tool names and signatures. It never
performs an HTTP request or validates the API key against a live service.

Examples:
  python check_mcp_config.py --mcp-root /path/to/open-wearables/mcp
  python check_mcp_config.py --mcp-root /path/to/open-wearables/mcp --strict
  python check_mcp_config.py --mcp-root /path/to/open-wearables/mcp --json
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import inspect
import io
import json
import os
import sys
import tomllib
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

EXPECTED_DEPS = ("fastmcp", "httpx", "pydantic", "pydantic-settings")
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
PLACEHOLDER_FRAGMENTS = (
    "replace",
    "placeholder",
    "your_api_key",
    "your-key",
    "example",
    "dummy",
    "test_key",
    "ow_your",
)
TOOL_SPECS = (
    ("get_users", "app.tools.users", "get_users"),
    ("get_activity_summary", "app.tools.activity", "get_activity_summary"),
    ("get_sleep_summary", "app.tools.sleep", "get_sleep_summary"),
    ("get_workout_events", "app.tools.workouts", "get_workout_events"),
    ("get_timeseries", "app.tools.timeseries", "get_timeseries"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Open Wearables MCP .env, pyproject metadata, and importable "
            "tool signatures without contacting the backend API."
        )
    )
    parser.add_argument(
        "--mcp-root",
        type=Path,
        default=Path.cwd(),
        help="Path to the Open Wearables MCP package directory (default: current directory).",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Path to the MCP .env file. Defaults to <mcp-root>/config/.env, falling back to .env.example.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON report instead of human-readable text.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when live-call config is missing, placeholder-only, or import checks fail.",
    )
    parser.add_argument(
        "--no-import-check",
        action="store_true",
        help="Skip importing the MCP package. Useful when dependencies have not been installed yet.",
    )
    return parser.parse_args()


def add_issue(report: dict[str, Any], severity: str, message: str, hint: str | None = None) -> None:
    issue: dict[str, str] = {"severity": severity, "message": message}
    if hint:
        issue["hint"] = hint
    report["issues"].append(issue)


def choose_env_file(mcp_root: Path, explicit: Path | None, report: dict[str, Any]) -> Path | None:
    if explicit is not None:
        return explicit
    env_file = mcp_root / "config" / ".env"
    if env_file.exists():
        return env_file
    example = mcp_root / "config" / ".env.example"
    if example.exists():
        add_issue(
            report,
            "warning",
            "Using .env.example because config/.env was not found.",
            "Copy the example to config/.env and replace placeholders before real tool calls.",
        )
        return example
    return env_file


def parse_dotenv(path: Path, report: dict[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        add_issue(
            report,
            "error",
            f"Environment file not found: {path}",
            "Create mcp/config/.env from the template or pass --env-file.",
        )
        return values

    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            add_issue(report, "warning", f"Ignoring malformed env line {line_no}: no '=' separator.")
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] in {"'", '"'} and value[-1:] == value[0]:
            value = value[1:-1]
        values[key] = value
    return values


def redact_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:3]}...{value[-4:]}"


def looks_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return any(fragment in lowered for fragment in PLACEHOLDER_FRAGMENTS)


def validate_env(values: dict[str, str], report: dict[str, Any]) -> None:
    api_url = values.get("OPEN_WEARABLES_API_URL", "")
    api_key = values.get("OPEN_WEARABLES_API_KEY", "")
    log_level = values.get("LOG_LEVEL", "INFO")
    timeout = values.get("REQUEST_TIMEOUT", "30")

    env_summary = {
        "OPEN_WEARABLES_API_URL": api_url,
        "OPEN_WEARABLES_API_KEY": redact_secret(api_key),
        "LOG_LEVEL": log_level,
        "REQUEST_TIMEOUT": timeout,
    }
    report["env"] = env_summary

    if not api_url:
        add_issue(report, "error", "OPEN_WEARABLES_API_URL is missing.", "Use an API base URL such as http://localhost:8000.")
    else:
        parsed = urlparse(api_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            add_issue(report, "error", "OPEN_WEARABLES_API_URL is not a valid HTTP(S) URL.")
        if parsed.path not in {"", "/"}:
            add_issue(
                report,
                "warning",
                "OPEN_WEARABLES_API_URL includes a path component.",
                "Use the API base host only; the MCP client appends /api/v1/... paths.",
            )

    if not api_key:
        add_issue(report, "error", "OPEN_WEARABLES_API_KEY is missing or blank.")
    elif looks_placeholder(api_key):
        add_issue(report, "error", "OPEN_WEARABLES_API_KEY still looks like a placeholder.")

    if log_level.upper() not in VALID_LOG_LEVELS:
        add_issue(report, "warning", f"LOG_LEVEL {log_level!r} is not a standard Python logging level.")

    try:
        timeout_value = int(timeout)
    except ValueError:
        add_issue(report, "error", "REQUEST_TIMEOUT must be an integer number of seconds.")
    else:
        if timeout_value <= 0:
            add_issue(report, "error", "REQUEST_TIMEOUT must be positive.")


def validate_pyproject(mcp_root: Path, report: dict[str, Any]) -> None:
    pyproject = mcp_root / "pyproject.toml"
    metadata: dict[str, Any] = {"path": str(pyproject), "present": pyproject.exists()}
    report["pyproject"] = metadata
    if not pyproject.exists():
        add_issue(report, "warning", "pyproject.toml was not found under --mcp-root.")
        return

    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        add_issue(report, "error", f"Could not parse pyproject.toml: {exc}")
        return

    project = data.get("project", {})
    metadata.update(
        {
            "name": project.get("name"),
            "version": project.get("version"),
            "requires_python": project.get("requires-python"),
            "start_script": (project.get("scripts") or {}).get("start"),
        }
    )

    if project.get("name") != "open-wearables-mcp":
        add_issue(report, "warning", "Project name is not open-wearables-mcp.")
    if project.get("requires-python") != ">=3.13":
        add_issue(report, "warning", "Expected requires-python to be >=3.13.")
    if (project.get("scripts") or {}).get("start") != "app.main:main":
        add_issue(report, "error", "Expected console script start = app.main:main.")

    deps = [str(dep).lower() for dep in project.get("dependencies", [])]
    missing = [dep for dep in EXPECTED_DEPS if not any(item.startswith(dep) for item in deps)]
    if missing:
        add_issue(report, "warning", f"Expected dependencies not found: {', '.join(missing)}")


def import_check(mcp_root: Path, report: dict[str, Any]) -> None:
    result: dict[str, Any] = {"status": "skipped", "tools": {}, "prompt": None}
    report["import_check"] = result
    if not (mcp_root / "app").is_dir():
        add_issue(report, "warning", "No app/ package found under --mcp-root; import check skipped.")
        return

    previous_path = list(sys.path)
    previous_env = {
        "OPEN_WEARABLES_API_KEY": os.environ.get("OPEN_WEARABLES_API_KEY"),
        "OPEN_WEARABLES_API_URL": os.environ.get("OPEN_WEARABLES_API_URL"),
    }
    previous_app_modules = {
        name: module for name, module in sys.modules.items() if name == "app" or name.startswith("app.")
    }

    try:
        for name in list(previous_app_modules):
            sys.modules.pop(name, None)
        sys.path.insert(0, str(mcp_root))
        os.environ.setdefault("OPEN_WEARABLES_API_KEY", "ow_check_placeholder")
        os.environ.setdefault("OPEN_WEARABLES_API_URL", "http://localhost:8000")

        with contextlib.redirect_stderr(io.StringIO()):
            main_module = importlib.import_module("app.main")
            api_client_module = importlib.import_module("app.services.api_client")

            result["status"] = "ok"
            result["server_type"] = type(getattr(main_module, "mcp")).__name__
            result["client_class"] = f"{api_client_module.OpenWearablesClient.__module__}.OpenWearablesClient"
            result["client_init_signature"] = str(inspect.signature(api_client_module.OpenWearablesClient.__init__))

            for public_name, module_name, attr_name in TOOL_SPECS:
                module = importlib.import_module(module_name)
                tool_obj = getattr(module, attr_name)
                fn = getattr(tool_obj, "fn", tool_obj)
                result["tools"][public_name] = str(inspect.signature(fn))

            prompts = importlib.import_module("app.prompts")
            prompt_obj = getattr(prompts, "present_health_data")
            prompt_fn = getattr(prompt_obj, "fn", prompt_obj)
            result["prompt"] = {"present_health_data": str(inspect.signature(prompt_fn))}
    except Exception as exc:  # noqa: BLE001 - user-facing diagnostic should catch dependency/import failures.
        result["status"] = "error"
        result["error"] = f"{type(exc).__name__}: {exc}"
        add_issue(
            report,
            "error",
            "MCP import check failed.",
            "Install dependencies from the MCP package directory, then rerun this checker.",
        )
    finally:
        sys.path[:] = previous_path
        for name in [name for name in sys.modules if name == "app" or name.startswith("app.")]:
            sys.modules.pop(name, None)
        sys.modules.update(previous_app_modules)
        for key, old_value in previous_env.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def print_text(report: dict[str, Any]) -> None:
    print("Open Wearables MCP configuration check")
    print(f"MCP root: {report['mcp_root']}")
    print(f"Env file: {report['env_file']}")
    env = report.get("env", {})
    if env:
        print("Environment:")
        for key in ("OPEN_WEARABLES_API_URL", "OPEN_WEARABLES_API_KEY", "LOG_LEVEL", "REQUEST_TIMEOUT"):
            print(f"  {key}: {env.get(key, '')}")

    pyproject = report.get("pyproject") or {}
    if pyproject:
        print("Package metadata:")
        print(f"  name: {pyproject.get('name')}")
        print(f"  version: {pyproject.get('version')}")
        print(f"  requires_python: {pyproject.get('requires_python')}")
        print(f"  start_script: {pyproject.get('start_script')}")

    import_result = report.get("import_check") or {}
    print(f"Import check: {import_result.get('status')}")
    if import_result.get("status") == "ok":
        print(f"  server_type: {import_result.get('server_type')}")
        print(f"  client_class: {import_result.get('client_class')}")
        for name, signature in (import_result.get("tools") or {}).items():
            print(f"  tool {name}: {signature}")
    elif import_result.get("error"):
        print(f"  error: {import_result['error']}")

    if report["issues"]:
        print("Issues:")
        for issue in report["issues"]:
            suffix = f" Hint: {issue['hint']}" if issue.get("hint") else ""
            print(f"  [{issue['severity']}] {issue['message']}{suffix}")
    else:
        print("Issues: none")

    print("Live API calls: not performed")


def main() -> int:
    args = parse_args()
    mcp_root = args.mcp_root.expanduser().resolve()
    report: dict[str, Any] = {
        "schema": "open-wearables-mcp-config-check.v1",
        "mcp_root": str(mcp_root),
        "issues": [],
    }

    env_file = choose_env_file(mcp_root, args.env_file.expanduser().resolve() if args.env_file else None, report)
    report["env_file"] = str(env_file) if env_file else None
    if env_file is not None:
        validate_env(parse_dotenv(env_file, report), report)
    validate_pyproject(mcp_root, report)
    if args.no_import_check:
        report["import_check"] = {"status": "skipped", "reason": "--no-import-check"}
    else:
        import_check(mcp_root, report)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    has_error = any(issue.get("severity") == "error" for issue in report["issues"])
    return 2 if args.strict and has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
