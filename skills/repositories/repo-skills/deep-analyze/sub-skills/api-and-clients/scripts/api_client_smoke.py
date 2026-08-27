#!/usr/bin/env python3
"""Requests-based smoke test for the DeepAnalyze API server."""

from __future__ import annotations

import argparse
import json
import mimetypes
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Exercise the DeepAnalyze API server with requests.")
    parser.add_argument("--api-base", default="http://127.0.0.1:8200", help="Root URL of the DeepAnalyze API server.")
    parser.add_argument("--model", default="DeepAnalyze-8B", help="Model name sent to chat completions.")
    parser.add_argument("--purpose", default="file-extract", help="Purpose used when uploading files.")
    parser.add_argument("--file", dest="files", action="append", default=[], help="Input file path to upload. May be repeated.")
    parser.add_argument("--message", default="Analyze the uploaded files and summarize the important structure.", help="First-turn user message.")
    parser.add_argument("--followup", default="Continue in the same thread and mention whether the thread persisted.", help="Second-turn user message.")
    parser.add_argument("--temperature", type=float, default=0.4, help="Sampling temperature.")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds.")
    parser.add_argument("--stream", action=argparse.BooleanOptionalAction, default=True, help="Use streaming for the second chat request.")
    parser.add_argument("--cleanup", action="store_true", help="Delete uploaded files at the end, even for user-supplied inputs.")
    return parser


def _preview(text: str, limit: int = 240) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit] + "..."


def _api_root(api_base: str) -> str:
    return api_base.rstrip("/") + "/v1"


def _guess_content_type(path: Path) -> str:
    return mimetypes.guess_type(str(path))[0] or "application/octet-stream"


def _build_default_inputs() -> Tuple[List[Path], Optional[tempfile.TemporaryDirectory[str]], bool]:
    temp_dir = tempfile.TemporaryDirectory(prefix="deepanalyze-api-smoke-")
    root = Path(temp_dir.name)
    csv_path = root / "smoke_a.csv"
    txt_path = root / "smoke_b.txt"
    csv_path.write_text(
        "dept,treatment,success\n"
        "A,1,1\n"
        "A,0,0\n"
        "B,1,1\n"
        "B,0,0\n",
        encoding="utf-8",
    )
    txt_path.write_text(
        "This second file validates multi-file attachments and thread persistence.\n",
        encoding="utf-8",
    )
    return [csv_path, txt_path], temp_dir, True


def _prepare_inputs(file_args: List[str]) -> Tuple[List[Path], Optional[tempfile.TemporaryDirectory[str]], bool]:
    if not file_args:
        return _build_default_inputs()
    paths = [Path(item).expanduser().resolve() for item in file_args]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit(f"Input file(s) not found: {', '.join(missing)}")
    return paths, None, False


def _iter_sse_payloads(response: Any):
    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line or not raw_line.startswith("data: "):
            continue
        payload = raw_line[6:]
        if payload == "[DONE]":
            break
        yield json.loads(payload)


def _upload_file(session: Any, api_root: str, path: Path, purpose: str, timeout: float) -> Dict[str, Any]:
    with path.open("rb") as handle:
        response = session.post(
            f"{api_root}/files",
            files={"file": (path.name, handle, _guess_content_type(path))},
            data={"purpose": purpose},
            timeout=timeout,
        )
    response.raise_for_status()
    return response.json()


def _download_bytes(session: Any, api_root: str, file_id: str, timeout: float) -> bytes:
    response = session.get(f"{api_root}/files/{file_id}/content", timeout=timeout)
    response.raise_for_status()
    return response.content


def _flatten_generated_files(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []
    if isinstance(payload.get("generated_files"), list):
        files.extend([item for item in payload["generated_files"] if isinstance(item, dict)])
    choices = payload.get("choices") or []
    if choices:
        choice0 = choices[0] or {}
        message = choice0.get("message") or {}
        delta = choice0.get("delta") or {}
        if isinstance(message.get("files"), list):
            files.extend([item for item in message["files"] if isinstance(item, dict)])
        if isinstance(delta.get("files"), list):
            files.extend([item for item in delta["files"] if isinstance(item, dict)])
    return files


def _require_generated_files(payload: Dict[str, Any], label: str) -> List[Dict[str, Any]]:
    files = _flatten_generated_files(payload)
    if not files:
        raise SystemExit(f"{label} did not return any generated files")
    return files


def _chat_json(session: Any, api_root: str, payload: Dict[str, Any], timeout: float, stream: bool):
    if stream:
        response = session.post(
            f"{api_root}/chat/completions",
            json=payload,
            stream=True,
            timeout=(timeout, None),
        )
    else:
        response = session.post(
            f"{api_root}/chat/completions",
            json=payload,
            timeout=timeout,
        )
    response.raise_for_status()
    return response


def main() -> int:
    args = build_parser().parse_args()
    try:
        import requests
    except Exception as exc:  # pragma: no cover - dependency issue is user-facing
        raise SystemExit(f"requests is required: {exc}") from exc

    api_root = _api_root(args.api_base)
    api_base_root = args.api_base.rstrip("/")
    session = requests.Session()
    local_files, temp_dir, auto_generated = _prepare_inputs(args.files)
    uploaded: List[Tuple[Path, str]] = []

    try:
        health = session.get(f"{api_base_root}/health", timeout=args.timeout)
        health.raise_for_status()
        print(f"Health: {health.json().get('status')}")

        models = session.get(f"{api_root}/models", timeout=args.timeout)
        models.raise_for_status()
        model_ids = [item.get("id") for item in models.json().get("data", []) if isinstance(item, dict) and item.get("id")]
        print("Models:", ", ".join(model_ids) or "<empty>")

        for path in local_files:
            meta = _upload_file(session, api_root, path, args.purpose, args.timeout)
            uploaded.append((path, meta["id"]))
            print(f"Uploaded {path.name} -> {meta['id']}")

            retrieved = session.get(f"{api_root}/files/{meta['id']}", timeout=args.timeout)
            retrieved.raise_for_status()
            retrieved_json = retrieved.json()
            if retrieved_json.get("filename") != path.name:
                raise SystemExit(f"Metadata filename mismatch for {path.name}")

            downloaded = _download_bytes(session, api_root, meta["id"], args.timeout)
            if downloaded != path.read_bytes():
                raise SystemExit(f"Downloaded content mismatch for {path.name}")

        listed = session.get(f"{api_root}/files", timeout=args.timeout)
        listed.raise_for_status()
        listed_ids = {item.get("id") for item in listed.json().get("data", []) if isinstance(item, dict)}
        missing_ids = [file_id for _, file_id in uploaded if file_id not in listed_ids]
        if missing_ids:
            raise SystemExit(f"Uploaded file id(s) missing from list endpoint: {', '.join(missing_ids)}")

        file_ids = [file_id for _, file_id in uploaded]
        first_payload = {
            "model": args.model,
            "messages": [{"role": "user", "content": args.message, "file_ids": file_ids}],
            "temperature": args.temperature,
            "stream": False,
        }
        first_response = _chat_json(session, api_root, first_payload, args.timeout, stream=False)
        first_result = first_response.json()
        first_message = first_result["choices"][0]["message"]
        thread_id = first_message.get("thread_id")
        if not thread_id:
            raise SystemExit("First chat reply did not return a thread_id")
        first_text = str(first_message.get("content", ""))
        first_files = _require_generated_files(first_result, "First chat reply")
        print("First reply preview:")
        print(_preview(first_text))
        print(f"Thread ID: {thread_id}")
        print(f"Generated files in first reply: {len(first_files)}")

        history = [
            {"role": "user", "content": args.message, "file_ids": file_ids},
            {"role": "assistant", "content": first_text},
            {"role": "user", "content": args.followup, "file_ids": file_ids, "thread_id": thread_id},
        ]

        if args.stream:
            stream_payload = {
                "model": args.model,
                "messages": history,
                "temperature": args.temperature,
                "stream": True,
            }
            stream_response = _chat_json(session, api_root, stream_payload, args.timeout, stream=True)
            try:
                stream_text = ""
                stream_thread_id = None
                stream_files: List[Dict[str, Any]] = []
                print("Streaming second reply:")
                for chunk in _iter_sse_payloads(stream_response):
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {}) or {}
                    content = delta.get("content")
                    if content:
                        stream_text += content
                        print(content, end="", flush=True)
                    if delta.get("thread_id"):
                        stream_thread_id = delta["thread_id"]
                    if isinstance(delta.get("files"), list):
                        stream_files.extend([item for item in delta["files"] if isinstance(item, dict)])
                    if isinstance(chunk.get("generated_files"), list):
                        stream_files.extend([item for item in chunk["generated_files"] if isinstance(item, dict)])
                print()
                if not stream_text.strip():
                    raise SystemExit("Streaming reply was empty")
                if stream_thread_id and stream_thread_id != thread_id:
                    raise SystemExit("Streaming reply returned a different thread_id")
                if not stream_files:
                    raise SystemExit("Streaming reply did not return any generated files")
                print(f"Streaming thread ID: {stream_thread_id or thread_id}")
                print(f"Streaming generated files: {len(stream_files)}")
            finally:
                stream_response.close()
        else:
            second_payload = {
                "model": args.model,
                "messages": history,
                "temperature": args.temperature,
                "stream": False,
            }
            second_response = _chat_json(session, api_root, second_payload, args.timeout, stream=False)
            second_result = second_response.json()
            second_message = second_result["choices"][0]["message"]
            second_thread_id = second_message.get("thread_id")
            second_text = str(second_message.get("content", ""))
            second_files = _require_generated_files(second_result, "Second chat reply")
            print("Second reply preview:")
            print(_preview(second_text))
            print(f"Second thread ID: {second_thread_id}")
            print(f"Second generated files: {len(second_files)}")
            if second_thread_id and second_thread_id != thread_id:
                raise SystemExit("Second reply returned a different thread_id")

        cleanup_remote = args.cleanup or auto_generated
        if cleanup_remote:
            for _, file_id in uploaded:
                delete_response = session.delete(f"{api_root}/files/{file_id}", timeout=args.timeout)
                delete_response.raise_for_status()
                print(f"Deleted uploaded file: {file_id}")
        else:
            print("Uploaded files were kept on the server. Pass --cleanup to delete them.")

        print("Requests smoke passed.")
        return 0
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
