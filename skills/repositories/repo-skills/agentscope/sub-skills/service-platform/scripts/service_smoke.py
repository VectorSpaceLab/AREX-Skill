#!/usr/bin/env python3
"""Smoke-test the AgentScope service bootstrap with local components."""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from agentscope.app import create_app
from agentscope.app.message_bus import InMemoryMessageBus
from agentscope.app.storage import AsyncSQLAlchemyStorage
from agentscope.app.workspace_manager import LocalWorkspaceManager


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="agentscope-service-") as tmpdir:
        base = Path(tmpdir)
        storage = AsyncSQLAlchemyStorage("sqlite+aiosqlite:///:memory:")
        message_bus = InMemoryMessageBus()
        workspace_manager = LocalWorkspaceManager(basedir=str(base / "workspaces"))

        app = create_app(
            storage=storage,
            message_bus=message_bus,
            workspace_manager=workspace_manager,
            enable_index_worker=False,
        )

        print(f"app type: {type(app).__name__}")
        routes = getattr(app, "routes", [])
        print(f"route count: {len(routes)}")
        for route in routes[:20]:
            print(getattr(route, "path", repr(route)))


if __name__ == "__main__":
    asyncio.run(main())
