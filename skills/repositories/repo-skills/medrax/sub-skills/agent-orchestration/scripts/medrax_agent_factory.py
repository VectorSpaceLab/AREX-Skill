#!/usr/bin/env python3
"""Adapted, explicit MedRAX agent factory with a safe no-construction default.

Copy this helper into an integration project or import ``build_agent`` from its
location in the skill. The module never creates a chat client, a tool, or a
network request at import time. Constructing selected tools is explicit and can
load optional model weights, so validate selection first.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any


TOOL_NAMES = (
    "ChestXRayClassifierTool",
    "ChestXRaySegmentationTool",
    "LlavaMedTool",
    "XRayVQATool",
    "ChestXRayReportGeneratorTool",
    "XRayPhraseGroundingTool",
    "ChestXRayGeneratorTool",
    "ImageVisualizerTool",
    "DicomProcessorTool",
)
UTILITY_TOOL_NAMES = ("ImageVisualizerTool", "DicomProcessorTool")


def validate_tool_selection(tools_to_use: Iterable[str] | None) -> list[str]:
    """Return a nonempty explicit selection or raise without importing tools."""
    if tools_to_use is None:
        raise ValueError(
            "Pass an explicit nonempty tools_to_use list; refusing the source default of all tools."
        )
    selected = list(tools_to_use)
    if not selected:
        raise ValueError("tools_to_use cannot be empty; use a fake model for graph-only tests.")
    unknown = sorted(set(selected) - set(TOOL_NAMES))
    if unknown:
        raise ValueError(f"Unknown MedRAX tool name(s): {unknown}")
    if len(set(selected)) != len(selected):
        raise ValueError("tools_to_use must not contain duplicate names")
    return selected


def openai_kwargs_from_env() -> dict[str, str]:
    """Read configured endpoint credentials without printing their values."""
    kwargs: dict[str, str] = {}
    if api_key := os.getenv("OPENAI_API_KEY"):
        kwargs["api_key"] = api_key
    if base_url := os.getenv("OPENAI_BASE_URL"):
        kwargs["base_url"] = base_url
    return kwargs


def _tool_factories(model_dir: str, temp_dir: str, device: str) -> dict[str, Callable[[], Any]]:
    """Build constructors lazily; calling a selected factory may load weights."""
    # Import occurs only when a caller explicitly requests real construction.
    # The package exposes its public tool classes through medrax.tools.
    from medrax.tools import (
        ChestXRayClassifierTool,
        ChestXRayGeneratorTool,
        ChestXRayReportGeneratorTool,
        ChestXRaySegmentationTool,
        DicomProcessorTool,
        ImageVisualizerTool,
        LlavaMedTool,
        XRayPhraseGroundingTool,
        XRayVQATool,
    )

    return {
        "ChestXRayClassifierTool": lambda: ChestXRayClassifierTool(device=device),
        "ChestXRaySegmentationTool": lambda: ChestXRaySegmentationTool(device=device),
        "LlavaMedTool": lambda: LlavaMedTool(cache_dir=model_dir, device=device, load_in_8bit=True),
        "XRayVQATool": lambda: XRayVQATool(cache_dir=model_dir, device=device),
        "ChestXRayReportGeneratorTool": lambda: ChestXRayReportGeneratorTool(
            cache_dir=model_dir, device=device
        ),
        "XRayPhraseGroundingTool": lambda: XRayPhraseGroundingTool(
            cache_dir=model_dir, temp_dir=temp_dir, load_in_8bit=True, device=device
        ),
        "ChestXRayGeneratorTool": lambda: ChestXRayGeneratorTool(
            model_path=f"{model_dir}/roentgen", temp_dir=temp_dir, device=device
        ),
        "ImageVisualizerTool": ImageVisualizerTool,
        "DicomProcessorTool": lambda: DicomProcessorTool(temp_dir=temp_dir),
    }


def build_agent(
    prompt_file: str | Path,
    *,
    tools_to_use: Iterable[str],
    model_dir: str | None = None,
    temp_dir: str = "temp",
    device: str = "cuda",
    model: str = "chatgpt-4o-latest",
    temperature: float = 0.7,
    top_p: float = 0.95,
    openai_kwargs: dict[str, Any] | None = None,
    system_prompt_section: str = "MEDICAL_ASSISTANT",
    log_tools: bool = True,
    log_dir: str | Path | None = "logs",
):
    """Construct and return ``(Agent, tools_dict)`` from explicit settings.

    This is an adapted counterpart to the application initializer. It rejects
    all-tools-by-accident selection, validates names before importing tool
    classes, permits an explicit prompt section, and exposes log settings.
    """
    selected = validate_tool_selection(tools_to_use)
    if any(name not in UTILITY_TOOL_NAMES for name in selected) and not model_dir:
        raise ValueError("model_dir is required for a model-backed tool")
    prompt_path = Path(prompt_file)
    if not prompt_path.is_file():
        raise FileNotFoundError(f"Prompts file not found: {prompt_path}")

    from langchain_openai import ChatOpenAI
    from langgraph.checkpoint.memory import MemorySaver
    from medrax.agent import Agent
    from medrax.utils.utils import load_prompts_from_file

    prompts = load_prompts_from_file(str(prompt_path))
    if system_prompt_section not in prompts:
        raise KeyError(f"Prompt section not found: {system_prompt_section}")
    factories = _tool_factories(model_dir or "", temp_dir, device)
    tools_dict = {name: factories[name]() for name in selected}
    client_kwargs = dict(openai_kwargs or {})
    chat_model = ChatOpenAI(
        model=model, temperature=temperature, top_p=top_p, **client_kwargs
    )
    agent = Agent(
        chat_model,
        tools=list(tools_dict.values()),
        system_prompt=prompts[system_prompt_section],
        checkpointer=MemorySaver(),
        log_tools=log_tools,
        log_dir=str(log_dir) if log_dir is not None else None,
    )
    return agent, tools_dict


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-tools", action="store_true")
    parser.add_argument("--validate", nargs="*", metavar="TOOL")
    args = parser.parse_args()
    if args.list_tools:
        print("\n".join(TOOL_NAMES))
        return 0
    if args.validate is not None:
        try:
            print("\n".join(validate_tool_selection(args.validate)))
        except ValueError as exc:
            parser.error(str(exc))
        return 0
    parser.print_help()
    print("\nNo agent was constructed. Use --list-tools or --validate for safe checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
