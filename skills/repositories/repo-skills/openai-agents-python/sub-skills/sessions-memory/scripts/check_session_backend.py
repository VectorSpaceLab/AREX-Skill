#!/usr/bin/env python3
"""Check OpenAI Agents SDK session backend imports without network access."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import sys
import traceback
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class BackendResult:
    backend: str
    ok: bool
    detail: str
    import_path: str | None = None
    install_hint: str | None = None


BACKEND_IMPORTS: dict[str, tuple[str, str, str | None]] = {
    "sqlite": ("agents", "SQLiteSession", None),
    "openai-conversations": ("agents", "OpenAIConversationsSession", None),
    "compaction": ("agents.memory", "OpenAIResponsesCompactionSession", None),
    "async-sqlite": ("agents.extensions.memory", "AsyncSQLiteSession", "pip install aiosqlite"),
    "advanced-sqlite": ("agents.extensions.memory", "AdvancedSQLiteSession", None),
    "redis": ("agents.extensions.memory", "RedisSession", "pip install 'openai-agents[redis]'"),
    "sqlalchemy": (
        "agents.extensions.memory",
        "SQLAlchemySession",
        "pip install 'openai-agents[sqlalchemy]'",
    ),
    "mongodb": ("agents.extensions.memory", "MongoDBSession", "pip install 'openai-agents[mongodb]'"),
    "dapr": ("agents.extensions.memory", "DaprSession", "pip install 'openai-agents[dapr]'"),
    "encrypted": (
        "agents.extensions.memory",
        "EncryptedSession",
        "pip install 'openai-agents[encrypt]'",
    ),
}


def _stringify_error(error: BaseException, *, verbose: bool) -> str:
    if verbose:
        return "".join(traceback.format_exception_only(type(error), error)).strip()
    return str(error) or error.__class__.__name__


def _missing_dependency_hint(error: BaseException, existing_hint: str | None) -> str | None:
    if isinstance(error, ModuleNotFoundError):
        missing = getattr(error, "name", None)
        if missing == "agents":
            return "pip install openai-agents"
        if missing == "openai":
            return "install the openai-agents base dependencies"
    return existing_hint


def check_import(backend: str, *, verbose: bool = False) -> BackendResult:
    module_name, attr_name, install_hint = BACKEND_IMPORTS[backend]
    import_path = f"{module_name}.{attr_name}"
    try:
        module = importlib.import_module(module_name)
        getattr(module, attr_name)
    except Exception as error:
        return BackendResult(
            backend=backend,
            ok=False,
            detail=_stringify_error(error, verbose=verbose),
            import_path=import_path,
            install_hint=_missing_dependency_hint(error, install_hint),
        )
    return BackendResult(
        backend=backend,
        ok=True,
        detail="import ok",
        import_path=import_path,
        install_hint=install_hint,
    )


async def check_sqlite_smoke(*, verbose: bool = False) -> BackendResult:
    import_result = check_import("sqlite", verbose=verbose)
    if not import_result.ok:
        return import_result

    try:
        from agents import SQLiteSession

        session = SQLiteSession("skill-check")
        await session.add_items([{"role": "user", "content": "ping"}])
        items = await session.get_items()
        popped = await session.pop_item()
        await session.clear_session()
        session.close()
    except Exception as error:
        return BackendResult(
            backend="sqlite",
            ok=False,
            detail=f"SQLiteSession smoke check failed: {_stringify_error(error, verbose=verbose)}",
            import_path="agents.SQLiteSession",
        )

    if len(items) != 1 or not popped:
        return BackendResult(
            backend="sqlite",
            ok=False,
            detail="SQLiteSession smoke check returned unexpected items",
            import_path="agents.SQLiteSession",
        )

    return BackendResult(
        backend="sqlite",
        ok=True,
        detail="import ok; in-memory add/get/pop/clear ok",
        import_path="agents.SQLiteSession",
    )


def _select_backends(requested: str) -> list[str]:
    if requested == "all":
        return list(BACKEND_IMPORTS)
    return [requested]


def _print_text(results: list[BackendResult]) -> None:
    width = max(len(result.backend) for result in results)
    for result in results:
        status = "ok" if result.ok else "missing"
        line = f"{result.backend:<{width}}  {status:<7}  {result.detail}"
        if result.install_hint and not result.ok:
            line = f"{line} ({result.install_hint})"
        print(line)


def _result_dict(result: BackendResult) -> dict[str, Any]:
    return {key: value for key, value in asdict(result).items() if value is not None}


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check OpenAI Agents SDK session backend imports without network access."
    )
    parser.add_argument(
        "--backend",
        choices=["all", *BACKEND_IMPORTS.keys()],
        default="all",
        help="Backend to check; sqlite includes an in-memory smoke test.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--verbose", action="store_true", help="Include fuller exception details.")
    args = parser.parse_args()

    checks: dict[str, Callable[[], Any]] = {
        backend: (lambda backend=backend: check_import(backend, verbose=args.verbose))
        for backend in BACKEND_IMPORTS
    }
    checks["sqlite"] = lambda: check_sqlite_smoke(verbose=args.verbose)

    results: list[BackendResult] = []
    for backend in _select_backends(args.backend):
        result_or_awaitable = checks[backend]()
        if asyncio.iscoroutine(result_or_awaitable):
            result = await result_or_awaitable
        else:
            result = result_or_awaitable
        results.append(result)

    if args.json:
        print(json.dumps([_result_dict(result) for result in results], indent=2, sort_keys=True))
    else:
        _print_text(results)

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
