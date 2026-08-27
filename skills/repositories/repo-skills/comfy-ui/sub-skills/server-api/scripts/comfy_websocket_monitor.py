#!/usr/bin/env python3
"""Queue a ComfyUI API workflow and monitor completion over /ws.

The monitor uses Python standard-library HTTP and websocket support. It ignores
binary websocket preview frames unless --save-binary-previews is provided.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import socket
import ssl
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


class ComfyWebsocketError(RuntimeError):
    """Raised for websocket or API failures."""


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise SystemExit(f"Could not read {path}: {exc}") from exc


def validate_api_prompt(prompt: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(prompt, dict):
        return ["Top-level workflow must be a JSON object mapping node ids to node objects."]
    if {"nodes", "links", "last_node_id", "last_link_id"}.intersection(prompt.keys()):
        errors.append("Workflow looks like UI workflow JSON; export API JSON with File -> Export (API).")
    if not prompt:
        errors.append("Workflow contains no nodes.")
    for node_id, node in prompt.items():
        if not isinstance(node, dict):
            errors.append(f"Node {node_id!r} must be an object.")
            continue
        if not isinstance(node.get("class_type"), str) or not node.get("class_type"):
            errors.append(f"Node {node_id!r} is missing string class_type.")
        if not isinstance(node.get("inputs"), dict):
            errors.append(f"Node {node_id!r} is missing inputs object.")
    return errors


def normalize_http_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if not normalized.startswith(("http://", "https://")):
        raise SystemExit("--server must start with http:// or https://")
    return normalized


def websocket_url(server: str, client_id: str) -> str:
    parsed = urllib.parse.urlsplit(server)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    query = urllib.parse.urlencode({"clientId": client_id})
    return urllib.parse.urlunsplit((scheme, parsed.netloc, "/ws", query, ""))


def request_json(method: str, url: str, payload: dict[str, Any] | None, timeout: float) -> Any:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise ComfyWebsocketError(f"{method} {url} failed with HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise ComfyWebsocketError(f"{method} {url} failed: {exc.reason}") from exc
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ComfyWebsocketError(f"{method} {url} returned non-JSON response") from exc


def queue_prompt(
    server: str,
    prompt: dict[str, Any],
    client_id: str,
    prompt_id: str | None,
    api_key: str | None,
    timeout: float,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"prompt": prompt, "client_id": client_id}
    if prompt_id:
        payload["prompt_id"] = prompt_id
    if api_key:
        payload["extra_data"] = {"api_key_comfy_org": api_key}
    response = request_json("POST", f"{server}/prompt", payload, timeout)
    if not isinstance(response, dict) or "prompt_id" not in response:
        raise ComfyWebsocketError(f"Unexpected /prompt response: {response!r}")
    return response


def get_history(server: str, prompt_id: str, timeout: float) -> dict[str, Any]:
    url = f"{server}/history/{urllib.parse.quote(prompt_id)}"
    response = request_json("GET", url, None, timeout)
    if not isinstance(response, dict):
        raise ComfyWebsocketError(f"Unexpected /history response: {response!r}")
    return response


def read_http_headers(sock: socket.socket) -> tuple[int, dict[str, str]]:
    raw = b""
    while b"\r\n\r\n" not in raw:
        chunk = sock.recv(4096)
        if not chunk:
            raise ComfyWebsocketError("Socket closed during websocket handshake")
        raw += chunk
        if len(raw) > 65536:
            raise ComfyWebsocketError("Websocket handshake headers are too large")
    header_text = raw.split(b"\r\n\r\n", 1)[0].decode("iso-8859-1")
    lines = header_text.split("\r\n")
    status_parts = lines[0].split(" ", 2)
    if len(status_parts) < 2 or not status_parts[1].isdigit():
        raise ComfyWebsocketError(f"Invalid websocket handshake status: {lines[0]!r}")
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    return int(status_parts[1]), headers


def open_websocket(url: str, timeout: float, insecure_tls: bool) -> socket.socket:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"ws", "wss"}:
        raise ComfyWebsocketError(f"Unsupported websocket scheme: {parsed.scheme}")
    host = parsed.hostname
    if not host:
        raise ComfyWebsocketError("Websocket URL is missing host")
    port = parsed.port or (443 if parsed.scheme == "wss" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    raw_sock = socket.create_connection((host, port), timeout=timeout)
    raw_sock.settimeout(timeout)
    if parsed.scheme == "wss":
        context = ssl._create_unverified_context() if insecure_tls else ssl.create_default_context()
        sock = context.wrap_socket(raw_sock, server_hostname=host)
    else:
        sock = raw_sock

    key = base64.b64encode(os.urandom(16)).decode("ascii")
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {parsed.netloc}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    )
    sock.sendall(request.encode("ascii"))
    status, headers = read_http_headers(sock)
    if status != 101:
        raise ComfyWebsocketError(f"Websocket handshake failed with HTTP {status}")

    expected_accept = base64.b64encode(
        hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
    ).decode("ascii")
    if headers.get("sec-websocket-accept") != expected_accept:
        raise ComfyWebsocketError("Websocket handshake accept header did not match")
    return sock


def recv_exact(sock: socket.socket, length: int) -> bytes:
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ComfyWebsocketError("Websocket closed unexpectedly")
        data += chunk
    return data


def recv_frame(sock: socket.socket) -> tuple[int, bytes]:
    header = recv_exact(sock, 2)
    first, second = header[0], header[1]
    opcode = first & 0x0F
    masked = bool(second & 0x80)
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", recv_exact(sock, 8))[0]
    mask = recv_exact(sock, 4) if masked else b""
    payload = recv_exact(sock, length) if length else b""
    if masked:
        payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    return opcode, payload


def send_close(sock: socket.socket) -> None:
    try:
        sock.sendall(b"\x88\x00")
    except OSError:
        pass


def monitor_until_complete(
    ws_url: str,
    prompt_id: str,
    timeout_seconds: float,
    request_timeout: float,
    insecure_tls: bool,
    save_binary_previews: Path | None,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    current_node: str | None = None
    messages: list[dict[str, Any]] = []
    binary_count = 0
    sock = open_websocket(ws_url, request_timeout, insecure_tls)
    try:
        while time.monotonic() < deadline:
            remaining = max(0.1, min(request_timeout, deadline - time.monotonic()))
            sock.settimeout(remaining)
            opcode, payload = recv_frame(sock)
            if opcode == 0x8:
                raise ComfyWebsocketError("Websocket closed before target prompt completed")
            if opcode == 0x9:
                sock.sendall(b"\x8a" + bytes([len(payload)]) + payload)
                continue
            if opcode == 0x2:
                binary_count += 1
                if save_binary_previews is not None:
                    save_binary_previews.mkdir(parents=True, exist_ok=True)
                    preview_path = save_binary_previews / f"preview-{binary_count:04d}.bin"
                    preview_path.write_bytes(payload)
                continue
            if opcode != 0x1:
                continue

            try:
                message = json.loads(payload.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(message, dict):
                messages.append(message)
                if message.get("type") == "executing" and isinstance(message.get("data"), dict):
                    data = message["data"]
                    if data.get("prompt_id") == prompt_id:
                        current_node = data.get("node")
                        if current_node is None:
                            return {
                                "completed": True,
                                "prompt_id": prompt_id,
                                "binary_frames": binary_count,
                                "messages_seen": len(messages),
                            }
        raise ComfyWebsocketError(f"Timed out waiting for prompt_id {prompt_id}; last node={current_node!r}")
    finally:
        send_close(sock)
        sock.close()


def iter_output_files(history_entry: dict[str, Any]) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    outputs = history_entry.get("outputs", {})
    if not isinstance(outputs, dict):
        return files
    for node_id, node_output in outputs.items():
        if not isinstance(node_output, dict):
            continue
        for media_type, values in node_output.items():
            if not isinstance(values, list):
                continue
            for item in values:
                if isinstance(item, dict) and isinstance(item.get("filename"), str):
                    files.append(
                        {
                            "node_id": str(node_id),
                            "media_type": str(media_type),
                            "filename": item["filename"],
                            "subfolder": str(item.get("subfolder", "")),
                            "type": str(item.get("type", "output")),
                        }
                    )
    return files


def download_outputs(server: str, history: dict[str, Any], prompt_id: str, download_dir: Path, timeout: float) -> list[Path]:
    entry = history.get(prompt_id)
    if not isinstance(entry, dict):
        raise ComfyWebsocketError(f"No history entry for prompt_id {prompt_id}")
    download_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for index, item in enumerate(iter_output_files(entry), start=1):
        query = urllib.parse.urlencode(
            {"filename": item["filename"], "subfolder": item["subfolder"], "type": item["type"]}
        )
        url = f"{server}/view?{query}"
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise ComfyWebsocketError(f"GET {url} failed with HTTP {exc.code}: {details}") from exc
        output_name = f"{index:03d}-{item['node_id']}-{Path(item['filename']).name}"
        output_path = download_dir / output_name
        output_path.write_bytes(data)
        saved.append(output_path)
    return saved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Queue a ComfyUI API workflow and wait for the matching websocket completion event.",
    )
    parser.add_argument("workflow", type=Path, help="Path to API-format workflow JSON.")
    parser.add_argument("--server", default="http://127.0.0.1:8188", help="ComfyUI base URL. Default: %(default)s")
    parser.add_argument("--client-id", default=None, help="Client id for websocket and /prompt. Default: generated UUID.")
    parser.add_argument("--prompt-id", default=None, help="Optional canonical lowercase hyphenated UUID prompt id.")
    parser.add_argument("--api-key-env", default=None, help="Environment variable containing Comfy API key for API nodes.")
    parser.add_argument("--timeout", type=float, default=300.0, help="Overall websocket wait timeout in seconds. Default: %(default)s")
    parser.add_argument("--request-timeout", type=float, default=30.0, help="Per-request/socket operation timeout. Default: %(default)s")
    parser.add_argument("--download-dir", type=Path, default=None, help="Directory for final files from /history and /view.")
    parser.add_argument("--save-binary-previews", type=Path, default=None, help="Optional directory for raw websocket binary frames.")
    parser.add_argument("--insecure-tls", action="store_true", help="Disable TLS certificate verification for wss:// test servers.")
    parser.add_argument("--dry-run", action="store_true", help="Validate JSON and print websocket URL without queueing.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = normalize_http_url(args.server)
    workflow = load_json(args.workflow)
    errors = validate_api_prompt(workflow)
    if errors:
        for error in errors:
            print(f"validation error: {error}", file=sys.stderr)
        return 2

    client_id = args.client_id or str(uuid.uuid4())
    ws_url = websocket_url(server, client_id)
    if args.dry_run:
        print(json.dumps({"ok": True, "nodes": len(workflow), "websocket_url": ws_url}, indent=2))
        return 0

    api_key = None
    if args.api_key_env:
        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            print(f"Environment variable {args.api_key_env!r} is not set or empty.", file=sys.stderr)
            return 2

    try:
        queued = queue_prompt(server, workflow, client_id, args.prompt_id, api_key, args.request_timeout)
        prompt_id = str(queued["prompt_id"])
        monitor = monitor_until_complete(
            ws_url,
            prompt_id,
            args.timeout,
            args.request_timeout,
            args.insecure_tls,
            args.save_binary_previews,
        )
        result: dict[str, Any] = {"queued": queued, "client_id": client_id, "websocket": monitor}
        if args.download_dir is not None:
            history = get_history(server, prompt_id, args.request_timeout)
            saved = download_outputs(server, history, prompt_id, args.download_dir, args.request_timeout)
            result["downloaded"] = [str(path) for path in saved]
        print(json.dumps(result, indent=2))
        return 0
    except (ComfyWebsocketError, OSError, TimeoutError) as exc:
        print(f"ComfyUI websocket error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
