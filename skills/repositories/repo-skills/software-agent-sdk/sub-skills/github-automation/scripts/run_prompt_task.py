#!/usr/bin/env python3
"""Run an OpenHands agent for a prompt read from a string, file, or URL."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from openhands.sdk import LLM, Conversation
from openhands.tools.preset.default import get_default_agent


def is_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def load_prompt(prompt_location: str) -> str:
    if is_url(prompt_location):
        with urlopen(prompt_location) as response:
            return response.read().decode("utf-8")
    return Path(prompt_location).read_text()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt_location", nargs="?", help="Prompt file path or URL")
    args = parser.parse_args()

    prompt_string = os.getenv("PROMPT_STRING")
    if prompt_string and args.prompt_location:
        print("Provide only one of PROMPT_STRING or prompt_location.", file=sys.stderr)
        return 1
    if not prompt_string and not args.prompt_location:
        print("Provide PROMPT_STRING or prompt_location.", file=sys.stderr)
        return 1

    prompt = prompt_string if prompt_string else load_prompt(args.prompt_location)
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("LLM_API_KEY environment variable is not set.", file=sys.stderr)
        return 1

    os.environ.setdefault("OPENHANDS_SUPPRESS_BANNER", "1")

    llm = LLM(
        model=os.getenv("LLM_MODEL", "gpt-5.5"),
        api_key=api_key,
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="agent_script",
        drop_params=True,
    )
    agent = get_default_agent(llm=llm, cli_mode=True)
    conversation = Conversation(agent=agent, workspace=os.getcwd())
    conversation.send_message(prompt)
    conversation.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
