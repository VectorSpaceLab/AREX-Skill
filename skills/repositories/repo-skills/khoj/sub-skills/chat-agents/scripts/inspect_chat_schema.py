#!/usr/bin/env python3
"""Inspect Khoj chat and agent schemas without starting the server."""

from __future__ import annotations

import argparse
import json
import os
from enum import Enum
from typing import Any


def model_schema(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_json_schema"):
        return model.model_json_schema()
    if hasattr(model, "schema"):
        return model.schema()
    raise TypeError(f"Unsupported schema model: {model!r}")


def enum_values(enum_cls: type[Enum]) -> list[str]:
    return [item.value for item in enum_cls]


def choice_values(choices: Any) -> list[str]:
    return [key for key, _label in choices]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print Khoj chat/agent Pydantic schemas, command values, agent choices, and stream event names."
    )
    parser.add_argument(
        "--pretty",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Pretty-print JSON output. Use --no-pretty for compact JSON.",
    )
    args = parser.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "khoj.app.settings")

    import django

    django.setup()

    from khoj.database.models import Agent
    from khoj.processor.conversation.utils import ChatEvent
    from khoj.routers.api_agents import ModifyAgentBody, ModifyHiddenAgentBody
    from khoj.utils.helpers import ConversationCommand, command_descriptions_for_agent, mode_descriptions_for_agent
    from khoj.utils.rawconfig import ChatRequestBody, FileAttachment

    payload = {
        "schemas": {
            "ChatRequestBody": model_schema(ChatRequestBody),
            "FileAttachment": model_schema(FileAttachment),
            "ModifyAgentBody": model_schema(ModifyAgentBody),
            "ModifyHiddenAgentBody": model_schema(ModifyHiddenAgentBody),
        },
        "choices": {
            "ConversationCommand": enum_values(ConversationCommand),
            "ChatEvent": enum_values(ChatEvent),
            "AgentPrivacyLevel": choice_values(Agent.PrivacyLevel.choices),
            "AgentInputToolOptions": choice_values(Agent.InputToolOptions.choices),
            "AgentOutputModeOptions": choice_values(Agent.OutputModeOptions.choices),
            "AgentStyleColorTypes": choice_values(Agent.StyleColorTypes.choices),
            "AgentStyleIconTypes": choice_values(Agent.StyleIconTypes.choices),
        },
        "agent_option_descriptions": {
            "input_tools": {key.value: value for key, value in command_descriptions_for_agent.items()},
            "output_modes": {key.value: value for key, value in mode_descriptions_for_agent.items()},
        },
    }

    indent = 2 if args.pretty else None
    print(json.dumps(payload, indent=indent, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
