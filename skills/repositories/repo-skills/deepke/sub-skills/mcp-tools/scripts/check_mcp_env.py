#!/usr/bin/env python3
"""Safely diagnose the DeepKE MCP wrapper environment.

The checks are intentionally non-invasive: this script imports packages, reads an
optional dotenv-style file, and inspects environment-variable presence. It does
not launch the MCP server, call LLM APIs, run DeepKE predictors, or mutate local
DeepKE config/data files.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Report:
    def __init__(self) -> None:
        self.items: List[Dict[str, object]] = []

    def add(self, name: str, status: str, message: str, **extra: object) -> None:
        self.items.append({"name": name, "status": status, "message": message, **extra})

    @property
    def has_failures(self) -> bool:
        return any(item["status"] == "fail" for item in self.items)

    @property
    def has_warnings(self) -> bool:
        return any(item["status"] == "warn" for item in self.items)

    def as_dict(self) -> Dict[str, object]:
        return {
            "ok": not self.has_failures,
            "warnings": self.has_warnings,
            "checks": self.items,
        }


def parse_env_file(path: Path) -> Dict[str, str]:
    """Parse a simple KEY=VALUE dotenv file without importing python-dotenv."""

    values: Dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            raise ValueError(f"{path}: line {lineno} is not KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"{path}: line {lineno} has an empty key")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'\"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def merged_env(env_file: Optional[Path], report: Report) -> Dict[str, str]:
    env = dict(os.environ)
    if env_file is None:
        default = Path.cwd() / ".env"
        if default.exists():
            env_file = default
        else:
            report.add("env_file", "warn", "no env file supplied and no .env found in the current directory")
            return env
    try:
        parsed = parse_env_file(env_file)
    except FileNotFoundError:
        report.add("env_file", "fail", "specified env file does not exist")
        return env
    except Exception as exc:  # pragma: no cover - diagnostic path
        report.add("env_file", "fail", f"could not parse env file: {exc}")
        return env
    env.update(parsed)
    report.add("env_file", "ok", f"loaded {len(parsed)} variable(s) from env file without printing values")
    return env


def distribution_version(dist_name: str) -> str:
    try:
        return importlib.metadata.version(dist_name)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def check_import(report: Report, module_name: str, dist_name: Optional[str] = None, attr: Optional[str] = None) -> None:
    try:
        module = importlib.import_module(module_name)
        if attr is not None and not hasattr(module, attr):
            report.add(module_name, "fail", f"imported module but missing attribute {attr}")
            return
    except Exception as exc:
        report.add(module_name, "fail", f"import failed: {exc.__class__.__name__}: {exc}")
        return
    version = distribution_version(dist_name or module_name.split(".")[0])
    report.add(module_name, "ok", "import succeeded", version=version)


def present(env: Dict[str, str], name: str) -> Tuple[bool, str]:
    value = env.get(name, "")
    return bool(value), value


def check_deepke_path(report: Report, env: Dict[str, str]) -> None:
    ok, value = present(env, "DEEPKE_PATH")
    if not ok:
        report.add("DEEPKE_PATH", "fail", "missing; server tools cannot resolve local DeepKE examples")
        return
    root = Path(value).expanduser()
    if not root.exists() or not root.is_dir():
        report.add("DEEPKE_PATH", "fail", "set but does not point to an existing directory", value_printed=False)
        return
    expected = [
        Path("example/ner/standard"),
        Path("example/re/standard"),
        Path("example/ae/standard"),
        Path("example/ee/standard"),
    ]
    missing = [str(rel) for rel in expected if not (root / rel).exists()]
    if missing:
        report.add("DEEPKE_PATH", "warn", "directory exists but expected example subdirectories are missing", missing=missing, value_printed=False)
    else:
        report.add("DEEPKE_PATH", "ok", "directory exists and expected example subdirectories are present", value_printed=False)


def check_python_prefix(report: Report, env: Dict[str, str], name: str, required: bool) -> None:
    ok, value = present(env, name)
    if not ok:
        status = "fail" if required else "warn"
        report.add(name, status, "missing", required=required)
        return
    tail = Path(value).name.lower().replace(".exe", "")
    if tail in {"python", "python3"}:
        report.add(
            name,
            "warn",
            "appears to point at a Python executable; the unmodified wrapper expects a directory prefix and appends 'python'",
            value_printed=False,
        )
        return
    if not value.endswith((os.sep, "/", "\\")):
        report.add(
            name,
            "warn",
            "does not end with a path separator; the unmodified wrapper concatenates this value directly with 'python'",
            value_printed=False,
        )
        return
    candidate = Path(value + "python").expanduser()
    if candidate.exists():
        report.add(name, "ok", "prefix plus 'python' resolves to an existing path", value_printed=False)
    else:
        report.add(name, "warn", "prefix is set but prefix plus 'python' was not found", value_printed=False)


def check_client_env(report: Report, env: Dict[str, str], require_client: bool) -> None:
    for name in ["API_KEY", "BASE_URL", "MODEL"]:
        ok, _ = present(env, name)
        if ok:
            report.add(name, "ok", "present for interactive OpenAI-compatible client", value_printed=False)
        else:
            status = "fail" if require_client else "warn"
            report.add(name, status, "missing; required only for the interactive LLM client", required=require_client)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check DeepKE MCP wrapper imports and environment variables safely.")
    parser.add_argument("--env-file", type=Path, help="optional dotenv-style file to read before checking variables")
    parser.add_argument("--require-ee", action="store_true", help="treat missing CONDA_EE_PY as a failure instead of a warning")
    parser.add_argument("--require-client", action="store_true", help="treat missing API_KEY/BASE_URL/MODEL as failures")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of human-readable text")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = Report()
    env = merged_env(args.env_file, report)

    check_import(report, "mcp", "mcp")
    check_import(report, "mcp.server.fastmcp", "mcp", attr="FastMCP")
    check_import(report, "mcp.client.stdio", "mcp", attr="stdio_client")
    check_import(report, "openai", "openai")
    check_import(report, "httpx", "httpx")
    check_import(report, "yaml", "PyYAML")
    check_import(report, "dotenv", "python-dotenv", attr="load_dotenv")

    check_deepke_path(report, env)
    check_python_prefix(report, env, "CONDA_PY", required=True)
    check_python_prefix(report, env, "CONDA_EE_PY", required=args.require_ee)
    check_client_env(report, env, require_client=args.require_client)

    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    else:
        for item in report.items:
            status = str(item["status"]).upper()
            print(f"[{status}] {item['name']}: {item['message']}")
        print("\nSummary:", "OK" if not report.has_failures else "FAILED")
        if report.has_warnings:
            print("Warnings indicate optional or local-configuration issues to resolve before full MCP use.")
    return 1 if report.has_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
