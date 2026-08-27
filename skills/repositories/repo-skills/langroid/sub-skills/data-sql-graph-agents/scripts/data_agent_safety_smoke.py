#!/usr/bin/env python3
"""No-network safety smoke for Langroid structured-data agents.

The script lazily imports Langroid config and validator objects when available,
prints the security defaults, and optionally validates one SQL, Cypher, or AQL
string. It never instantiates an agent, connects to a database, or calls an LLM
provider.
"""

from __future__ import annotations

import argparse
import importlib
import re
import sys
from typing import Any, Dict, Iterable, Optional, Tuple

DEFAULTS = {
    "TableChatAgentConfig.full_eval": False,
    "SQLChatAgentConfig.allowed_statement_types": ["SELECT"],
    "SQLChatAgentConfig.allow_dangerous_operations": False,
    "Neo4jChatAgentConfig.allow_dangerous_operations": False,
    "ArangoChatAgentConfig.allow_dangerous_operations": False,
    "ArangoChatAgentConfig.max_num_results": 10,
    "ArangoChatAgentConfig.max_schema_fields": 500,
}

SQL_DANGEROUS_PATTERNS = [
    re.compile(r"\bcopy\b[\s\S]*\bprogram\b", re.IGNORECASE),
    re.compile(
        r"\bpg_(read|stat|ls|current_logfile)[A-Za-z0-9_]*\s*\(",
        re.IGNORECASE,
    ),
    re.compile(r"\blo_(import|export)\b", re.IGNORECASE),
    re.compile(r"\binto\s+(outfile|dumpfile)\b", re.IGNORECASE),
    re.compile(r"\bload_file\s*\(", re.IGNORECASE),
    re.compile(r"\bload\s+data\b", re.IGNORECASE),
    re.compile(r"\bload_extension\s*\(", re.IGNORECASE),
    re.compile(r"\battach\b(\s+database)?\s+['\"\w]", re.IGNORECASE),
    re.compile(r"\bxp_cmdshell\b", re.IGNORECASE),
    re.compile(r"\bsp_oacreate\b", re.IGNORECASE),
    re.compile(r"\bsp_oamethod\b", re.IGNORECASE),
    re.compile(r"\b(openrowset|opendatasource)\b", re.IGNORECASE),
    re.compile(r"\bbulk\s+insert\b", re.IGNORECASE),
    re.compile(
        r"\bcreate\s+(or\s+replace\s+)?"
        r"(function|procedure|trigger|language|rule|event\s+trigger|foreign\s+table)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bcreate\s+extension\b", re.IGNORECASE),
]
SQL_DANGEROUS_FUNCTION_NAMES = frozenset(
    {"load_file", "load_extension", "sp_oacreate", "sp_oamethod"}
)
SQL_DANGEROUS_FUNCTION_PREFIXES = (
    "pg_read",
    "pg_stat",
    "pg_ls",
    "pg_current_logfile",
    "lo_",
)

CYPHER_DANGEROUS_PATTERNS = [
    (re.compile(r"\bLOAD\s+CSV\b", re.IGNORECASE), "LOAD CSV file/URL access"),
    (re.compile(r"\bapoc\.", re.IGNORECASE), "an apoc.* procedure/function"),
    (re.compile(r"\bdbms\.", re.IGNORECASE), "a dbms.* admin procedure"),
    (re.compile(r"\bCALL\s+db\.", re.IGNORECASE), "a CALL db.* admin procedure"),
]
CYPHER_WRITE_PATTERNS = [
    (re.compile(r"(?<!\.)\bCREATE\b", re.IGNORECASE), "CREATE"),
    (re.compile(r"(?<!\.)\bMERGE\b", re.IGNORECASE), "MERGE"),
    (re.compile(r"(?<!\.)\bSET\b", re.IGNORECASE), "SET"),
    (re.compile(r"(?<!\.)\bDELETE\b", re.IGNORECASE), "DELETE"),
    (re.compile(r"(?<!\.)\bREMOVE\b", re.IGNORECASE), "REMOVE"),
    (re.compile(r"(?<!\.)\bDROP\b", re.IGNORECASE), "DROP"),
    (re.compile(r"(?<!\.)\bFOREACH\b", re.IGNORECASE), "FOREACH"),
]

AQL_DANGEROUS_PATTERNS = [
    (
        re.compile(r"[A-Za-z0-9_]+\s*::\s*[A-Za-z0-9_]+"),
        "a user-defined function call (namespace::func)",
    )
]
AQL_WRITE_PATTERNS = [
    (re.compile(r"(?<!\.)\bINSERT\b", re.IGNORECASE), "INSERT"),
    (re.compile(r"(?<!\.)\bUPDATE\b", re.IGNORECASE), "UPDATE"),
    (re.compile(r"(?<!\.)\bREPLACE\b", re.IGNORECASE), "REPLACE"),
    (re.compile(r"(?<!\.)\bREMOVE\b", re.IGNORECASE), "REMOVE"),
    (re.compile(r"(?<!\.)\bUPSERT\b", re.IGNORECASE), "UPSERT"),
]


def try_import_runtime_api() -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Best-effort imports of the runtime config/validator objects."""
    api: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    imports = {
        "table_agent": "langroid.agent.special.table_chat_agent",
        "sql_agent": "langroid.agent.special.sql.sql_chat_agent",
        "neo4j_agent": "langroid.agent.special.neo4j.neo4j_chat_agent",
        "neo4j_validator": "langroid.agent.special.neo4j.cypher_validator",
        "arango_agent": "langroid.agent.special.arangodb.arangodb_agent",
        "arango_validator": "langroid.agent.special.arangodb.aql_validator",
    }
    for key, module_name in imports.items():
        try:
            api[key] = importlib.import_module(module_name)
        except Exception as exc:  # keep --help and fallback modes robust
            errors[key] = f"{type(exc).__name__}: {exc}"
    return api, errors


def live_defaults(api: Dict[str, Any]) -> Dict[str, Any]:
    """Read defaults from config classes when imports succeeded; otherwise fallback."""
    defaults = dict(DEFAULTS)

    table_mod = api.get("table_agent")
    if table_mod is not None:
        try:
            import pandas as pd  # type: ignore

            cfg = table_mod.TableChatAgentConfig(data=pd.DataFrame({"x": [1]}))
            defaults["TableChatAgentConfig.full_eval"] = cfg.full_eval
        except Exception:
            pass

    sql_mod = api.get("sql_agent")
    if sql_mod is not None:
        try:
            cfg = sql_mod.SQLChatAgentConfig()
            defaults["SQLChatAgentConfig.allowed_statement_types"] = list(
                cfg.allowed_statement_types
            )
            defaults["SQLChatAgentConfig.allow_dangerous_operations"] = (
                cfg.allow_dangerous_operations
            )
        except Exception:
            pass

    neo_mod = api.get("neo4j_agent")
    if neo_mod is not None:
        try:
            cfg = neo_mod.Neo4jChatAgentConfig()
            defaults["Neo4jChatAgentConfig.allow_dangerous_operations"] = (
                cfg.allow_dangerous_operations
            )
        except Exception:
            pass

    arango_mod = api.get("arango_agent")
    if arango_mod is not None:
        try:
            cfg = arango_mod.ArangoChatAgentConfig()
            defaults["ArangoChatAgentConfig.allow_dangerous_operations"] = (
                cfg.allow_dangerous_operations
            )
            defaults["ArangoChatAgentConfig.max_num_results"] = cfg.max_num_results
            defaults["ArangoChatAgentConfig.max_schema_fields"] = cfg.max_schema_fields
        except Exception:
            pass

    return defaults


def normalize_sql_dialect(name: str) -> str:
    mapping = {"postgresql": "postgres", "mssql": "tsql"}
    return mapping.get(name, name)


def sql_is_dangerous_function_name(name: str) -> bool:
    if name in SQL_DANGEROUS_FUNCTION_NAMES:
        return True
    return any(name.startswith(prefix) for prefix in SQL_DANGEROUS_FUNCTION_PREFIXES)


def sql_called_function_names(stmt: Any, exp: Any) -> Iterable[str]:
    for node in stmt.find_all(exp.Func):
        if isinstance(node, exp.Anonymous):
            this = node.this
            if isinstance(this, exp.Expression):
                name = this.name
            else:
                name = str(this) if this is not None else ""
        else:
            name = getattr(type(node), "key", "") or ""
        name = name.rsplit(".", 1)[-1].strip().lower()
        if name:
            yield name


def sql_creates_table(into: Any, exp: Any) -> bool:
    if into is None:
        return False
    target = into.this
    if target is None:
        return False
    return not isinstance(getattr(target, "this", None), exp.Parameter)


def sql_nested_write_kinds(stmt: Any, kind_map: Dict[Any, str], exp: Any) -> set[str]:
    write_types = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Merge,
        exp.Create,
        exp.Drop,
        exp.Alter,
        exp.TruncateTable,
    )
    merge_actions = {
        id(when.args["then"])
        for when in stmt.find_all(exp.When)
        if when.args.get("then") is not None
    }
    kinds = {
        kind_map[type(node)]
        for node in stmt.find_all(*write_types)
        if node is not stmt and type(node) in kind_map and id(node) not in merge_actions
    }
    selects = list(stmt.find_all(exp.Select))
    if isinstance(stmt, exp.Select):
        selects.append(stmt)
    if any(sql_creates_table(sel.args.get("into"), exp) for sel in selects):
        kinds.add("CREATE")
    return kinds


def validate_sql_without_sqlglot(query: str) -> Optional[str]:
    """Conservative fallback when sqlglot is unavailable."""
    stripped = query.strip()
    for pat in SQL_DANGEROUS_PATTERNS:
        if pat.search(stripped):
            return (
                "Query REJECTED for safety: it matches a dangerous SQL pattern "
                f"({pat.pattern!r})."
            )
    if ";" in stripped.rstrip(";"):
        return (
            "Query REJECTED for safety: sqlglot is unavailable and multi-"
            "statement SQL cannot be verified."
        )
    if re.search(r"(?is)\bselect\b[\s\S]*\binto\b", stripped):
        return (
            "Query REJECTED for safety: SELECT ... INTO requires sqlglot "
            "verification and is rejected by the conservative fallback."
        )
    if not re.match(r"(?is)^\s*(select|with)\b", stripped):
        return (
            "Query REJECTED for safety: sqlglot is unavailable and this "
            "fallback only permits simple read-only SELECT/CTE queries."
        )
    if re.search(
        r"(?is)\b(insert|update|delete|merge|create|drop|alter|truncate|"
        r"copy|exec|call|attach|load)\b",
        stripped,
    ):
        return (
            "Query REJECTED for safety: sqlglot is unavailable and a "
            "potentially write-capable keyword was detected."
        )
    return None


def validate_sql_default(query: str, dialect: str, api: Dict[str, Any]) -> Optional[str]:
    sql_mod = api.get("sql_agent")
    if sql_mod is not None:
        patterns = getattr(sql_mod, "_DANGEROUS_SQL_PATTERNS", SQL_DANGEROUS_PATTERNS)
        nested_write_kinds = getattr(sql_mod, "_nested_write_kinds", None)
        called_function_names = getattr(sql_mod, "_called_function_names", None)
        is_dangerous_function_name = getattr(
            sql_mod, "_is_dangerous_function_name", sql_is_dangerous_function_name
        )
        sqlglot = getattr(sql_mod, "sqlglot", None)
        exp = getattr(sql_mod, "sqlglot_exp", None)
    else:
        patterns = SQL_DANGEROUS_PATTERNS
        nested_write_kinds = None
        called_function_names = None
        is_dangerous_function_name = sql_is_dangerous_function_name
        sqlglot = None
        exp = None
        try:
            import sqlglot as sqlglot_import  # type: ignore
            from sqlglot import expressions as exp_import  # type: ignore
        except Exception:
            pass
        else:
            sqlglot = sqlglot_import
            exp = exp_import

    if sqlglot is None or exp is None:
        return validate_sql_without_sqlglot(query)

    for pat in patterns:
        if pat.search(query):
            return (
                "Query REJECTED for safety: it matches a dangerous SQL pattern "
                f"({pat.pattern!r})."
            )

    allowed = {"SELECT"}
    try:
        statements = sqlglot.parse(query, read=normalize_sql_dialect(dialect))
    except Exception as exc:
        return f"Query REJECTED for safety: could not parse as {dialect}: {exc}"

    kind_map = {
        exp.Select: "SELECT",
        exp.Insert: "INSERT",
        exp.Update: "UPDATE",
        exp.Delete: "DELETE",
        exp.Merge: "MERGE",
        exp.Create: "CREATE",
        exp.Drop: "DROP",
        exp.Alter: "ALTER",
        exp.TruncateTable: "TRUNCATE",
        exp.Command: "COMMAND",
    }
    for stmt in statements:
        if stmt is None:
            continue
        kind = next(
            (value for cls, value in kind_map.items() if isinstance(stmt, cls)),
            type(stmt).__name__.upper(),
        )
        if kind not in allowed:
            return (
                f"Query REJECTED for safety: statement type {kind!r} is not "
                f"in the default allowlist {sorted(allowed)}."
            )
        if nested_write_kinds is not None:
            nested = nested_write_kinds(stmt, kind_map)
        else:
            nested = sql_nested_write_kinds(stmt, kind_map, exp)
        disallowed = sorted(nested - allowed)
        if disallowed:
            return (
                "Query REJECTED for safety: it embeds write kinds "
                f"{disallowed} under a {kind} statement."
            )
        names: Iterable[str]
        if called_function_names is not None:
            names = called_function_names(stmt)
        else:
            names = sql_called_function_names(stmt, exp)
        for fn_name in names:
            if is_dangerous_function_name(fn_name):
                return (
                    "Query REJECTED for safety: it calls dangerous function "
                    f"{fn_name!r}."
                )
    return None


def strip_cypher_literals_and_comments(query: str) -> str:
    out = []
    i, n = 0, len(query)
    while i < n:
        two = query[i : i + 2]
        if two == "//":
            j = query.find("\n", i)
            j = n if j == -1 else j
            out.append(" " * (j - i))
            i = j
        elif two == "/*":
            j = query.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append(" " * (j - i))
            i = j
        elif query[i] in "'\"":
            ch = query[i]
            j = i + 1
            while j < n:
                if query[j] == "\\":
                    j += 2
                    continue
                if query[j] == ch:
                    break
                j += 1
            j = min(j + 1, n)
            out.append(" " * (j - i))
            i = j
        elif query[i] == "`":
            j = i + 1
            while j < n:
                if query[j] == "`":
                    if j + 1 < n and query[j + 1] == "`":
                        j += 2
                        continue
                    break
                j += 1
            j = min(j + 1, n)
            out.append(" " * (j - i))
            i = j
        else:
            out.append(query[i])
            i += 1
    return "".join(out)


def validate_cypher_fallback(query: str, *, is_write: bool) -> Optional[str]:
    scrubbed = strip_cypher_literals_and_comments(query)
    for pat, label in CYPHER_DANGEROUS_PATTERNS:
        if pat.search(scrubbed):
            return f"Cypher query REJECTED for safety: it uses {label}."
    if not is_write:
        for pat, label in CYPHER_WRITE_PATTERNS:
            if pat.search(scrubbed):
                return (
                    "Cypher query REJECTED for safety: the retrieval path is "
                    f"read-only but this query uses {label}."
                )
    return None


def strip_aql_literals_and_comments(query: str) -> str:
    out = []
    i, n = 0, len(query)
    while i < n:
        two = query[i : i + 2]
        if two == "//":
            j = query.find("\n", i)
            j = n if j == -1 else j
            out.append(" " * (j - i))
            i = j
        elif two == "/*":
            j = query.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append(" " * (j - i))
            i = j
        elif query[i] in "'\"":
            ch = query[i]
            j = i + 1
            while j < n:
                if query[j] == "\\":
                    j += 2
                    continue
                if query[j] == ch:
                    break
                j += 1
            j = min(j + 1, n)
            out.append(" " * (j - i))
            i = j
        elif query[i] in "`´":
            ch = query[i]
            j = query.find(ch, i + 1)
            j = n if j == -1 else j + 1
            out.append(" " * (j - i))
            i = j
        else:
            out.append(query[i])
            i += 1
    return "".join(out)


def validate_aql_fallback(query: str, *, is_write: bool) -> Optional[str]:
    scrubbed = strip_aql_literals_and_comments(query)
    for pat, label in AQL_DANGEROUS_PATTERNS:
        if pat.search(scrubbed):
            return f"AQL query REJECTED for safety: it uses {label}."
    if not is_write:
        for pat, label in AQL_WRITE_PATTERNS:
            if pat.search(scrubbed):
                return (
                    "AQL query REJECTED for safety: the retrieval path is "
                    f"read-only but this query uses {label}."
                )
    return None


def validate_cypher_default(query: str, is_write: bool, api: Dict[str, Any]) -> Optional[str]:
    validator = getattr(api.get("neo4j_validator"), "validate_cypher_query", None)
    if callable(validator):
        return validator(query, is_write=is_write, allow_dangerous=False)
    return validate_cypher_fallback(query, is_write=is_write)


def validate_aql_default(query: str, is_write: bool, api: Dict[str, Any]) -> Optional[str]:
    validator = getattr(api.get("arango_validator"), "validate_aql_query", None)
    if callable(validator):
        return validator(query, is_write=is_write, allow_dangerous=False)
    return validate_aql_fallback(query, is_write=is_write)


def print_defaults(defaults: Dict[str, Any], errors: Dict[str, str]) -> None:
    print("Structured-data agent safety defaults:")
    for key in sorted(defaults):
        print(f"  - {key}: {defaults[key]!r}")
    if errors:
        print("\nRuntime import notes (fallback defaults/validators may be used):")
        for key, msg in sorted(errors.items()):
            print(f"  - {key}: {msg}")


def report_result(label: str, rejection: Optional[str]) -> bool:
    if rejection is None:
        print(f"{label}: OK under default safety policy")
        return True
    print(f"{label}: {rejection}")
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Show Langroid structured-data agent safety defaults and validate "
            "SQL, Cypher, or AQL strings locally."
        ),
        epilog=(
            "Examples:\n"
            "  data_agent_safety_smoke.py --sql 'SELECT 1'\n"
            "  data_agent_safety_smoke.py --sql 'DROP TABLE users'\n"
            "  data_agent_safety_smoke.py --cypher 'MATCH (n) RETURN n'\n"
            "  data_agent_safety_smoke.py --aql 'FOR doc IN users RETURN doc'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--sql", help="SQL string to validate with SELECT-only defaults")
    parser.add_argument(
        "--sql-dialect",
        default="sqlite",
        choices=["sqlite", "postgres", "postgresql", "mysql", "tsql", "mssql"],
        help="SQL dialect for sqlglot parsing (default: sqlite)",
    )
    parser.add_argument("--cypher", help="Cypher string to validate")
    parser.add_argument(
        "--cypher-write",
        action="store_true",
        help="Validate Cypher as a creation/write-tool query instead of retrieval",
    )
    parser.add_argument("--aql", help="AQL string to validate")
    parser.add_argument(
        "--aql-write",
        action="store_true",
        help="Validate AQL as a creation/write-tool query instead of retrieval",
    )
    parser.add_argument(
        "--no-defaults",
        action="store_true",
        help="Suppress the default/security summary",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    api, errors = try_import_runtime_api()
    defaults = live_defaults(api)

    if not args.no_defaults:
        print_defaults(defaults, errors)

    ok = True
    if args.sql:
        ok &= report_result(
            f"SQL[{args.sql_dialect}]",
            validate_sql_default(args.sql, args.sql_dialect, api),
        )
    if args.cypher:
        mode = "write" if args.cypher_write else "read"
        ok &= report_result(
            f"Cypher[{mode}]",
            validate_cypher_default(args.cypher, args.cypher_write, api),
        )
    if args.aql:
        mode = "write" if args.aql_write else "read"
        ok &= report_result(
            f"AQL[{mode}]",
            validate_aql_default(args.aql, args.aql_write, api),
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
