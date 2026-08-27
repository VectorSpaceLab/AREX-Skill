#!/usr/bin/env python3
"""Smoke-test ai-data-science-team SQL safety helpers without LLM calls.

The script creates a tiny in-memory SQLite database, inspects metadata with
get_database_metadata(), checks dialect-aware sample-query construction, and
asserts that _validate_sql() accepts read-only SELECT queries while rejecting
unsafe/non-SELECT SQL. It performs no external service calls, downloads,
training, app launches, or persistent writes.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import pathlib
import sys
from typing import Any, Callable


def fail(stage: str, message: str, code: int = 1) -> int:
    payload = {
        "ok": False,
        "stage": stage,
        "error": message,
        "recovery": (
            "Verify that ai-data-science-team and its base runtime dependencies "
            "are installed in the active Python environment, then rerun this smoke."
        ),
    }
    print(json.dumps(payload, indent=2), file=sys.stderr)
    return code


def require(condition: bool, stage: str, message: str) -> None:
    if not condition:
        raise AssertionError(f"{stage}: {message}")


def table_map(metadata: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tables: dict[str, dict[str, Any]] = {}
    for schema in metadata.get("schemas", []):
        for table in schema.get("tables", []):
            tables[table.get("table_name", "")] = table
    return tables


def _package_dir() -> pathlib.Path:
    spec = importlib.util.find_spec("ai_data_science_team")
    if spec is None or not spec.submodule_search_locations:
        raise ImportError("ai_data_science_team package is not importable")
    return pathlib.Path(next(iter(spec.submodule_search_locations)))


def _load_module_from_file(module_name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load required module file: {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_validate_sql_from_source(agent_path: pathlib.Path) -> Callable[[str, bool], str | None]:
    tree = ast.parse(agent_path.read_text(encoding="utf-8"))
    function_node = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_validate_sql":
            function_node = node
            break
    if function_node is None:
        raise ImportError("_validate_sql function was not found")
    module = ast.Module(body=[function_node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: dict[str, Any] = {}
    exec(compile(module, "sql_database_agent._validate_sql", "exec"), namespace)
    return namespace["_validate_sql"]


def load_sql_helpers():
    """Load SQL helpers, falling back to source-file extraction for SQL-only smoke.

    Some package versions import notebook/display dependencies from the top-level
    package before SQL helpers are reached. The fallback still loads the installed
    package files discovered on Python's import path and avoids hard-coded source
    checkout paths.
    """
    try:
        from ai_data_science_team.agents.sql_database_agent import _validate_sql
        from ai_data_science_team.tools.sql import build_query, get_database_metadata

        return _validate_sql, build_query, get_database_metadata, "normal", None
    except Exception as exc:
        normal_error = f"{exc.__class__.__name__}: {exc}"
        pkg_dir = _package_dir()
        sql_tools = _load_module_from_file("_aids_sql_tools_smoke", pkg_dir / "tools" / "sql.py")
        validate_sql = _load_validate_sql_from_source(pkg_dir / "agents" / "sql_database_agent.py")
        return validate_sql, sql_tools.build_query, sql_tools.get_database_metadata, "source-fallback", normal_error


def main() -> int:
    try:
        import sqlalchemy as sa
        _validate_sql, build_query, get_database_metadata, import_mode, normal_import_error = load_sql_helpers()
    except Exception as exc:  # pragma: no cover - exercised only in broken envs
        return fail("import", f"{exc.__class__.__name__}: {exc}", code=2)

    try:
        engine = sa.create_engine("sqlite://")
        with engine.begin() as conn:
            conn.exec_driver_sql(
                "CREATE TABLE customers ("
                "id INTEGER PRIMARY KEY, "
                "name TEXT NOT NULL, "
                "country TEXT NOT NULL)"
            )
            conn.exec_driver_sql(
                "CREATE TABLE \"Customer Orders\" ("
                "id INTEGER PRIMARY KEY, "
                "customer_id INTEGER NOT NULL, "
                "\"order amount\" REAL NOT NULL, "
                "status TEXT NOT NULL, "
                "FOREIGN KEY(customer_id) REFERENCES customers(id))"
            )
            conn.exec_driver_sql(
                "INSERT INTO customers (id, name, country) VALUES "
                "(1, 'Ada', 'UK'), (2, 'Lin', 'US')"
            )
            conn.exec_driver_sql(
                "INSERT INTO \"Customer Orders\" "
                "(id, customer_id, \"order amount\", status) VALUES "
                "(10, 1, 42.50, 'shipped'), (11, 2, 10.00, 'pending')"
            )

            metadata = get_database_metadata(conn, n_samples=2)

        require(metadata.get("dialect") == "sqlite", "metadata", "dialect should be sqlite")
        tables = table_map(metadata)
        require("customers" in tables, "metadata", "customers table not found")
        require("Customer Orders" in tables, "metadata", "quoted table with space not found")

        customer_columns = {col["name"] for col in tables["customers"].get("columns", [])}
        order_columns = {col["name"] for col in tables["Customer Orders"].get("columns", [])}
        require({"id", "name", "country"}.issubset(customer_columns), "metadata", "customer columns missing")
        require({"id", "customer_id", "order amount", "status"}.issubset(order_columns), "metadata", "order columns missing")

        sample_queries = {
            "postgresql": build_query('"name"', '"customers"', 2, "postgresql"),
            "mysql": build_query('`name`', '`customers`', 2, "mysql"),
            "sqlite": build_query('"name"', '"customers"', 2, "sqlite"),
            "mssql": build_query('[name]', '[customers]', 2, "mssql"),
            "fallback": build_query('"name"', '"customers"', 2, "oracle"),
        }
        require("ORDER BY RANDOM() LIMIT 2" in sample_queries["postgresql"], "build_query", "postgres sample shape changed")
        require("ORDER BY RAND() LIMIT 2" in sample_queries["mysql"], "build_query", "mysql sample shape changed")
        require("ORDER BY RANDOM() LIMIT 2" in sample_queries["sqlite"], "build_query", "sqlite sample shape changed")
        require(sample_queries["mssql"].startswith("SELECT TOP 2"), "build_query", "mssql sample shape changed")
        require("ROWNUM <= 2" in sample_queries["fallback"], "build_query", "fallback sample shape changed")

        allowed = [
            "SELECT id, name FROM customers",
            '  select "order amount" from "Customer Orders" where status = \'shipped\'  ',
        ]
        blocked = [
            "",
            "UPDATE customers SET name = 'Grace' WHERE id = 1",
            "DROP TABLE customers",
            "WITH recent AS (SELECT id FROM customers) SELECT * FROM recent",
            "SELECT * FROM customers; DELETE FROM customers",
        ]

        for query in allowed:
            result = _validate_sql(query, safe_mode=True)
            require(result is None, "validate_sql", f"read-only SELECT was rejected: {result}")

        for query in blocked:
            result = _validate_sql(query, safe_mode=True)
            require(isinstance(result, str) and result, "validate_sql", f"unsafe query was accepted: {query!r}")

        require(_validate_sql("DROP TABLE customers", safe_mode=False) is None, "validate_sql", "safe_mode=False behavior changed")

    except Exception as exc:
        return fail("smoke", f"{exc.__class__.__name__}: {exc}", code=1)

    payload = {
        "ok": True,
        "checks": [
            "loaded SQL helpers",
            "created in-memory SQLite fixture",
            "inspected metadata and quoted identifiers",
            "checked dialect sample-query shapes",
            "verified safe-mode SQL validation",
        ],
        "import_mode": import_mode,
        "normal_import_error": normal_import_error,
        "dialect": metadata.get("dialect"),
        "tables": sorted(tables),
        "validation_counts": {"allowed": len(allowed), "blocked": len(blocked)},
        "notes": "No LLM calls, external services, downloads, app launches, training, or persistent writes were performed.",
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
