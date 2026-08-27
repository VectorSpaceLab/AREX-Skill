#!/usr/bin/env bash
set -euo pipefail

swarms --help >/dev/null

python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory

from swarms.cli.main import setup_argument_parser
from swarms.agents.create_agents_from_yaml import load_yaml_safely
from swarms.utils.agent_loader_markdown import MarkdownAgentLoader

parser = setup_argument_parser()
assert parser.parse_args([
    "agent",
    "--name", "Demo",
    "--description", "Demo agent",
    "--system-prompt", "You are helpful",
]).command == "agent"

yaml_text = """\
agents:
  - agent_name: DemoAgent
    system_prompt: You are concise.
    model_name: gpt-5.4
    max_loops: 1
"""
config = load_yaml_safely(yaml_string=yaml_text)
assert config["agents"][0]["agent_name"] == "DemoAgent"

with TemporaryDirectory() as td:
    path = Path(td) / "demo.md"
    path.write_text(
        """---\nname: DemoAgent\ndescription: Demo markdown agent\nmodel_name: gpt-5.4\nmax_loops: 1\n---\nYou are concise.\n""",
        encoding="utf-8",
    )
    loader = MarkdownAgentLoader()
    parsed = loader.parse_markdown_file(str(path))
    assert parsed.name == "DemoAgent"
    assert "You are concise." in parsed.system_prompt

print("cli smoke ok")
PY
