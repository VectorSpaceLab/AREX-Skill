#!/usr/bin/env python3
"""Validate vLLM structured-output/tool/reasoning request fragments locally.

This helper performs conservative shape checks only. It does not import vLLM,
start a server, download models, execute tools, or contact external services.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

STRUCTURED_KEYS = {
    "choice",
    "regex",
    "json",
    "grammar",
    "structural_tag",
    "whitespace_pattern",
}

DEPRECATED_GUIDED_KEYS = {
    "guided_json",
    "guided_regex",
    "guided_choice",
    "guided_grammar",
    "guided_whitespace_pattern",
    "guided_decoding_backend",
}

TOOL_CHOICE_STRINGS = {"auto", "required", "none"}
HIGH_RISK_SCHEMA_KEYS = {
    "$recursiveRef",
    "$dynamicRef",
    "patternProperties",
    "dependentSchemas",
    "dependencies",
    "unevaluatedProperties",
    "unevaluatedItems",
    "contains",
    "propertyNames",
    "multipleOf",
    "if",
    "then",
    "else",
}
UNION_KEYS = {"anyOf", "oneOf", "allOf"}
KNOWN_TOOL_PARSERS = {
    "apertus",
    "cohere_command3",
    "cohere_command4",
    "deepseek_v3",
    "deepseek_v31",
    "deepseek_v32",
    "deepseek_v4",
    "ernie45",
    "functiongemma",
    "gemma4",
    "gigachat3",
    "glm45",
    "glm47",
    "granite",
    "granite-20b-fc",
    "granite4",
    "hermes",
    "hunyuan_a13b",
    "hy_v3",
    "internlm",
    "jamba",
    "kimi_k2",
    "lfm2",
    "llama3_json",
    "llama4_json",
    "llama4_pythonic",
    "longcat",
    "mimo",
    "minicpm5",
    "minimax",
    "minimax_m2",
    "minimax_m3",
    "mistral",
    "olmo3",
    "openai",
    "phi4_mini_json",
    "poolside_v1",
    "pythonic",
    "qwen3_coder",
    "qwen3_xml",
    "seed_oss",
    "step3",
    "step3p5",
    "xlam",
}
KNOWN_REASONING_PARSERS = {
    "cohere_command3",
    "cohere_command4",
    "deepseek_r1",
    "deepseek_v3",
    "deepseek_v4",
    "ernie45",
    "gemma4",
    "glm45",
    "glm47",
    "granite",
    "holo2",
    "hunyuan_a13b",
    "hy_v3",
    "kimi_k2",
    "mimo",
    "minimax_m2",
    "minimax_m2_append_think",
    "minimax_m3",
    "mistral",
    "nemotron_v3",
    "olmo3",
    "openai_gptoss",
    "poolside_v1",
    "qwen3",
    "seed_oss",
    "step3",
    "step3p5",
}

EXAMPLES: dict[str, dict[str, Any]] = {
    "json-schema": {
        "messages": [{"role": "user", "content": "Return a person as JSON."}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "person",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                    "required": ["name", "age"],
                    "additionalProperties": False,
                },
            },
        },
    },
    "unsupported-schema": {
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "risky",
                "schema": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "multipleOf": 5},
                        "node": {"anyOf": [{"$ref": "#"}, {"type": "null"}]},
                    },
                    "patternProperties": {"^x": {"type": "string"}},
                },
            },
        }
    },
    "tool-streaming": {
        "stream": True,
        "server_flags": {
            "enable_auto_tool_choice": True,
            "tool_call_parser": "xlam",
        },
        "messages": [{"role": "user", "content": "Weather in Boston?"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather.",
                    "strict": True,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"},
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        },
                        "required": ["location", "unit"],
                        "additionalProperties": False,
                    },
                },
            }
        ],
        "tool_choice": "auto",
        "client_notes": {"accumulates_streaming_tool_call_arguments": True},
    },
    "reasoning": {
        "server_flags": {"reasoning_parser": "qwen3"},
        "messages": [{"role": "user", "content": "9.11 and 9.8, which is greater?"}],
        "thinking_token_budget": 16,
    },
}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors


def iter_schema_items(value: Any, path: str = "$") -> Iterable[tuple[str, Any, str]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield key, child, child_path
            yield from iter_schema_items(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_schema_items(child, f"{path}[{index}]")


def load_request(args: argparse.Namespace) -> dict[str, Any]:
    sources = [args.input is not None, args.json_text is not None, args.example is not None]
    if sum(sources) != 1:
        raise ValueError("choose exactly one of --input, --json, or --example")
    if args.example is not None:
        return EXAMPLES[args.example]
    if args.input is not None:
        text = Path(args.input).read_text(encoding="utf-8")
    else:
        text = args.json_text
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError("request fragment must be a JSON object")
    return loaded


def get_server_flags(request: Mapping[str, Any]) -> Mapping[str, Any]:
    flags = request.get("server_flags", {})
    return flags if isinstance(flags, Mapping) else {}


def validate_response_format(request: Mapping[str, Any], report: Report) -> None:
    response_format = request.get("response_format")
    if response_format is None:
        return
    if not isinstance(response_format, Mapping):
        report.error("response_format must be an object")
        return

    fmt_type = response_format.get("type")
    if fmt_type == "json_schema":
        json_schema = response_format.get("json_schema")
        if not isinstance(json_schema, Mapping):
            report.error("response_format.type=json_schema requires json_schema object")
            return
        if not isinstance(json_schema.get("name"), str) or not json_schema.get("name"):
            report.error("json_schema.name must be a non-empty string")
        schema = json_schema.get("schema")
        if not isinstance(schema, Mapping):
            report.error("json_schema.schema must be an object")
            return
        validate_schema(schema, report, location="response_format.json_schema.schema")
    elif fmt_type == "json_object":
        report.warn(
            "json_object mode checks JSON syntax only; use json_schema when exact fields matter"
        )
    elif fmt_type == "structural_tag":
        validate_structural_tag(response_format, report, "response_format")
    elif fmt_type is None:
        report.error("response_format.type is required")
    else:
        report.warn(f"unrecognized response_format.type {fmt_type!r}; verify API support")


def validate_structured_outputs(request: Mapping[str, Any], report: Report) -> None:
    for key in DEPRECATED_GUIDED_KEYS:
        if key in request:
            report.error(f"deprecated field {key!r}; use structured_outputs instead")

    structured = request.get("structured_outputs")
    extra_body = request.get("extra_body")
    if structured is None and isinstance(extra_body, Mapping):
        structured = extra_body.get("structured_outputs")

    if structured is None:
        return
    if not isinstance(structured, Mapping):
        report.error("structured_outputs must be an object")
        return

    keys = set(structured)
    recognized = keys & STRUCTURED_KEYS
    if not recognized:
        report.error("structured_outputs must include one of choice, regex, json, grammar, structural_tag")
        return
    primary = recognized - {"whitespace_pattern"}
    if len(primary) > 1:
        report.warn(
            "multiple structured_outputs constraints found; keep one primary constraint unless intentional"
        )

    if "choice" in structured:
        choice = structured["choice"]
        if not isinstance(choice, list) or not choice or not all(
            isinstance(item, str) for item in choice
        ):
            report.error("structured_outputs.choice must be a non-empty list of strings")
    if "regex" in structured:
        pattern = structured["regex"]
        if not isinstance(pattern, str) or not pattern:
            report.error("structured_outputs.regex must be a non-empty string")
        else:
            try:
                re.compile(pattern)
            except re.error as exc:
                report.warn(f"regex is invalid for Python re ({exc}); backend dialect may also differ")
            if pattern.endswith("\\n") and "stop" not in request:
                report.warn("regex appears newline-terminated; consider stop=['\\n'] for serving requests")
    if "json" in structured:
        schema = structured["json"]
        if not isinstance(schema, Mapping):
            report.error("structured_outputs.json must be a JSON schema object")
        else:
            validate_schema(schema, report, location="structured_outputs.json")
    if "grammar" in structured:
        grammar = structured["grammar"]
        if not isinstance(grammar, str) or not grammar.strip():
            report.error("structured_outputs.grammar must be a non-empty grammar string")
        else:
            validate_grammar(grammar, report)
    if "structural_tag" in structured:
        validate_structural_tag(structured["structural_tag"], report, "structured_outputs.structural_tag")


def validate_schema(schema: Mapping[str, Any], report: Report, *, location: str) -> None:
    schema_type = schema.get("type")
    if schema_type is None and not any(key in schema for key in UNION_KEYS):
        report.warn(f"{location}: schema has no type; backend compatibility may be reduced")

    if schema_type == "object":
        properties = schema.get("properties")
        if not isinstance(properties, Mapping) or not properties:
            report.warn(f"{location}: object schema should define non-empty properties")
        required = schema.get("required")
        if required is None:
            report.warn(f"{location}: object schema should define required fields")
        elif not isinstance(required, list) or not all(isinstance(item, str) for item in required):
            report.error(f"{location}: required must be a list of strings")
        if schema.get("additionalProperties") is not False:
            report.warn(
                f"{location}: set additionalProperties=false for stricter vLLM/tool schemas"
            )

    for key, value, path in iter_schema_items(schema):
        if key in HIGH_RISK_SCHEMA_KEYS:
            report.warn(f"{location}{path[1:]} uses high-risk keyword {key!r}")
        if key in UNION_KEYS:
            if not isinstance(value, list) or len(value) > 3:
                report.warn(f"{location}{path[1:]} uses complex {key!r}; simplify if backend rejects it")
        if key == "$ref" and value == "#":
            report.warn(f"{location}{path[1:]} appears recursive; many guided backends reject recursion")


def validate_grammar(grammar: str, report: Report) -> None:
    if "::=" not in grammar and ":" not in grammar:
        report.error("grammar should contain production rules such as root ::= ...")
    if "root" not in grammar and "start" not in grammar:
        report.warn("grammar has no obvious root/start production")
    if grammar.count('"') % 2:
        report.warn("grammar has an odd number of double quotes; check literal quoting")


def validate_structural_tag(value: Any, report: Report, location: str) -> None:
    if not isinstance(value, Mapping):
        report.error(f"{location} must be an object")
        return
    structures = value.get("structures")
    if not isinstance(structures, list) or not structures:
        report.error(f"{location}.structures must be a non-empty list")
        return
    for index, structure in enumerate(structures):
        item_location = f"{location}.structures[{index}]"
        if not isinstance(structure, Mapping):
            report.error(f"{item_location} must be an object")
            continue
        for key in ("begin", "schema", "end"):
            if key not in structure:
                report.error(f"{item_location}.{key} is required")
        schema = structure.get("schema")
        if isinstance(schema, Mapping):
            validate_schema(schema, report, location=f"{item_location}.schema")


def validate_tools(request: Mapping[str, Any], report: Report) -> None:
    tools = request.get("tools")
    tool_choice = request.get("tool_choice")
    flags = get_server_flags(request)

    if tools is None:
        if tool_choice is not None:
            report.error("tool_choice is set but tools is missing")
        return
    if not isinstance(tools, list) or not tools:
        report.error("tools must be a non-empty list when provided")
        return

    function_names: set[str] = set()
    strict_tools = 0
    for index, tool in enumerate(tools):
        location = f"tools[{index}]"
        if not isinstance(tool, Mapping):
            report.error(f"{location} must be an object")
            continue
        if tool.get("type") != "function":
            report.warn(f"{location}.type is not 'function'; verify API surface supports it")
        function = tool.get("function")
        if not isinstance(function, Mapping):
            report.error(f"{location}.function must be an object")
            continue
        name = function.get("name")
        if not isinstance(name, str) or not name:
            report.error(f"{location}.function.name must be a non-empty string")
        else:
            function_names.add(name)
        if function.get("strict") is True:
            strict_tools += 1
        parameters = function.get("parameters")
        if not isinstance(parameters, Mapping):
            report.error(f"{location}.function.parameters must be a JSON schema object")
        else:
            validate_schema(parameters, report, location=f"{location}.function.parameters")

    if tool_choice is None:
        report.note("tools provided without tool_choice; serving default behavior applies")
    elif isinstance(tool_choice, str):
        if tool_choice not in TOOL_CHOICE_STRINGS:
            report.error("string tool_choice must be one of auto, required, none")
        if tool_choice == "auto":
            if not flags.get("enable_auto_tool_choice"):
                report.warn("tool_choice='auto' requires server flag --enable-auto-tool-choice")
            parser = flags.get("tool_call_parser")
            if not parser:
                report.warn("tool_choice='auto' requires server flag --tool-call-parser <parser>")
            elif parser not in KNOWN_TOOL_PARSERS:
                report.warn(f"unknown tool_call_parser {parser!r}; check parser name spelling")
            if not strict_tools:
                report.warn(
                    "auto tool choice has no strict=true tools; arguments may be unconstrained raw parser output"
                )
        if tool_choice == "none" and tools:
            report.note(
                "tools with tool_choice='none' may still appear in prompts unless server excludes them"
            )
    elif isinstance(tool_choice, Mapping):
        function = tool_choice.get("function")
        name = function.get("name") if isinstance(function, Mapping) else None
        if tool_choice.get("type") != "function" or not isinstance(name, str):
            report.error("named tool_choice must be {'type':'function','function':{'name':...}}")
        elif function_names and name not in function_names:
            report.error(f"named tool_choice references unknown function {name!r}")
    else:
        report.error("tool_choice must be a string or named-function object")

    if request.get("stream") is True:
        client_notes = request.get("client_notes", {})
        accumulates = isinstance(client_notes, Mapping) and client_notes.get(
            "accumulates_streaming_tool_call_arguments"
        )
        if not accumulates:
            report.warn(
                "streaming tool calls arrive as deltas; client should accumulate arguments before json.loads"
            )


def validate_reasoning(request: Mapping[str, Any], report: Report) -> None:
    flags = get_server_flags(request)
    parser = flags.get("reasoning_parser") or request.get("reasoning_parser")
    reasoning_requested = any(
        key in request
        for key in (
            "thinking_token_budget",
            "reasoning_effort",
            "reasoning",
            "reasoning_config",
        )
    ) or parser is not None

    extra_body = request.get("extra_body")
    chat_template_kwargs = None
    if isinstance(extra_body, Mapping):
        chat_template_kwargs = extra_body.get("chat_template_kwargs")

    if not reasoning_requested:
        return
    if parser is None:
        report.warn("reasoning-related fields present but no server_flags.reasoning_parser supplied")
    elif parser not in KNOWN_REASONING_PARSERS:
        report.warn(f"unknown reasoning_parser {parser!r}; check parser name spelling")

    if "reasoning_content" in request:
        report.warn("reasoning_content is deprecated; use reasoning")
    if "thinking_token_budget" in request and not isinstance(
        request["thinking_token_budget"], int
    ):
        report.error("thinking_token_budget must be an integer token count")
    if "reasoning_effort" in request and request["reasoning_effort"] not in {
        "none",
        "low",
        "medium",
        "high",
    }:
        report.error("reasoning_effort must be one of none, low, medium, high")
    if chat_template_kwargs is not None and not isinstance(chat_template_kwargs, Mapping):
        report.error("extra_body.chat_template_kwargs must be an object when provided")

    structured_enabled = flags.get("structured_outputs_enable_in_reasoning")
    has_structured = "response_format" in request or "structured_outputs" in request
    if has_structured and parser is not None and not structured_enabled:
        report.warn(
            "structured outputs plus reasoning may require --structured-outputs-config.enable_in_reasoning=True for some models"
        )


def validate_request(request: Mapping[str, Any]) -> Report:
    report = Report()
    if "messages" in request and not isinstance(request["messages"], list):
        report.error("messages must be a list when provided")
    if "extra_body" in request and not isinstance(request["extra_body"], Mapping):
        report.error("extra_body must be an object when provided")
    if "server_flags" in request and not isinstance(request["server_flags"], Mapping):
        report.error("server_flags must be an object when provided")

    validate_response_format(request, report)
    validate_structured_outputs(request, report)
    validate_tools(request, report)
    validate_reasoning(request, report)

    if "response_format" in request and "structured_outputs" in request:
        report.warn(
            "both response_format and structured_outputs are present; ensure the API accepts this combination"
        )
    return report


def print_report(report: Report, *, verbose: bool) -> None:
    if report.ok:
        print("OK: request shape looks usable")
    else:
        print("FAILED: request shape has errors")
    for message in report.errors:
        print(f"ERROR: {message}")
    for message in report.warnings:
        print(f"WARN: {message}")
    if verbose:
        for message in report.notes:
            print(f"NOTE: {message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate vLLM structured_outputs, response_format, tools, "
            "tool_choice, and reasoning request fragments without contacting a server."
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="Path to a JSON request fragment")
    source.add_argument("--json", dest="json_text", help="Inline JSON request fragment")
    source.add_argument(
        "--example",
        choices=sorted(EXAMPLES),
        help="Validate a bundled tiny example fragment",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print informational notes in addition to warnings and errors",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        request = load_request(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    report = validate_request(request)
    print_report(report, verbose=args.verbose)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
