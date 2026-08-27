#!/usr/bin/env python3
"""Service-free AdalFlow DataClass/parser smoke check.

This script performs deterministic checks for DataClass serialization,
required fields, DataClassParser instructions, and low-level string parsers.
It makes no provider, network, dataset, or model calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import List

import adalflow as adal


@dataclass
class Evidence(adal.DataClass):
    title: str = field(metadata={"desc": "Short evidence title."})
    score: float = field(default=1.0, metadata={"desc": "Confidence score."})


@dataclass
class StructuredAnswer(adal.DataClass):
    question: str = field(default=None, metadata={"desc": "Original input question."})
    answer: str = field(
        default_factory=adal.required_field(),
        metadata={"desc": "Concise answer."},
    )
    confidence: float = field(default=1.0, metadata={"desc": "Confidence from 0 to 1."})
    evidence: List[Evidence] = field(
        default_factory=list,
        metadata={"desc": "Evidence supporting the answer."},
    )

    __input_fields__ = ["question"]
    __output_fields__ = ["answer", "confidence", "evidence"]


def assert_required_field_error() -> None:
    try:
        StructuredAnswer(question="What is required?")
    except TypeError as exc:
        assert "required" in str(exc).lower()
    else:  # pragma: no cover - defensive; assertion should fail loudly.
        raise AssertionError("required_field() did not reject a missing answer")

    try:
        StructuredAnswer.from_dict({"question": "missing answer"})
    except ValueError as exc:
        assert "failed to load" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("from_dict() did not reject a missing required field")


def main() -> None:
    assert_required_field_error()

    instance = StructuredAnswer(
        question="What is AdalFlow?",
        answer="A framework for LLM task pipelines.",
        confidence=0.95,
        evidence=[Evidence(title="Docs", score=0.9)],
    )

    as_dict = instance.to_dict()
    assert list(as_dict.keys()) == ["question", "answer", "confidence", "evidence"]
    assert StructuredAnswer.from_dict(as_dict).to_dict() == as_dict
    assert StructuredAnswer.from_json(instance.to_json()).to_dict() == as_dict
    assert StructuredAnswer.from_yaml(instance.to_yaml()).to_dict() == as_dict

    included = instance.to_dict(include=["question", "answer"])
    assert included == {
        "question": "What is AdalFlow?",
        "answer": "A framework for LLM task pipelines.",
    }

    redacted = instance.to_dict(exclude={"StructuredAnswer": ["question"], "Evidence": ["score"]})
    assert redacted == {
        "answer": "A framework for LLM task pipelines.",
        "confidence": 0.95,
        "evidence": [{"title": "Docs"}],
    }

    parser = adal.DataClassParser(
        data_class=StructuredAnswer,
        return_data_class=True,
        format_type="json",
    )
    output_format = parser.get_output_format_str()
    assert "answer" in output_format and "confidence" in output_format
    assert "properties" in output_format  # instruction explains schema interpretation

    parsed = parser(
        '''```json
{"answer": "Service-free parse succeeded.", "confidence": 0.88, "evidence": [{"title": "unit", "score": 1.0}]}
```'''
    )
    assert isinstance(parsed, StructuredAnswer)
    assert parsed.answer == "Service-free parse succeeded."
    first_evidence = parsed.evidence[0]
    assert (first_evidence.title if hasattr(first_evidence, "title") else first_evidence["title"]) == "unit"

    dict_parser = adal.DataClassParser(
        data_class=StructuredAnswer,
        return_data_class=False,
        format_type="yaml",
    )
    parsed_dict = dict_parser(
        """```yaml
answer: YAML parse succeeded.
confidence: 0.77
evidence:
  - title: yaml
    score: 0.8
```"""
    )
    assert parsed_dict["answer"] == "YAML parse succeeded."

    assert adal.JsonParser()('{"ok": true, "items": [1, 2]}') == {"ok": True, "items": [1, 2]}
    assert adal.YamlParser()("flag: true\ncount: 3") == {"flag": True, "count": 3}
    assert adal.ListParser()('choose ["a", "b"]') == ["a", "b"]
    assert adal.BooleanParser()("Result: true") is True
    assert adal.IntParser()("n = 42") == 42
    assert abs(adal.FloatParser()("score=0.125") - 0.125) < 1e-12

    summary = {
        "status": "ok",
        "checks": [
            "required_field",
            "DataClass to_dict/json/yaml/from_dict",
            "include/exclude",
            "DataClassParser json/yaml",
            "string parsers",
        ],
    }
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
