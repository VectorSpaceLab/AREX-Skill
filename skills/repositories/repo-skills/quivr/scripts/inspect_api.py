#!/usr/bin/env python3
"""Inspect the live Quivr API without touching networked providers."""

from __future__ import annotations

import argparse
import inspect
import json
import os
from importlib.metadata import PackageNotFoundError, version

os.environ.setdefault("OPENAI_API_KEY", "test")

from quivr_core import Brain
from quivr_core.llm import LLMEndpoint
from quivr_core.processor.implementations.simple_txt_processor import (
    SimpleTxtProcessor,
)
from quivr_core.rag.entities.chat import ChatHistory
from quivr_core.rag.entities.config import LLMEndpointConfig, RetrievalConfig


TARGETS = {
    "Brain.afrom_langchain_documents": Brain.afrom_langchain_documents,
    "Brain.afrom_files": Brain.afrom_files,
    "Brain.aask": Brain.aask,
    "Brain.ask_streaming": Brain.ask_streaming,
    "Brain.ask": Brain.ask,
    "Brain.asearch": Brain.asearch,
    "SimpleTxtProcessor.process_file": SimpleTxtProcessor.process_file,
    "LLMEndpoint.from_config": LLMEndpoint.from_config,
    "ChatHistory.iter_pairs": ChatHistory.iter_pairs,
}


def package_version() -> str:
    try:
        return version("quivr-core")
    except PackageNotFoundError:
        return "dev"


def collect_signatures() -> dict[str, str]:
    return {name: str(inspect.signature(target)) for name, target in TARGETS.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-import",
        action="store_true",
        help="Import the public API and print a short success message.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the inspection result as JSON instead of plain text.",
    )
    args = parser.parse_args()

    data = {
        "quivr_core_version": package_version(),
        "signatures": collect_signatures(),
        "llm_default": LLMEndpointConfig().model_dump(),
        "retrieval_default": RetrievalConfig().model_dump(),
    }

    if args.check_import:
        print("quivr_core import ok")

    if args.json:
        print(json.dumps(data, indent=2, default=str))
    else:
        print(f"quivr-core {data['quivr_core_version']}")
        for name, sig in data["signatures"].items():
            print(f"{name}{sig}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
