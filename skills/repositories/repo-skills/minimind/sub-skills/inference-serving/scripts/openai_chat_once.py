#!/usr/bin/env python3
"""
Send one non-interactive OpenAI-compatible chat request to a MiniMind server.

The helper supports MiniMind-specific thinking fields and OpenAI-style tools,
collects streaming deltas into one JSON summary, and never stores credentials or
conversation history.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def get_field(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    value = getattr(obj, key, default)
    if value is not None:
        return value
    extra = getattr(obj, "model_extra", None)
    if isinstance(extra, dict):
        return extra.get(key, default)
    return default


def to_plain(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, list):
        return [to_plain(item) for item in obj]
    if isinstance(obj, tuple):
        return [to_plain(item) for item in obj]
    if isinstance(obj, dict):
        return {str(k): to_plain(v) for k, v in obj.items() if v is not None}
    if hasattr(obj, "model_dump"):
        return obj.model_dump(exclude_none=True)
    return repr(obj)


def load_json_arg(path_or_json: Optional[str], label: str) -> Any:
    if not path_or_json:
        return None
    candidate = Path(path_or_json)
    if candidate.exists():
        text = candidate.read_text(encoding="utf-8")
    else:
        text = path_or_json
    try:
        return json.loads(text)
    except Exception as exc:
        raise SystemExit(f"Failed to parse {label} as JSON or JSON file: {exc}") from exc


def load_tools(path_or_json: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    data = load_json_arg(path_or_json, "tools")
    if data is None:
        return None
    if isinstance(data, dict) and "tools" in data:
        data = data["tools"]
    if not isinstance(data, list):
        raise SystemExit("Tools JSON must be a list or an object with a 'tools' list")
    return data


def normalize_tool_calls(tool_calls: Any) -> List[Dict[str, Any]]:
    plain = to_plain(tool_calls)
    if not plain:
        return []
    normalized: List[Dict[str, Any]] = []
    for index, tc in enumerate(plain):
        if not isinstance(tc, dict):
            normalized.append({"id": f"call_{index}", "type": "function", "function": {"name": "", "arguments": ""}, "raw": tc})
            continue
        fn = tc.get("function") or {}
        if not isinstance(fn, dict):
            fn = to_plain(fn) if isinstance(to_plain(fn), dict) else {}
        normalized.append(
            {
                "id": tc.get("id") or f"call_{index}",
                "type": tc.get("type") or "function",
                "function": {
                    "name": fn.get("name", ""),
                    "arguments": fn.get("arguments", ""),
                },
            }
        )
    return normalized


def accumulate_stream_tool_calls(acc: Dict[int, Dict[str, Any]], chunks: Iterable[Any]) -> None:
    for chunk in chunks or []:
        idx = get_field(chunk, "index")
        if idx is None:
            idx = len(acc)
        rec = acc.setdefault(int(idx), {"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
        chunk_id = get_field(chunk, "id") or ""
        if chunk_id:
            rec["id"] += chunk_id
        chunk_type = get_field(chunk, "type")
        if chunk_type:
            rec["type"] = chunk_type
        fn = get_field(chunk, "function")
        if fn:
            name = get_field(fn, "name") or ""
            arguments = get_field(fn, "arguments") or ""
            rec["function"]["name"] += name
            rec["function"]["arguments"] += arguments


def build_messages(args: argparse.Namespace) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": args.prompt})
    return messages


def build_extra_body(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    extra: Dict[str, Any] = {}
    user_extra = load_json_arg(args.extra_body_json, "extra body")
    if user_extra is not None:
        if not isinstance(user_extra, dict):
            raise SystemExit("--extra-body-json must decode to an object")
        extra.update(user_extra)
    if args.open_thinking:
        extra["open_thinking"] = True
        ctk = extra.get("chat_template_kwargs")
        if not isinstance(ctk, dict):
            ctk = {}
        ctk["open_thinking"] = True
        extra["chat_template_kwargs"] = ctk
    return extra or None


def request_once(args: argparse.Namespace) -> Dict[str, Any]:
    try:
        from openai import OpenAI
    except Exception as exc:
        return {"ok": False, "error": f"The openai package is required for this helper: {exc}"}

    tools = load_tools(args.tools_json)
    extra_body = build_extra_body(args)
    client = OpenAI(api_key=args.api_key, base_url=args.base_url, timeout=args.timeout)
    kwargs: Dict[str, Any] = {
        "model": args.model,
        "messages": build_messages(args),
        "stream": args.stream,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "top_p": args.top_p,
    }
    if tools:
        kwargs["tools"] = tools
    if extra_body:
        kwargs["extra_body"] = extra_body

    summary: Dict[str, Any] = {
        "ok": True,
        "request": {
            "base_url": args.base_url,
            "model": args.model,
            "stream": args.stream,
            "open_thinking": args.open_thinking,
            "tools_count": len(tools or []),
            "max_tokens": args.max_tokens,
            "temperature": args.temperature,
            "top_p": args.top_p,
        },
        "content": "",
        "reasoning_content": "",
        "tool_calls": [],
        "finish_reason": None,
    }

    try:
        response = client.chat.completions.create(**kwargs)
        if not args.stream:
            choices = get_field(response, "choices", []) or []
            if not choices:
                summary.update({"ok": False, "error": "response had no choices"})
                return summary
            choice = choices[0]
            message = get_field(choice, "message")
            summary["content"] = get_field(message, "content", "") or ""
            summary["reasoning_content"] = get_field(message, "reasoning_content", "") or ""
            summary["tool_calls"] = normalize_tool_calls(get_field(message, "tool_calls", []))
            summary["finish_reason"] = get_field(choice, "finish_reason")
            return summary

        content_parts: List[str] = []
        reasoning_parts: List[str] = []
        tool_call_acc: Dict[int, Dict[str, Any]] = {}
        finish_reason = None
        for chunk in response:
            choices = get_field(chunk, "choices", []) or []
            if not choices:
                continue
            choice = choices[0]
            finish_reason = get_field(choice, "finish_reason", finish_reason)
            delta = get_field(choice, "delta")
            reasoning = get_field(delta, "reasoning_content", "") or ""
            content = get_field(delta, "content", "") or ""
            if reasoning:
                reasoning_parts.append(reasoning)
                if args.echo_stream:
                    print(reasoning, end="", flush=True, file=sys.stderr)
            if content:
                content_parts.append(content)
                if args.echo_stream:
                    print(content, end="", flush=True, file=sys.stderr)
            accumulate_stream_tool_calls(tool_call_acc, get_field(delta, "tool_calls", []) or [])
        if args.echo_stream:
            print(file=sys.stderr)
        summary["content"] = "".join(content_parts)
        summary["reasoning_content"] = "".join(reasoning_parts)
        summary["tool_calls"] = [tool_call_acc[i] for i in sorted(tool_call_acc)]
        summary["finish_reason"] = finish_reason
        return summary
    except Exception as exc:
        summary.update({"ok": False, "error": str(exc)})
        return summary


def build_parser() -> argparse.ArgumentParser:
    default_base_url = os.environ.get("MINIMIND_OPENAI_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or "http://127.0.0.1:8998/v1"
    default_api_key = os.environ.get("MINIMIND_API_KEY") or os.environ.get("OPENAI_API_KEY") or "not-needed"
    default_model = os.environ.get("MINIMIND_MODEL") or "minimind"

    parser = argparse.ArgumentParser(description="Send one OpenAI-compatible MiniMind chat request and print a JSON summary.")
    parser.add_argument("--base-url", default=default_base_url, help="OpenAI-compatible base URL. Default: env MINIMIND_OPENAI_BASE_URL/OPENAI_BASE_URL or http://127.0.0.1:8998/v1")
    parser.add_argument("--api-key", default=default_api_key, help="API key or dummy value for local servers. Defaults to env MINIMIND_API_KEY/OPENAI_API_KEY or 'not-needed'.")
    parser.add_argument("--model", default=default_model, help="Model identifier sent in the request. Default: env MINIMIND_MODEL or minimind.")
    parser.add_argument("--prompt", default="Who are you?", help="Single user prompt to send.")
    parser.add_argument("--system", help="Optional system message.")
    parser.add_argument("--temperature", type=float, default=0.8, help="Sampling temperature. Default: 0.8.")
    parser.add_argument("--top-p", type=float, default=0.8, help="Nucleus sampling top_p. Default: 0.8.")
    parser.add_argument("--max-tokens", type=int, default=256, help="Maximum tokens to request. Default: 256.")
    stream_group = parser.add_mutually_exclusive_group()
    stream_group.add_argument("--stream", dest="stream", action="store_true", help="Use streaming responses.")
    stream_group.add_argument("--no-stream", dest="stream", action="store_false", help="Use non-streaming responses. This is the default.")
    parser.set_defaults(stream=False)
    parser.add_argument("--open-thinking", action="store_true", help="Enable MiniMind template-level thinking via extra_body.")
    parser.add_argument("--tools-json", help="Tool schema as a JSON file path or inline JSON list/object containing a tools list.")
    parser.add_argument("--extra-body-json", help="Additional OpenAI SDK extra_body object as JSON or JSON file.")
    parser.add_argument("--timeout", type=float, default=60.0, help="Client timeout in seconds. Default: 60.")
    parser.add_argument("--echo-stream", action="store_true", help="Echo streaming reasoning/content chunks to stderr while still printing final JSON to stdout.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    summary = request_once(args)
    print(dumps(summary))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
