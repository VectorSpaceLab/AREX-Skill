#!/usr/bin/env python3
"""Offline smoke check for Swarms single-agent support objects."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from swarms import Agent
from swarms.agents.skills_manager import SkillsManager
from swarms.artifacts.main_artifact import Artifact
from swarms.structs.conversation import Conversation


def main() -> None:
    print(f"Agent import OK: {Agent.__name__}")

    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        workspace = tmp_path / "workspace"
        os.environ["WORKSPACE_DIR"] = str(workspace)

        skills_root = tmp_path / "skills"
        demo_skill = skills_root / "demo-skill"
        demo_skill.mkdir(parents=True)
        (demo_skill / "SKILL.md").write_text(
            """---
name: demo-skill
description: Demo skill for offline smoke testing.
metadata:
  disco-role: operating
disable-model-invocation: true
---

# Demo skill

This file exists only to prove skill loading works.
""",
            encoding="utf-8",
        )

        agent = Agent(
            agent_name="Smoke-Agent",
            model_name="gpt-5.4",
            skills_dir=str(skills_root),
            persistent_memory=False,
            prompt_caching=False,
            context_compression=False,
            max_loops=1,
            print_on=False,
        )
        print(f"Agent name: {agent.agent_name}")
        print(f"Skills dir enabled: {agent.skills.enabled}")
        print(
            "Loaded skills: ",
            len(agent.skills.load_metadata()),
        )
        print(
            "Prompt contains skills header: ",
            "Available Skills" in agent.skills.prompt_for_task("demo"),
        )

        conv = Conversation(
            name="single-agent-smoke",
            save_filepath=str(tmp_path / "conversation.json"),
            conversations_dir=str(tmp_path / "conversations"),
        )
        conv.add("user", "hello")
        print(f"Conversation length: {len(conv.conversation_history)}")

        artifact_path = tmp_path / "artifact.txt"
        artifact = Artifact(
            file_path=str(artifact_path),
            contents="seed",
            edit_count=0,
        )
        artifact.create("seed")
        artifact.save()
        print(f"Artifact exists: {artifact_path.exists()}")

    print("single-agent smoke ok")


if __name__ == "__main__":
    main()
