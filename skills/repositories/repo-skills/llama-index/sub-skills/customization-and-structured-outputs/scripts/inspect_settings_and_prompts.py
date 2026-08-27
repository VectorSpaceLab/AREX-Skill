#!/usr/bin/env python3
"""Inspect LlamaIndex Settings, prompts, parsers, callbacks, and eval shapes.

This script intentionally avoids external provider calls. It uses MockLLM and
MockEmbedding for safe local checks and prints guidance for prompt and structured
output customization.
"""

from __future__ import annotations

import argparse
import json
from contextlib import contextmanager
from typing import Any, Dict

from llama_index.core import Settings
from llama_index.core.bridge.pydantic import BaseModel, Field
from llama_index.core.callbacks import CallbackManager, CBEventType, TokenCountingHandler
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.evaluation import EvaluationResult
from llama_index.core.llms import MockLLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.core.prompts import PromptTemplate


class DemoAnswer(BaseModel):
    answer: str = Field(description="Concise answer")
    evidence: list[str] = Field(description="Evidence snippets")
    confidence: float = Field(ge=0, le=1, description="Confidence from 0 to 1")


@contextmanager
def isolated_settings(**overrides: Any):
    snapshot: Dict[str, Any] = {
        "_llm": Settings._llm,
        "_embed_model": Settings._embed_model,
        "_callback_manager": Settings._callback_manager,
        "_node_parser": Settings._node_parser,
        "_transformations": Settings._transformations,
        "_prompt_helper": Settings._prompt_helper,
        "_chat_prompt_helper": Settings._chat_prompt_helper,
    }
    try:
        for name, value in overrides.items():
            setattr(Settings, name, value)
        yield
    finally:
        for name, value in snapshot.items():
            setattr(Settings, name, value)


def describe_settings() -> None:
    print("== Settings snapshot ==")
    print(f"llm configured: {Settings._llm is not None}")
    print(f"embed_model configured: {Settings._embed_model is not None}")
    print(f"callback_manager configured: {Settings._callback_manager is not None}")
    print(f"node_parser configured: {Settings._node_parser is not None}")
    print(f"transformations configured: {Settings._transformations is not None}")
    print("Tip: use explicit constructor arguments for local overrides; use Settings for app-wide defaults.")


def inspect_prompt_and_parser() -> None:
    print("\n== Prompt and parser check ==")
    parser = PydanticOutputParser(output_cls=DemoAnswer)
    prompt = PromptTemplate(
        "Context: {context_str}\nQuestion: {query_str}\nReturn JSON only.",
        output_parser=parser,
    )
    formatted = prompt.format(context_str="LlamaIndex supports structured output.", query_str="What is supported?")
    print("Prompt template variables:", prompt.template_vars)
    print("Formatted prompt includes schema:", "JSON schema" in formatted)
    print("Schema fields:", sorted(DemoAnswer.model_json_schema().get("properties", {}).keys()))

    valid_json = json.dumps(
        {
            "answer": "Structured output is supported.",
            "evidence": ["PydanticOutputParser validates JSON."],
            "confidence": 0.9,
        }
    )
    parsed = parser.parse(valid_json)
    print("Parsed model type:", type(parsed).__name__)
    print("Parsed confidence:", parsed.confidence)


def inspect_program_contract() -> None:
    print("\n== Pydantic program contract ==")
    program = LLMTextCompletionProgram.from_defaults(
        output_cls=DemoAnswer,
        prompt_template_str="Context: {context_str}\nQuestion: {query_str}\nReturn JSON only.",
        llm=MockLLM(max_tokens=32),
    )
    print("Program output class:", program.output_cls.__name__)
    print("Program prompt variables:", program.prompt.template_vars)
    print("Note: MockLLM is safe for construction checks; use a fake JSON-returning LLM for exact program calls.")


def inspect_callbacks() -> None:
    print("\n== Callback check ==")
    counter = TokenCountingHandler(tokenizer=lambda text: text.split())
    manager = CallbackManager([counter])
    with manager.as_trace("settings-and-prompts-demo"):
        with manager.event(CBEventType.QUERY, payload={"query": "demo"}):
            pass
    print("Callback handlers:", [type(handler).__name__ for handler in manager.handlers])
    print("Trace recorded without external APIs: yes")


def inspect_evaluation_shape() -> None:
    print("\n== EvaluationResult shape ==")
    result = EvaluationResult(
        query="What is checked?",
        contexts=["Settings, prompts, parsers, callbacks."],
        response="The script checks customization surfaces.",
        passing=True,
        score=1.0,
        feedback="Shape-only local check.",
    )
    print(result.model_dump())


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect LlamaIndex customization surfaces without provider calls.")
    parser.add_argument("--skip-isolation-demo", action="store_true", help="Do not temporarily set MockLLM/MockEmbedding Settings.")
    args = parser.parse_args()

    describe_settings()
    if args.skip_isolation_demo:
        inspect_prompt_and_parser()
        inspect_program_contract()
        inspect_callbacks()
        inspect_evaluation_shape()
        return

    with isolated_settings(
        llm=MockLLM(max_tokens=64),
        embed_model=MockEmbedding(embed_dim=8),
        node_parser=SentenceSplitter(chunk_size=128, chunk_overlap=16),
    ):
        print("\n== Isolated Settings demo ==")
        print("LLM type:", type(Settings.llm).__name__)
        print("Embedding type:", type(Settings.embed_model).__name__)
        print("Chunk size:", Settings.chunk_size)
        print("Chunk overlap:", Settings.chunk_overlap)
        inspect_prompt_and_parser()
        inspect_program_contract()
        inspect_callbacks()
        inspect_evaluation_shape()

    print("\nSettings restored after isolation demo.")


if __name__ == "__main__":
    main()
