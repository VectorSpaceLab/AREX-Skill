#!/usr/bin/env python3
"""Smoke-test MiniMind Agentic RL tool-call parsing, mock tools, gt hits, and rollout backend planning.

The helper is deterministic and offline by default. It does not load MiniMind,
Reward Models, or SGLang unless --probe-sglang is explicitly requested.

Examples:
  python scripts/reward_toolcall_smoke.py --text '<tool_call>{"name":"calculate_math","arguments":{"expression":"71**2"}}</tool_call> The answer is 5041.' --gt '["5041"]'
  python scripts/reward_toolcall_smoke.py --rollout-engine sglang --sglang-base-url http://localhost:8998
  python scripts/reward_toolcall_smoke.py --rollout-engine sglang --probe-sglang
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import operator
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

DEFAULT_TEXT = '<tool_call>{"name":"calculate_math","arguments":{"expression":"2+2"}}</tool_call> The answer is 4.'
DEFAULT_GT = '["4"]'

DEFAULT_TOOLS = [
    {"type": "function", "function": {"name": "calculate_math", "parameters": {"type": "object", "required": ["expression"]}}},
    {"type": "function", "function": {"name": "unit_converter", "parameters": {"type": "object", "required": ["value", "from_unit", "to_unit"]}}},
    {"type": "function", "function": {"name": "get_current_weather", "parameters": {"type": "object", "required": ["location"]}}},
    {"type": "function", "function": {"name": "get_current_time", "parameters": {"type": "object", "required": []}}},
    {"type": "function", "function": {"name": "get_exchange_rate", "parameters": {"type": "object", "required": ["from_currency", "to_currency"]}}},
    {"type": "function", "function": {"name": "translate_text", "parameters": {"type": "object", "required": ["text", "target_language"]}}},
]

MOCK_WEATHER = {"北京": ("28°C", "晴"), "Tokyo": ("12°C", "晴"), "New York": ("8°C", "多云")}
MOCK_RATES = {("USD", "CNY"): 7.21, ("EUR", "CNY"): 7.85, ("USD", "EUR"): 0.92}
MOCK_TRANSLATE = {("你好世界", "english"): "Hello World", ("Good morning", "chinese"): "早上好"}
UNIT_FACTORS = {("km", "miles"): 0.621371, ("miles", "km"): 1.60934, ("kg", "pounds"): 2.20462, ("pounds", "kg"): 0.453592}

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
}


@dataclass
class ParsedCall:
    name: str
    arguments: dict[str, Any]
    raw: str
    valid_json: bool = True
    error: str | None = None


def safe_eval_expr(expr: str) -> float:
    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](visit(node.operand))
        raise ValueError(f"unsupported expression element: {type(node).__name__}")
    normalized = expr.replace("^", "**").replace("×", "*").replace("÷", "/").replace("−", "-")
    return visit(ast.parse(normalized, mode="eval"))


def parse_calls(text: str) -> tuple[list[ParsedCall], list[str]]:
    errors: list[str] = []
    if text.count("<tool_call>") != text.count("</tool_call>"):
        errors.append("mismatched <tool_call> tag count")
    calls: list[ParsedCall] = []
    for match in re.finditer(r"<tool_call>(.*?)</tool_call>", text, flags=re.DOTALL):
        raw = match.group(1).strip()
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            calls.append(ParsedCall(name="", arguments={}, raw=raw, valid_json=False, error=exc.msg))
            errors.append(f"malformed tool_call JSON: {exc.msg}")
            continue
        name = obj.get("name", "") if isinstance(obj, dict) else ""
        arguments = obj.get("arguments", {}) if isinstance(obj, dict) else {}
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                errors.append(f"tool {name!r} arguments string is not JSON")
                arguments = {}
        if not isinstance(arguments, dict):
            errors.append(f"tool {name!r} arguments must be an object")
            arguments = {}
        calls.append(ParsedCall(name=name, arguments=arguments, raw=raw))
    return calls, errors


def tool_requirements(tools: list[dict[str, Any]]) -> dict[str, set[str]]:
    reqs: dict[str, set[str]] = {}
    for tool in tools:
        fn = tool.get("function", {}) if isinstance(tool, dict) else {}
        name = fn.get("name")
        params = fn.get("parameters", {}) if isinstance(fn, dict) else {}
        required = params.get("required", []) if isinstance(params, dict) else []
        if isinstance(name, str):
            reqs[name] = set(required or []) if isinstance(required, list) else set()
    return reqs


def execute_mock_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "calculate_math":
        value = safe_eval_expr(str(args.get("expression", "0")))
        result: int | float = int(value) if abs(value - int(value)) < 1e-12 else value
        return {"result": result}
    if name == "unit_converter":
        factor = UNIT_FACTORS.get((str(args.get("from_unit", "")).lower(), str(args.get("to_unit", "")).lower()), 1.0)
        return {"result": round(float(args.get("value", 0)) * factor, 4)}
    if name == "get_current_weather":
        temp, condition = MOCK_WEATHER.get(str(args.get("location", "")), ("22°C", "晴"))
        return {"temperature": temp, "condition": condition}
    if name == "get_current_time":
        return {"datetime": "2025-03-07 14:30:00", "timezone": args.get("timezone", "Asia/Shanghai")}
    if name == "get_exchange_rate":
        return {"rate": MOCK_RATES.get((args.get("from_currency"), args.get("to_currency")), 1.0)}
    if name == "translate_text":
        return {"translated_text": MOCK_TRANSLATE.get((args.get("text"), args.get("target_language")), str(args.get("text", "")))}
    raise ValueError(f"unknown tool: {name}")


def parse_json_list(text: str, label: str) -> list[Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label} must be valid JSON: {exc.msg}")
    if not isinstance(value, list):
        raise SystemExit(f"{label} must be a JSON list")
    return value


def final_answer_region(text: str) -> str:
    if "</tool_call>" in text:
        return text.rsplit("</tool_call>", 1)[-1]
    if "</think>" in text:
        return text.rsplit("</think>", 1)[-1]
    return text


def gt_hits(text: str, gt: list[Any]) -> list[Any]:
    region = final_answer_region(text)
    lowered = region.lower()
    numeric_text = region.replace(",", "")
    nums = [float(x) for x in re.findall(r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?![\w.])", numeric_text)]
    hits: list[Any] = []
    for target in gt:
        target_s = str(target).strip()
        if not target_s:
            continue
        if target_s.lower() in lowered:
            hits.append(target)
            continue
        target_num_s = target_s.replace(",", "")
        if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", target_num_s):
            target_num = float(target_num_s)
            if any(abs(target_num - n) < 1e-6 for n in nums):
                hits.append(target)
    return hits


def probe_sglang(base_url: str) -> tuple[bool, str]:
    url = base_url.rstrip("/") + "/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return 200 <= response.status < 300, f"HTTP {response.status} from {url}"
    except (urllib.error.URLError, TimeoutError) as exc:
        return False, f"probe failed for {url}: {exc}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke MiniMind Agentic RL tool-call and reward logic.")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="Assistant text containing optional <tool_call> blocks.")
    parser.add_argument("--gt", default=DEFAULT_GT, help="JSON list of scalar ground-truth targets.")
    parser.add_argument("--tools-json", default=json.dumps(DEFAULT_TOOLS, ensure_ascii=False), help="OpenAI-style tools JSON list.")
    parser.add_argument("--rollout-engine", choices=["torch", "sglang"], default="torch")
    parser.add_argument("--sglang-base-url", default="http://localhost:8998")
    parser.add_argument("--probe-sglang", action="store_true", help="Actually probe the SGLang /health endpoint.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    gt = parse_json_list(args.gt, "--gt")
    tools = parse_json_list(args.tools_json, "--tools-json")
    reqs = tool_requirements(tools)
    valid_names = set(reqs)

    calls, errors = parse_calls(args.text)
    executed: list[dict[str, Any]] = []
    valid_call_count = 0
    for call in calls:
        if not call.valid_json:
            continue
        if call.name not in valid_names:
            errors.append(f"unknown tool name: {call.name!r}")
            continue
        missing = sorted(reqs[call.name] - set(call.arguments))
        if missing:
            errors.append(f"tool {call.name!r} missing required arguments: {missing}")
            continue
        try:
            result = execute_mock_tool(call.name, call.arguments)
        except Exception as exc:  # noqa: BLE001 - surface safe smoke failures
            errors.append(f"tool {call.name!r} execution failed: {exc}")
            continue
        valid_call_count += 1
        executed.append({"name": call.name, "arguments": call.arguments, "result": result})

    hits = gt_hits(args.text, gt)
    warnings: list[str] = []
    if gt and not hits:
        errors.append("no ground-truth targets were detected in final answer text")
    if calls and valid_call_count != len(gt):
        warnings.append(f"valid tool call count {valid_call_count} differs from gt count {len(gt)}")

    rollout_status = {"engine": args.rollout_engine, "checked": "dry"}
    if args.rollout_engine == "sglang":
        if args.probe_sglang:
            ok, msg = probe_sglang(args.sglang_base_url)
            rollout_status = {"engine": "sglang", "checked": "health", "ok": ok, "message": msg}
            if not ok:
                errors.append(msg)
        else:
            rollout_status["message"] = "SGLang selected but not contacted; add --probe-sglang to hit /health."
    else:
        rollout_status["message"] = "Torch rollout requires no service probe for this smoke."

    score = max(min(2.5 * (len(hits) / max(len(gt), 1)) - 0.5 * len(errors), 3.0), -3.0)
    summary = {
        "ok": not errors,
        "calls": [call.__dict__ for call in calls],
        "executed": executed,
        "gt": gt,
        "gt_hits": hits,
        "warnings": warnings,
        "errors": errors,
        "rollout": rollout_status,
        "score_like_signal": score,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"calls={len(calls)} valid_calls={valid_call_count} gt_hits={len(hits)}/{len(gt)} score_like={score:.3f}")
        for item in executed:
            print(f"tool={item['name']} result={json.dumps(item['result'], ensure_ascii=False)}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        for error in errors:
            print(f"ERROR: {error}")
        print(f"rollout={rollout_status['engine']} check={rollout_status.get('checked')} {rollout_status.get('message', '')}")
        print("status=OK" if not errors else "status=FAILED")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
