#!/usr/bin/env python3
"""
Parse MiniMind thinking/tool-call tags and optionally execute deterministic mock tools.

This helper is intentionally model-free: it checks response parsing and tool-loop
plumbing without loading weights, downloading data, using credentials, or running
untrusted tool implementations.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import operator
import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

TOOL_CALL_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)

DEFAULT_TEXT = (
    "<think>Need a calculator.</think>\n"
    '<tool_call>{"name":"calculate_math","arguments":{"expression":"256 * 37"}}</tool_call>'
)

TOOL_SPECS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "calculate_math",
            "description": "Calculate a bounded arithmetic expression.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Return a deterministic current time for smoke tests.",
            "parameters": {
                "type": "object",
                "properties": {"timezone": {"type": "string", "default": "Asia/Shanghai"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "random_number",
            "description": "Return a seeded pseudo-random integer.",
            "parameters": {
                "type": "object",
                "properties": {"min": {"type": "integer"}, "max": {"type": "integer"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "text_length",
            "description": "Count characters and whitespace-separated words.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "unit_converter",
            "description": "Convert a small set of common units.",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {"type": "number"},
                    "from_unit": {"type": "string"},
                    "to_unit": {"type": "string"},
                },
                "required": ["value", "from_unit", "to_unit"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Return fixed weather for smoke tests.",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}, "unit": {"type": "string"}},
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "Return fixed exchange-rate data for smoke tests.",
            "parameters": {
                "type": "object",
                "properties": {"from_currency": {"type": "string"}, "to_currency": {"type": "string"}},
                "required": ["from_currency", "to_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "translate_text",
            "description": "Return deterministic toy translations.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}, "target_language": {"type": "string"}},
                "required": ["text", "target_language"],
            },
        },
    },
]

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_ALLOWED_FUNCS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "pow": pow,
}
_ALLOWED_CONSTS = {"pi": math.pi, "e": math.e}


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def _count_nodes(node: ast.AST) -> int:
    return sum(1 for _ in ast.walk(node))


def _eval_ast(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name) and node.id in _ALLOWED_CONSTS:
        return _ALLOWED_CONSTS[node.id]
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
        return _ALLOWED_UNARY[type(node.op)](_eval_ast(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 12:
            raise ValueError("exponent too large for smoke helper")
        result = _ALLOWED_BINOPS[type(node.op)](left, right)
        if abs(result) > 1e15:
            raise ValueError("result magnitude too large for smoke helper")
        return result
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _ALLOWED_FUNCS:
        if node.keywords:
            raise ValueError("keyword arguments are not allowed")
        args = [_eval_ast(arg) for arg in node.args]
        if len(args) > 3:
            raise ValueError("too many function arguments")
        result = _ALLOWED_FUNCS[node.func.id](*args)
        if isinstance(result, (int, float)) and abs(result) > 1e15:
            raise ValueError("result magnitude too large for smoke helper")
        return result
    raise ValueError(f"unsupported expression node: {type(node).__name__}")


def safe_calculate(expression: str) -> Any:
    normalized = (
        str(expression)
        .replace("^", "**")
        .replace("×", "*")
        .replace("÷", "/")
        .replace("−", "-")
        .replace("²", "**2")
        .replace("³", "**3")
        .replace("（", "(")
        .replace("）", ")")
    )
    if len(normalized) > 160:
        raise ValueError("expression too long")
    tree = ast.parse(normalized, mode="eval")
    if _count_nodes(tree) > 80:
        raise ValueError("expression too complex")
    value = _eval_ast(tree)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def parse_tool_calls(text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    calls: List[Dict[str, Any]] = []
    invalid: List[Dict[str, Any]] = []
    for index, match in enumerate(TOOL_CALL_RE.finditer(text)):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except Exception as exc:  # keep explicit diagnostics for malformed model output
            invalid.append({"index": index, "raw": raw, "error": f"JSON parse failed: {exc}"})
            continue
        if not isinstance(data, dict):
            invalid.append({"index": index, "raw": raw, "error": "tool call must be a JSON object"})
            continue
        name = data.get("name", "")
        arguments = data.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except Exception as exc:
                invalid.append({"index": index, "raw": raw, "error": f"arguments string is not JSON: {exc}"})
                continue
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            invalid.append({"index": index, "raw": raw, "error": "arguments must be an object"})
            continue
        if not isinstance(name, str) or not name:
            invalid.append({"index": index, "raw": raw, "error": "name must be a non-empty string"})
            continue
        calls.append(
            {
                "id": f"call_{index}",
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(arguments, ensure_ascii=False),
                },
                "parsed_arguments": arguments,
                "raw": raw,
            }
        )
    return calls, invalid


def parse_response(text: str) -> Dict[str, Any]:
    reasoning_content = None
    content = text
    think_match = THINK_RE.search(content)
    if think_match:
        reasoning_content = think_match.group(1).strip()
        content = THINK_RE.sub("", content, count=1).strip()
    elif "</think>" in content:
        before, after = content.split("</think>", 1)
        reasoning_content = before.strip()
        content = after.strip()

    tool_calls, invalid = parse_tool_calls(content)
    visible_content = TOOL_CALL_RE.sub("", content).strip() if tool_calls else content.strip()
    return {
        "content": visible_content,
        "reasoning_content": reasoning_content,
        "tool_calls": tool_calls,
        "invalid_tool_calls": invalid,
    }


def convert_unit(value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
    key = (from_unit.lower(), to_unit.lower())
    conversions = {
        ("km", "miles"): lambda x: x * 0.621371,
        ("kilometer", "mile"): lambda x: x * 0.621371,
        ("kilometers", "miles"): lambda x: x * 0.621371,
        ("miles", "km"): lambda x: x / 0.621371,
        ("m", "ft"): lambda x: x * 3.28084,
        ("ft", "m"): lambda x: x / 3.28084,
        ("kg", "pounds"): lambda x: x * 2.20462,
        ("pounds", "kg"): lambda x: x / 2.20462,
        ("celsius", "fahrenheit"): lambda x: x * 9 / 5 + 32,
        ("fahrenheit", "celsius"): lambda x: (x - 32) * 5 / 9,
    }
    if key not in conversions:
        return {"error": f"unsupported conversion: {from_unit} -> {to_unit}"}
    return {"result": round(conversions[key](value), 4), "from": f"{value} {from_unit}", "to_unit": to_unit}


def execute_tool(name: str, args: Dict[str, Any], rng: random.Random, fixed_time: str) -> Dict[str, Any]:
    try:
        if name == "calculate_math":
            return {"result": str(safe_calculate(str(args.get("expression", "0"))))}
        if name == "get_current_time":
            return {"datetime": fixed_time, "timezone": args.get("timezone", "Asia/Shanghai")}
        if name == "random_number":
            lo = int(args.get("min", 0))
            hi = int(args.get("max", 100))
            if hi < lo:
                lo, hi = hi, lo
            return {"result": rng.randint(lo, hi)}
        if name == "text_length":
            text = str(args.get("text", ""))
            return {"characters": len(text), "words": len(text.split())}
        if name == "unit_converter":
            return convert_unit(float(args.get("value", 0)), str(args.get("from_unit", "")), str(args.get("to_unit", "")))
        if name == "get_current_weather":
            unit = args.get("unit", "celsius")
            temp = "22°C" if unit != "fahrenheit" else "72°F"
            return {"city": args.get("location"), "temperature": temp, "humidity": "65%", "condition": "clear"}
        if name == "get_exchange_rate":
            return {"from": args.get("from_currency", "USD"), "to": args.get("to_currency", "CNY"), "rate": 7.15}
        if name == "translate_text":
            text = str(args.get("text", ""))
            target = str(args.get("target_language", args.get("target_lang", "english"))).lower()
            translated = "hello world" if "你好" in text and target in {"english", "en"} else f"[{target}] {text}"
            return {"translated": translated}
        return {"error": f"unknown tool: {name}"}
    except Exception as exc:
        return {"error": f"tool execution failed: {exc}"}


def execute_calls(calls: Iterable[Dict[str, Any]], seed: int, fixed_time: str) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    results = []
    for call in calls:
        name = call["function"]["name"]
        args = call.get("parsed_arguments") or json.loads(call["function"].get("arguments", "{}"))
        results.append({"id": call["id"], "name": name, "arguments": args, "result": execute_tool(name, args, rng, fixed_time)})
    return results


def read_input_text(args: argparse.Namespace) -> str:
    if args.from_file:
        return Path(args.from_file).read_text(encoding="utf-8")
    if args.text is not None:
        return args.text
    return DEFAULT_TEXT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse MiniMind <think> and <tool_call> output without loading a model.")
    parser.add_argument("--text", help="Assistant text to parse. Defaults to a deterministic calculator tool-call sample.")
    parser.add_argument("--from-file", help="Read assistant text from a UTF-8 file.")
    parser.add_argument("--execute", action="store_true", help="Execute parsed calls with deterministic mock tools.")
    parser.add_argument("--seed", type=int, default=1234, help="Seed for deterministic random_number mock tool. Default: 1234.")
    parser.add_argument("--fixed-time", default="2026-03-15 17:18:22", help="Fixed datetime returned by get_current_time.")
    parser.add_argument("--list-tools", action="store_true", help="Print bundled OpenAI-compatible mock tool schemas and exit.")
    parser.add_argument("--strict-invalid", action="store_true", help="Exit with status 2 if malformed tool calls are present.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON. Pretty text is used otherwise.")
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list_tools:
        print(dumps(TOOL_SPECS))
        return 0

    parsed = parse_response(read_input_text(args))
    if args.execute:
        parsed["executions"] = execute_calls(parsed["tool_calls"], seed=args.seed, fixed_time=args.fixed_time)

    if args.json:
        print(dumps(parsed))
    else:
        print("Content:", parsed["content"] or "<empty>")
        print("Reasoning:", parsed["reasoning_content"] if parsed["reasoning_content"] is not None else "<none>")
        print("Tool calls:", len(parsed["tool_calls"]))
        for call in parsed["tool_calls"]:
            print(f"- {call['id']} {call['function']['name']} args={call['function']['arguments']}")
        if parsed["invalid_tool_calls"]:
            print("Invalid tool calls:", file=sys.stderr)
            for item in parsed["invalid_tool_calls"]:
                print(f"- index={item['index']} error={item['error']} raw={item['raw']!r}", file=sys.stderr)
        for item in parsed.get("executions", []):
            print(f"Executed {item['name']}: {json.dumps(item['result'], ensure_ascii=False)}")

    if args.strict_invalid and parsed["invalid_tool_calls"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
