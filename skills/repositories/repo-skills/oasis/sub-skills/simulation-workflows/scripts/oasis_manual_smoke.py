#!/usr/bin/env python3
"""Run a tiny no-LLM OASIS manual-action smoke test.

The script is safe by default:
- no provider calls and no LLMAction;
- creates a temporary SQLite database unless --db-path is supplied;
- sets a non-secret OPENAI_API_KEY placeholder only if absent because current
  CAMEL may require a non-empty key when constructing SocialAgent(model=None);
- closes the environment before inspecting table counts.

Examples:
    python oasis_manual_smoke.py --help
    python oasis_manual_smoke.py --keep-db
    python oasis_manual_smoke.py --db-path ./oasis_smoke.db --overwrite
"""
from __future__ import annotations

import argparse
import asyncio
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Iterable

PLACEHOLDER_OPENAI_KEY = "oasis-manual-smoke-placeholder-no-provider-call"
COUNT_TABLES = ("user", "post", "comment", "follow", "trace")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny OASIS Reddit-style simulation using only ManualAction. "
            "No real LLM calls or provider credentials are used."
        )
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help=(
            "SQLite .db path to create. If omitted, a temporary DB is used. "
            "Existing files are not overwritten unless --overwrite is set."
        ),
    )
    parser.add_argument(
        "--keep-db",
        action="store_true",
        help="Keep the temporary DB after printing counts. User-provided DB paths are always kept.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing --db-path file.",
    )
    parser.add_argument(
        "--semaphore",
        type=int,
        default=1,
        help="LLM concurrency limit passed to oasis.make; no LLM calls are made. Default: 1.",
    )
    return parser


def ensure_db_path(args: argparse.Namespace) -> tuple[Path, Path | None, bool]:
    """Return (db_path, temp_root, should_delete_after_counts)."""
    if args.db_path is None:
        temp_root = Path(tempfile.mkdtemp(prefix="oasis-manual-smoke-"))
        db_path = temp_root / "oasis_manual_smoke.db"
        return db_path, temp_root, not args.keep_db

    db_path = args.db_path.expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        if not args.overwrite:
            raise FileExistsError(
                f"Refusing to overwrite existing DB: {db_path}. "
                "Choose a new --db-path or pass --overwrite."
            )
        db_path.unlink()
    return db_path, None, False


def read_counts(db_path: Path, tables: Iterable[str] = COUNT_TABLES) -> dict[str, int | str]:
    counts: dict[str, int | str] = {}
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        for table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                counts[table] = int(cursor.fetchone()[0])
            except sqlite3.Error as exc:
                counts[table] = f"unavailable: {exc}"
    return counts


async def run_smoke(db_path: Path, semaphore: int) -> dict[str, object]:
    # OASIS creates ./log at import/runtime. Isolate that side effect.
    work_root = Path(tempfile.mkdtemp(prefix="oasis-smoke-work-"))
    original_cwd = Path.cwd()
    previous_db_env = os.environ.get("OASIS_DB_PATH")
    placeholder_set = False

    try:
        os.chdir(work_root)
        os.environ["OASIS_DB_PATH"] = str(db_path)
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = PLACEHOLDER_OPENAI_KEY
            placeholder_set = True

        try:
            from oasis import (  # type: ignore
                ActionType,
                AgentGraph,
                DefaultPlatformType,
                ManualAction,
                SocialAgent,
                UserInfo,
                make,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Could not import OASIS. Install camel-oasis with its base "
                f"dependencies before running this smoke. Import error: {exc}"
            ) from exc

        available_actions = [
            ActionType.CREATE_POST,
            ActionType.CREATE_COMMENT,
            ActionType.FOLLOW,
            ActionType.DO_NOTHING,
        ]
        agent_graph = AgentGraph()
        for agent_id, user_name, name, description in [
            (0, "alice", "Alice", "A manual smoke-test user."),
            (1, "bob", "Bob", "Another manual smoke-test user."),
        ]:
            agent = SocialAgent(
                agent_id=agent_id,
                user_info=UserInfo(
                    user_name=user_name,
                    name=name,
                    description=description,
                    profile=None,
                    recsys_type="reddit",
                ),
                agent_graph=agent_graph,
                model=None,
                available_actions=available_actions,
            )
            agent_graph.add_agent(agent)

        env = make(
            agent_graph=agent_graph,
            platform=DefaultPlatformType.REDDIT,
            database_path=str(db_path),
            semaphore=semaphore,
        )

        closed = False
        try:
            await env.reset()
            await env.step({
                env.agent_graph.get_agent(0): ManualAction(
                    action_type=ActionType.CREATE_POST,
                    action_args={"content": "Hello from the OASIS manual smoke."},
                )
            })
            await env.step({
                env.agent_graph.get_agent(1): [
                    ManualAction(
                        action_type=ActionType.CREATE_COMMENT,
                        action_args={
                            "post_id": 1,
                            "content": "Bob comments without any LLM call.",
                        },
                    ),
                    ManualAction(
                        action_type=ActionType.FOLLOW,
                        action_args={"followee_id": 0},
                    ),
                ]
            })
        finally:
            await env.close()
            closed = True

        counts = read_counts(db_path)
        return {
            "db_path": str(db_path),
            "counts": counts,
            "closed": closed,
            "placeholder_openai_key_set": placeholder_set,
            "llm_calls": 0,
        }
    finally:
        if previous_db_env is None:
            os.environ.pop("OASIS_DB_PATH", None)
        else:
            os.environ["OASIS_DB_PATH"] = previous_db_env
        os.chdir(original_cwd)
        shutil.rmtree(work_root, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.semaphore < 1:
        parser.error("--semaphore must be >= 1")

    temp_root: Path | None = None
    delete_after = False
    runtime_log = StringIO()
    try:
        db_path, temp_root, delete_after = ensure_db_path(args)
        # OASIS and some dependencies print/log during import and platform actions.
        # Capture that noise so the script's stdout remains machine-readable JSON.
        with redirect_stdout(runtime_log), redirect_stderr(runtime_log):
            result = asyncio.run(run_smoke(db_path.resolve(), args.semaphore))
        result["kept_db"] = not delete_after
        print(json.dumps(result, indent=2, sort_keys=True))
        if os.environ.get("OASIS_MANUAL_SMOKE_DEBUG") and runtime_log.getvalue():
            print(runtime_log.getvalue(), file=sys.stderr)
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI should surface concise failures.
        print(f"oasis_manual_smoke failed: {exc}", file=sys.stderr)
        if runtime_log.getvalue():
            print(runtime_log.getvalue(), file=sys.stderr)
        return 1
    finally:
        if delete_after and temp_root is not None:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
