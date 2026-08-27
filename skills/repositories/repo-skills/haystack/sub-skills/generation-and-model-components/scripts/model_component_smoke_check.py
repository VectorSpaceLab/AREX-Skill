#!/usr/bin/env python3
"""Deterministic smoke checks for Haystack generation/model components.

This script avoids network calls, provider credentials, and local model downloads. It verifies
public imports plus non-network behavior for prompt builders, answer building, JSON schema
validation, and top-p sampling.
"""

from __future__ import annotations

import json
import sys
from typing import Any

try:
    from haystack import Document
    from haystack.components.builders import AnswerBuilder, ChatPromptBuilder, PromptBuilder
    from haystack.components.samplers import TopPSampler
    from haystack.components.validators import JsonSchemaValidator
    from haystack.dataclasses import ChatMessage
except ModuleNotFoundError as exc:
    missing = exc.name or str(exc)
    print(
        "Haystack or one of its runtime dependencies is not importable. "
        f"Missing module: {missing}. Install `haystack-ai` with the optional dependencies needed for "
        "generation/model components, then rerun this script.",
        file=sys.stderr,
    )
    sys.exit(2)


def check_prompt_builder() -> None:
    builder = PromptBuilder(
        template="Answer in {{ language }}: {{ question }}",
        required_variables=["language", "question"],
    )
    rendered = builder.run(language="English", question="What is Haystack?")["prompt"]
    assert rendered == "Answer in English: What is Haystack?"

    try:
        builder.run(language="English")
    except ValueError as exc:
        assert "question" in str(exc)
    else:
        raise AssertionError("PromptBuilder did not reject a missing required variable")


def check_chat_prompt_builder() -> None:
    template = [
        ChatMessage.from_system("Answer as a {{ role }}."),
        ChatMessage.from_user("Question: {{ question }}"),
    ]
    builder = ChatPromptBuilder(template=template, required_variables="*")
    rendered = builder.run(role="teacher", question="What is a component?")["prompt"]

    assert len(rendered) == 2
    assert rendered[0].text == "Answer as a teacher."
    assert rendered[1].text == "Question: What is a component?"
    assert template[0].text == "Answer as a {{ role }}."


def check_answer_builder() -> None:
    documents = [
        Document(content="Berlin is in Germany."),
        Document(content="Paris is in France."),
    ]
    builder = AnswerBuilder(reference_pattern=r"\[(\d+)\]", return_only_referenced_documents=True)
    result = builder.run(
        query="Where is Paris?",
        replies=["Paris is in France [2]."],
        documents=documents,
    )

    answers = result["answers"]
    assert len(answers) == 1
    assert answers[0].data == "Paris is in France ."
    assert len(answers[0].documents) == 1
    assert answers[0].documents[0].content == "Paris is in France."
    assert answers[0].documents[0].meta["source_index"] == 2
    assert answers[0].documents[0].meta["referenced"] is True


def check_json_schema_validator() -> None:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {"answer": {"type": "string"}, "score": {"type": "number"}},
        "required": ["answer", "score"],
    }
    validator = JsonSchemaValidator(json_schema=schema)

    valid = validator.run(messages=[ChatMessage.from_assistant(json.dumps({"answer": "Berlin", "score": 0.9}))])
    assert "validated" in valid
    assert valid["validated"][0].text == '{"answer": "Berlin", "score": 0.9}'

    invalid_json = validator.run(messages=[ChatMessage.from_assistant("```json\n{}\n```")])
    assert "validation_error" in invalid_json
    assert "not a valid JSON object" in (invalid_json["validation_error"][0].text or "")

    invalid_schema = validator.run(messages=[ChatMessage.from_assistant(json.dumps({"answer": "Berlin"}))])
    assert "validation_error" in invalid_schema
    assert "score" in (invalid_schema["validation_error"][0].text or "")


def check_top_p_sampler() -> None:
    documents = [
        Document(content="low", score=0.1),
        Document(content="middle", score=0.4),
        Document(content="high", score=2.0),
    ]
    sampled = TopPSampler(top_p=0.8, min_top_k=1).run(documents=documents)["documents"]
    assert sampled
    assert sampled[0].content == "high"

    metadata_documents = [
        Document(content="a", meta={"similarity_score": -10.0}),
        Document(content="b", meta={"similarity_score": -1.0}),
    ]
    sampled_by_meta = TopPSampler(top_p=0.5, score_field="similarity_score").run(documents=metadata_documents)[
        "documents"
    ]
    assert sampled_by_meta[0].content == "b"


def main() -> int:
    checks = [
        check_prompt_builder,
        check_chat_prompt_builder,
        check_answer_builder,
        check_json_schema_validator,
        check_top_p_sampler,
    ]

    for check in checks:
        check()
        print(f"ok - {check.__name__}")

    print("All deterministic generation/model component smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
