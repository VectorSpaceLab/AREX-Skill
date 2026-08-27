#!/usr/bin/env python3
"""Smoke-test the local AgentScope workspace backend."""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from agentscope.workspace import LocalWorkspace


SKILL_TEXT = """---
name: smoke-skill
description: "A tiny smoke-test skill."
---

# Smoke Skill

This skill exists only so the workspace can seed and list one local skill.
"""


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="agentscope-workspace-") as tmpdir:
        root = Path(tmpdir)
        skill_dir = root / "skill-src"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(SKILL_TEXT, encoding="utf-8")

        workspace = LocalWorkspace(
            workdir=str(root / "workspace"),
            skill_paths=[str(skill_dir)],
        )
        await workspace.initialize()

        print(f"workspace id: {workspace.workspace_id}")
        print(f"workdir: {workspace.workdir}")
        print(f"backend: {type(workspace.get_backend()).__name__}")

        print("\nskills:")
        for skill in await workspace.list_skills():
            print(f"- {skill.name}: {skill.description}")

        print("\ntools:")
        for tool in await workspace.list_tools():
            print(f"- {type(tool).__name__}")

        print("\nmcps:")
        for mcp in await workspace.list_mcps():
            print(f"- {mcp.name}")

        await workspace.close()


if __name__ == "__main__":
    asyncio.run(main())
