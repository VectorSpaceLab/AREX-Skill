#!/usr/bin/env python3
"""OpenAI-client smoke test for the DeepAnalyze API server."""

from __future__ import annotations

import argparse
import mimetypes
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Exercise the DeepAnalyze API server with the OpenAI client.")
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
    temp_dir = tempfile.TemporaryDirectory(prefix="deepanalyze-openai-smoke-")
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


def _content_to_bytes(content_obj: Any) -> bytes:
    if isinstance(content_obj, (bytes, bytearray)):
        return bytes(content_obj)
    if hasattr(content_obj, "read"):
        data = content_obj.read()
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8")
    if hasattr(content_obj, "text"):
        text = content_obj.text
        if isinstance(text, bytes):
            return text
        return str(text).encode("utf-8")
    return str(content_obj).encode("utf-8")


def _flatten_generated_files(message: Any, response: Any) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []
    if hasattr(message, "files") and message.files:
        files.extend([item for item in message.files if isinstance(item, dict)])
    if hasattr(response, "generated_files") and response.generated_files:
        files.extend([item for item in response.generated_files if isinstance(item, dict)])
    if hasattr(message, "delta") and getattr(message.delta, "files", None):
        files.extend([item for item in message.delta.files if isinstance(item, dict)])
    return files


def _require_generated_files(message: Any, response: Any, label: str) -> List[Dict[str, Any]]:
    files = _flatten_generated_files(message, response)
    if not files:
        raise SystemExit(f"{label} did not return any generated files")
    return files


def _prepare_client(api_base: str, timeout: float):
    try:
        import openai
    except Exception as exc:  # pragma: no cover - dependency issue is user-facing
        raise SystemExit(f"openai is required: {exc}") from exc
    return openai.OpenAI(base_url=_api_root(api_base), api_key="dummy", timeout=timeout)


def _upload_file(client: Any, path: Path, purpose: str):
    with path.open("rb") as handle:
        return client.files.create(file=handle, purpose=purpose)


def _retrieve_metadata(client: Any, file_id: str):
    retriever = getattr(client.files, "retrieve", None)
    if retriever is not None:
        return retriever(file_id)
    files_page = client.files.list()
    for item in files_page.data:
        if getattr(item, "id", None) == file_id:
            return item
    raise RuntimeError(f"Could not retrieve metadata for {file_id}")


def main() -> int:
    args = build_parser().parse_args()
    client = _prepare_client(args.api_base, args.timeout)
    local_files, temp_dir, auto_generated = _prepare_inputs(args.files)
    uploaded: List[Tuple[Path, str]] = []

    try:
        models = client.models.list()
        model_ids = [item.id for item in getattr(models, "data", [])]
        print(f"Models: {', '.join(model_ids) or '<empty>'}")

        for path in local_files:
            file_obj = _upload_file(client, path, args.purpose)
            uploaded.append((path, file_obj.id))
            print(f"Uploaded {path.name} -> {file_obj.id}")

            metadata = _retrieve_metadata(client, file_obj.id)
            if getattr(metadata, "filename", None) != path.name:
                raise SystemExit(f"Metadata filename mismatch for {path.name}")

            downloaded = _content_to_bytes(client.files.content(file_obj.id))
            if downloaded != path.read_bytes():
                raise SystemExit(f"Downloaded content mismatch for {path.name}")

        listed = client.files.list()
        listed_ids = {getattr(item, "id", None) for item in getattr(listed, "data", [])}
        missing_ids = [file_id for _, file_id in uploaded if file_id not in listed_ids]
        if missing_ids:
            raise SystemExit(f"Uploaded file id(s) missing from list endpoint: {', '.join(missing_ids)}")

        file_ids = [file_id for _, file_id in uploaded]
        first_messages = [{"role": "user", "content": args.message, "file_ids": file_ids}]
        first_response = client.chat.completions.create(model=args.model, messages=first_messages, temperature=args.temperature)
        first_message = first_response.choices[0].message
        thread_id = getattr(first_message, "thread_id", None)
        if not thread_id:
            raise SystemExit("First chat reply did not return a thread_id")
        first_text = str(first_message.content or "")
        first_files = _require_generated_files(first_message, first_response, "First chat reply")
        print("First reply preview:")
        print(_preview(first_text))
        print(f"Thread ID: {thread_id}")
        print(f"Generated files in first reply: {len(first_files)}")

        messages = [
            {"role": "user", "content": args.message, "file_ids": file_ids},
            {"role": "assistant", "content": first_text},
            {"role": "user", "content": args.followup, "file_ids": file_ids, "thread_id": thread_id},
        ]

        if args.stream:
            stream = client.chat.completions.create(model=args.model, messages=messages, temperature=args.temperature, stream=True)
            stream_text = ""
            stream_thread_id = None
            stream_files: List[Dict[str, Any]] = []
            print("Streaming second reply:")
            for chunk in stream:
                if chunk.choices and getattr(chunk.choices[0].delta, "content", None):
                    stream_text += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end="", flush=True)
                if chunk.choices and getattr(chunk.choices[0].delta, "thread_id", None):
                    stream_thread_id = chunk.choices[0].delta.thread_id
                if chunk.choices and getattr(chunk.choices[0].delta, "files", None):
                    stream_files.extend([item for item in chunk.choices[0].delta.files if isinstance(item, dict)])
                if hasattr(chunk, "generated_files") and chunk.generated_files:
                    stream_files.extend([item for item in chunk.generated_files if isinstance(item, dict)])
            print()
            if not stream_text.strip():
                raise SystemExit("Streaming reply was empty")
            if stream_thread_id and stream_thread_id != thread_id:
                raise SystemExit("Streaming reply returned a different thread_id")
            if not stream_files:
                raise SystemExit("Streaming reply did not return any generated files")
            print(f"Streaming thread ID: {stream_thread_id or thread_id}")
            print(f"Streaming generated files: {len(stream_files)}")
        else:
            second = client.chat.completions.create(model=args.model, messages=messages, temperature=args.temperature)
            second_message = second.choices[0].message
            second_text = str(second_message.content or "")
            second_thread_id = getattr(second_message, "thread_id", None)
            second_files = _require_generated_files(second_message, second, "Second chat reply")
            print("Second reply preview:")
            print(_preview(second_text))
            print(f"Second thread ID: {second_thread_id}")
            print(f"Second generated files: {len(second_files)}")
            if second_thread_id and second_thread_id != thread_id:
                raise SystemExit("Second reply returned a different thread_id")

        cleanup_remote = args.cleanup or auto_generated
        if cleanup_remote:
            for _, file_id in uploaded:
                client.files.delete(file_id)
                print(f"Deleted uploaded file: {file_id}")
        else:
            print("Uploaded files were kept on the server. Pass --cleanup to delete them.")

        print("OpenAI client smoke passed.")
        return 0
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
