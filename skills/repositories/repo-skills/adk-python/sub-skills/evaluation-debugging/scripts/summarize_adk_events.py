#!/usr/bin/env python3
"""Summarize ADK session, event, or trace JSON without exposing long values.

Reads JSON from --input or stdin and prints a concise event/span summary with
truncated text, tool arguments, tool responses, outputs, and actions. The script
is read-only, performs no network calls, and writes only to stdout/stderr.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

DEFAULT_MAX_TEXT = 180
SECRET_KEY_HINTS = (
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "password",
    "secret",
    "token",
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|token|password|secret)(\s*[:=]\s*)([^\s,;]+)"),
)


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
      description=(
          "Summarize ADK session/event JSON from stdin or --input. "
          "Long values are truncated and common secret-looking keys are redacted."
      )
  )
  parser.add_argument(
      "--input",
      "-i",
      type=Path,
      help="Path to a JSON file. If omitted, JSON is read from stdin.",
  )
  parser.add_argument(
      "--max-text",
      type=int,
      default=DEFAULT_MAX_TEXT,
      help=f"Maximum characters per displayed value (default: {DEFAULT_MAX_TEXT}).",
  )
  parser.add_argument(
      "--limit",
      type=int,
      default=0,
      help="Maximum number of events/spans to print; 0 means no limit.",
  )
  return parser.parse_args()


def load_json(input_path: Path | None) -> Any:
  try:
    if input_path:
      return json.loads(input_path.read_text(encoding="utf-8"))
    return json.load(sys.stdin)
  except FileNotFoundError as exc:
    raise SystemExit(f"Input file not found: {exc.filename}") from exc
  except json.JSONDecodeError as exc:
    raise SystemExit(f"Invalid JSON: {exc}") from exc


def redact_string(value: str) -> str:
  for pattern in SECRET_VALUE_PATTERNS:
    if "bearer" in pattern.pattern.lower():
      value = pattern.sub(r"\1<redacted>", value)
    else:
      value = pattern.sub(r"\1\2<redacted>", value)
  return value


def truncate(value: Any, max_text: int) -> str:
  if value is None:
    return ""
  if not isinstance(value, str):
    value = json.dumps(redact(value), ensure_ascii=False, sort_keys=True)
  value = redact_string(value)
  value = " ".join(value.split())
  if len(value) <= max_text:
    return value
  return value[: max_text - 1] + "…"


def is_secret_key(key: str) -> bool:
  lowered = key.lower().replace("-", "_")
  return any(hint in lowered for hint in SECRET_KEY_HINTS)


def redact(value: Any) -> Any:
  if isinstance(value, Mapping):
    redacted = {}
    for key, item in value.items():
      key_text = str(key)
      redacted[key_text] = "<redacted>" if is_secret_key(key_text) else redact(item)
    return redacted
  if isinstance(value, list):
    return [redact(item) for item in value]
  if isinstance(value, str):
    return redact_string(value)
  return value


def first_present(mapping: Mapping[str, Any], *keys: str) -> Any:
  for key in keys:
    if key in mapping:
      return mapping[key]
  return None


def as_list(value: Any) -> list[Any]:
  if value is None:
    return []
  if isinstance(value, list):
    return value
  return [value]


def find_events(data: Any) -> list[Mapping[str, Any]]:
  if isinstance(data, list):
    return [item for item in data if isinstance(item, Mapping)]
  if not isinstance(data, Mapping):
    return []

  for key in ("events", "invocation_events", "invocationEvents"):
    events = data.get(key)
    if isinstance(events, list):
      return [item for item in events if isinstance(item, Mapping)]

  for key in ("session", "data"):
    nested = data.get(key)
    events = find_events(nested)
    if events:
      return events

  if any(key in data for key in ("author", "content", "output", "actions", "nodeInfo")):
    return [data]
  return []


def find_spans(data: Any) -> list[Mapping[str, Any]]:
  if isinstance(data, list):
    return [item for item in data if isinstance(item, Mapping) and "name" in item]
  if not isinstance(data, Mapping):
    return []
  for key in ("spans", "trace", "traces"):
    spans = data.get(key)
    if isinstance(spans, list):
      return [item for item in spans if isinstance(item, Mapping)]
  if "name" in data and ("attributes" in data or "span_id" in data or "spanId" in data):
    return [data]
  return []


def iter_content_parts(event: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
  content = event.get("content")
  if not isinstance(content, Mapping):
    return []
  parts = content.get("parts")
  if not isinstance(parts, list):
    return []
  return [part for part in parts if isinstance(part, Mapping)]


def summarize_part(part: Mapping[str, Any], max_text: int) -> list[str]:
  lines = []
  text = part.get("text")
  if text:
    lines.append(f"text: {truncate(text, max_text)}")

  function_call = first_present(part, "functionCall", "function_call")
  if isinstance(function_call, Mapping):
    name = first_present(function_call, "name") or "<unnamed>"
    args = first_present(function_call, "args") or {}
    call_id = first_present(function_call, "id")
    suffix = f" id={call_id}" if call_id else ""
    lines.append(f"call: {name}{suffix} args={truncate(args, max_text)}")

  function_response = first_present(part, "functionResponse", "function_response")
  if isinstance(function_response, Mapping):
    name = first_present(function_response, "name") or "<unnamed>"
    response = first_present(function_response, "response") or {}
    response_id = first_present(function_response, "id")
    suffix = f" id={response_id}" if response_id else ""
    lines.append(f"response: {name}{suffix} value={truncate(response, max_text)}")

  executable_code = first_present(part, "executableCode", "executable_code")
  if isinstance(executable_code, Mapping):
    language = first_present(executable_code, "language") or "code"
    code = first_present(executable_code, "code") or ""
    lines.append(f"code[{language}]: {truncate(code, max_text)}")

  code_result = first_present(part, "codeExecutionResult", "code_execution_result")
  if isinstance(code_result, Mapping):
    output = first_present(code_result, "output") or code_result
    lines.append(f"code-result: {truncate(output, max_text)}")

  inline_data = first_present(part, "inlineData", "inline_data")
  if isinstance(inline_data, Mapping):
    mime_type = first_present(inline_data, "mimeType", "mime_type") or "data"
    lines.append(f"inline-data: {mime_type}")

  file_data = first_present(part, "fileData", "file_data")
  if isinstance(file_data, Mapping):
    uri = first_present(file_data, "fileUri", "file_uri") or "file"
    lines.append(f"file: {truncate(uri, max_text)}")

  return lines


def node_path(event: Mapping[str, Any]) -> str:
  node_info = first_present(event, "nodeInfo", "node_info")
  if isinstance(node_info, Mapping):
    path = node_info.get("path")
    if path:
      return str(path)
  branch = event.get("branch")
  return str(branch) if branch else ""


def action_summary(actions: Any, max_text: int) -> str:
  if not isinstance(actions, Mapping):
    return ""
  compact = {}
  for key, value in actions.items():
    if value in (None, {}, [], ""):
      continue
    compact[str(key)] = value
  return truncate(compact, max_text) if compact else ""


def output_summary(event: Mapping[str, Any], max_text: int) -> str:
  output = event.get("output")
  if output not in (None, "", {}, []):
    return truncate(output, max_text)
  return ""


def summarize_events(events: Sequence[Mapping[str, Any]], max_text: int, limit: int) -> None:
  count = len(events) if limit <= 0 else min(len(events), limit)
  print(f"Events: {len(events)} total, showing {count}")
  for index, event in enumerate(events[:count], start=1):
    event_id = first_present(event, "id", "eventId", "event_id") or ""
    invocation_id = first_present(event, "invocationId", "invocation_id") or ""
    author = event.get("author") or "<unknown>"
    path = node_path(event)
    header_bits = [f"[{index}]", f"author={author}"]
    if path:
      header_bits.append(f"path={path}")
    if event_id:
      header_bits.append(f"event={event_id}")
    if invocation_id:
      header_bits.append(f"invocation={invocation_id}")
    print(" ".join(header_bits))

    part_lines = []
    for part in iter_content_parts(event):
      part_lines.extend(summarize_part(part, max_text))
    for line in part_lines:
      print(f"  - {line}")

    output = output_summary(event, max_text)
    if output:
      print(f"  - output: {output}")

    actions = action_summary(event.get("actions"), max_text)
    if actions:
      print(f"  - actions: {actions}")

    if not part_lines and not output and not actions:
      print("  - no content/output/actions")


def summarize_spans(spans: Sequence[Mapping[str, Any]], max_text: int, limit: int) -> None:
  count = len(spans) if limit <= 0 else min(len(spans), limit)
  print(f"Spans: {len(spans)} total, showing {count}")
  for index, span in enumerate(spans[:count], start=1):
    attributes = span.get("attributes") if isinstance(span.get("attributes"), Mapping) else {}
    name = span.get("name") or "<unnamed>"
    event_id = attributes.get("gcp.vertex.agent.event_id") if isinstance(attributes, Mapping) else None
    span_id = first_present(span, "span_id", "spanId")
    parent_id = first_present(span, "parent_span_id", "parentSpanId")
    header_bits = [f"[{index}]", f"span={name}"]
    if span_id:
      header_bits.append(f"span_id={span_id}")
    if parent_id:
      header_bits.append(f"parent={parent_id}")
    if event_id:
      header_bits.append(f"event={event_id}")
    print(" ".join(header_bits))

    if isinstance(attributes, Mapping):
      for key in (
          "gen_ai.request.model",
          "gen_ai.response.finish_reasons",
          "gen_ai.usage.input_tokens",
          "gen_ai.usage.output_tokens",
          "gcp.vertex.agent.llm_request",
          "gcp.vertex.agent.llm_response",
          "gcp.vertex.agent.tool_call_args",
          "gcp.vertex.agent.tool_response",
      ):
        value = attributes.get(key)
        if value not in (None, "", {}, []):
          print(f"  - {key}: {truncate(value, max_text)}")


def main() -> int:
  args = parse_args()
  if args.max_text < 20:
    raise SystemExit("--max-text must be at least 20")
  data = load_json(args.input)

  events = find_events(data)
  spans = find_spans(data)

  if events:
    summarize_events(events, args.max_text, args.limit)
  if spans:
    if events:
      print()
    summarize_spans(spans, args.max_text, args.limit)
  if not events and not spans:
    print("No ADK events or trace spans found in input.", file=sys.stderr)
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
