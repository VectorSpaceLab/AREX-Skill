#!/usr/bin/env python3
"""Validate a CubeStudio SQLLab request without making any DB connections."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

ALLOWED_ENGINES = ("mysql", "postgres", "presto", "clickhouse", "hive", "impala")
TOKEN = r"(?:\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*|[^/@:?#]+)"
PATH_TOKEN = r"(?:\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*|[^/?#]+)"
URI_PATTERNS = {
    "mysql": re.compile(rf"^mysql\+pymysql://{TOKEN}:{TOKEN}@{TOKEN}:{TOKEN}/{PATH_TOKEN}(?:\?.*)?$"),
    "postgres": re.compile(rf"^postgresql\+psycopg2://{TOKEN}:{TOKEN}@{TOKEN}:{TOKEN}/{PATH_TOKEN}(?:\?.*)?$"),
    "presto": re.compile(rf"^presto://{TOKEN}:{TOKEN}@{TOKEN}:{TOKEN}/{PATH_TOKEN}/{PATH_TOKEN}(?:\?.*)?$"),
    "clickhouse": re.compile(rf"^clickhouse\+native://{TOKEN}:{TOKEN}@{TOKEN}:{TOKEN}/{PATH_TOKEN}(?:\?.*)?$"),
    "hive": re.compile(rf"^hive://(?:{TOKEN}:{TOKEN}@)?{TOKEN}:{TOKEN}/{PATH_TOKEN}(?:\?.*)?$"),
    "impala": re.compile(rf"^impala://(?:{TOKEN}:{TOKEN}@)?{TOKEN}:{TOKEN}/{PATH_TOKEN}(?:\?.*)?$"),
}


def read_text(source: str | None) -> str:
    if source in (None, "-"):
        return sys.stdin.read()

    candidate = source.strip()
    if candidate.startswith("{") or candidate.startswith("["):
        return source

    path = Path(source)
    if path.is_file():
        return path.read_text(encoding="utf-8")

    return source


def load_payload(source: str | None) -> Any:
    text = read_text(source)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON input: {exc.msg} (line {exc.lineno}, column {exc.colno})") from exc


def extract_request(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    if isinstance(payload.get("request"), dict):
        return payload["request"]

    if any(key in payload for key in ("engine_arg1", "engine_arg2", "sql", "qsql", "engine", "uri", "uri_template")):
        return payload

    raise ValueError("payload must contain either the request object or engine_arg1/engine_arg2/sql fields")


def normalize_request(request: Dict[str, Any]) -> Tuple[Any, Any, Any]:
    engine = request.get("engine_arg1", request.get("engine"))
    uri = request.get("engine_arg2", request.get("uri", request.get("uri_template")))
    sql = request.get("sql", request.get("qsql"))
    return engine, uri, sql


def validate_request(engine: Any, uri: Any, sql: Any) -> list[str]:
    errors: list[str] = []

    if not isinstance(engine, str) or not engine.strip():
        errors.append("engine_arg1 is required")
    elif engine not in ALLOWED_ENGINES:
        errors.append(f"unsupported engine_arg1: {engine!r}; allowed: {', '.join(ALLOWED_ENGINES)}")

    if not isinstance(uri, str) or not uri.strip():
        errors.append("engine_arg2 is required")
    else:
        pattern = URI_PATTERNS.get(engine)
        if pattern and not pattern.fullmatch(uri.strip()):
            errors.append(f"engine_arg2 does not match the documented {engine} URI shape")

    if not isinstance(sql, str) or not sql.strip():
        errors.append("sql is required")
    elif not re.search(r"\blimit\b", sql, re.IGNORECASE):
        errors.append("sql must contain a LIMIT clause to match the current SQLLab executor")

    return errors


def render_report(report: Dict[str, Any], as_json: bool) -> str:
    if as_json:
        return json.dumps(report, ensure_ascii=False, indent=2)

    if report["ok"]:
        return (
            f"OK: engine_arg1={report['engine_arg1']}, "
            f"uri_shape=valid, sql_chars={report['sql_chars']}"
        )

    lines = ["Validation failed:"]
    for error in report["errors"]:
        lines.append(f"- {error}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a CubeStudio SQLLab request JSON payload.",
        epilog=(
            "Examples:\n"
            "  validate_sqllab_request.py request.json\n"
            "  cat request.json | validate_sqllab_request.py -\n"
            "  validate_sqllab_request.py '{\"engine_arg1\":\"mysql\",...}'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "payload",
        nargs="?",
        help="Path to a JSON file, raw JSON text, or '-' for stdin",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON report instead of a human-readable summary",
    )
    args = parser.parse_args()

    try:
        payload = load_payload(args.payload)
        request = extract_request(payload)
        engine, uri, sql = normalize_request(request)
        errors = validate_request(engine, uri, sql)
        report = {
            "ok": not errors,
            "engine_arg1": engine,
            "engine_arg2": uri,
            "sql_chars": len(sql) if isinstance(sql, str) else 0,
            "errors": errors,
        }
    except Exception as exc:
        report = {
            "ok": False,
            "engine_arg1": None,
            "engine_arg2": None,
            "sql_chars": 0,
            "errors": [str(exc)],
        }

    print(render_report(report, args.json))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
