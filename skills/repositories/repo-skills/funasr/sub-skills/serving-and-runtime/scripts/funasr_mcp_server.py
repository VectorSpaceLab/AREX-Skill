#!/usr/bin/env python3
"""Small MCP stdio helper for local FunASR transcription.

The helper exposes one tool, transcribe_audio, and keeps stdout reserved for
JSON-RPC traffic so it can be used by agent tooling.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


DEFAULT_MODEL = os.getenv("FUNASR_MODEL", "iic/SenseVoiceSmall")
DEFAULT_DEVICE = os.getenv("FUNASR_DEVICE", "cpu")
DEFAULT_LANGUAGE = os.getenv("FUNASR_LANGUAGE", "auto")
SUPPORTED_LANGUAGES = ("auto", "zh", "yue", "en", "ja", "ko")

ARGS = argparse.Namespace(
    model=DEFAULT_MODEL,
    device=DEFAULT_DEVICE,
    language=DEFAULT_LANGUAGE,
)
MODEL_CACHE = None


def get_server_version() -> str:
    try:
        return version("funasr")
    except PackageNotFoundError:
        return "unknown"


def send_json(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def send_result(request_id, result: dict) -> None:
    send_json({"jsonrpc": "2.0", "id": request_id, "result": result})


def send_error(request_id, code: int, message: str) -> None:
    send_json({
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    })


def send_tool_error(request_id, message: str) -> None:
    send_result(
        request_id,
        {
            "content": [{"type": "text", "text": f"Error: {message}"}],
            "isError": True,
        },
    )


def get_model():
    global MODEL_CACHE
    if MODEL_CACHE is not None:
        return MODEL_CACHE

    try:
        from funasr import AutoModel
    except ImportError as exc:
        raise RuntimeError(
            "FunASR is not installed. Install the package and its runtime dependencies first."
        ) from exc

    MODEL_CACHE = AutoModel(
        model=ARGS.model,
        vad_model="fsmn-vad",
        vad_kwargs={"max_single_segment_time": 30000},
        device=ARGS.device,
        disable_update=True,
    )
    return MODEL_CACHE


def transcribe(audio_path: str, language: str) -> dict:
    model = get_model()
    result = model.generate(input=audio_path, batch_size=1, language=language)
    first = result[0] if result else {}
    text = re.sub(r"<\|[^|]*\|>", "", first.get("text", "")).strip()

    response = {"text": text}
    if "sentence_info" in first:
        segments = []
        for seg in first["sentence_info"]:
            segments.append(
                {
                    "text": seg.get("text") or seg.get("sentence") or "",
                    "start": float(seg.get("start", 0)) / 1000.0,
                    "end": float(seg.get("end", 0)) / 1000.0,
                    "speaker": seg.get("spk"),
                }
            )
        if segments:
            response["segments"] = segments
    return response


def render_transcription(result: dict) -> str:
    text = result.get("text", "")
    lines = [f"Transcription: {text}"]
    segments = result.get("segments") or []
    if segments:
        lines.append("")
        lines.append("Segments:")
        for segment in segments:
            speaker = (
                f" [Speaker {segment['speaker']}]"
                if segment.get("speaker") is not None
                else ""
            )
            lines.append(
                f"  [{segment['start']:.1f}s - {segment['end']:.1f}s]{speaker} {segment['text']}"
            )
    return "\n".join(lines)


def normalize_language(value: str | None) -> str:
    language = (value or DEFAULT_LANGUAGE or "auto").strip()
    if language not in SUPPORTED_LANGUAGES:
        supported = ", ".join(SUPPORTED_LANGUAGES)
        raise ValueError(f"unsupported language '{language}'; choose one of: {supported}")
    return language


def handle_initialize(request_id) -> None:
    send_result(
        request_id,
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "funasr", "version": get_server_version()},
        },
    )


def handle_tools_list(request_id) -> None:
    send_result(
        request_id,
        {
            "tools": [
                {
                    "name": "transcribe_audio",
                    "description": (
                        "Transcribe one existing local audio file with FunASR. "
                        "Use this tool when the user provides a file path that the "
                        "MCP helper can see and wants speech converted to text. "
                        "Do not use it for URLs, live microphone streams, or files "
                        "that are not mounted into the helper process."
                    ),
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "audio_path": {
                                "type": "string",
                                "description": (
                                    "Existing local audio file path visible to the helper."
                                ),
                            },
                            "language": {
                                "type": "string",
                                "description": (
                                    "Optional language hint. Use auto to let the backend "
                                    "detect the language, or provide zh, yue, en, ja, or ko."
                                ),
                                "enum": list(SUPPORTED_LANGUAGES),
                                "default": DEFAULT_LANGUAGE,
                            },
                        },
                        "required": ["audio_path"],
                    },
                }
            ]
        },
    )


def handle_transcribe_audio(request_id, args: dict) -> None:
    audio_path = args.get("audio_path")
    language = args.get("language", DEFAULT_LANGUAGE)

    if not isinstance(audio_path, str) or not audio_path.strip():
        send_tool_error(request_id, "audio_path is required")
        return

    try:
        language = normalize_language(language)
    except ValueError as exc:
        send_tool_error(request_id, str(exc))
        return

    expanded = Path(audio_path).expanduser()
    if not expanded.is_file():
        send_tool_error(request_id, f"file not found: {expanded}")
        return

    try:
        result = transcribe(str(expanded), language)
    except Exception as exc:
        send_tool_error(request_id, f"transcription failed: {exc}")
        return

    send_result(request_id, {"content": [{"type": "text", "text": render_transcription(result)}]})


def handle_request(request: dict) -> None:
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params") or {}

    if method == "initialize":
        handle_initialize(request_id)
        return

    if method == "tools/list":
        handle_tools_list(request_id)
        return

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if tool_name == "transcribe_audio":
            handle_transcribe_audio(request_id, arguments)
        else:
            send_tool_error(request_id, f"unknown tool: {tool_name}")
        return

    if method == "notifications/initialized":
        return

    if request_id is not None:
        send_error(request_id, -32601, f"Unknown method: {method}")


def main() -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"Ignoring non-JSON input: {exc}", file=sys.stderr)
            continue

        try:
            handle_request(request)
        except Exception as exc:
            request_id = request.get("id") if isinstance(request, dict) else None
            if request_id is not None:
                send_tool_error(request_id, f"internal helper error: {exc}")
            else:
                print(f"MCP helper error: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FunASR MCP stdio helper")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name or local model path")
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="Device passed to AutoModel")
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help="Default language hint for transcribe_audio",
    )
    ARGS = parser.parse_args()
    raise SystemExit(main())
