#!/usr/bin/env python3
"""Queue a ComfyUI API workflow and optionally collect outputs.

This helper expects JSON exported from ComfyUI with File -> Export (API).
It uses only the Python standard library and never stores credentials.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


class ComfyApiError(RuntimeError):
    """Raised for ComfyUI API request failures."""


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

    ui_workflow_keys = {"nodes", "links", "last_node_id", "last_link_id"}
    if ui_workflow_keys.intersection(prompt.keys()):
        errors.append(
            "Workflow looks like UI workflow JSON. Export API JSON with File -> Export (API)."
        )

    if not prompt:
        errors.append("Workflow contains no nodes.")

    for node_id, node in prompt.items():
        if not isinstance(node_id, str):
            errors.append(f"Node id {node_id!r} is not a string.")
        if not isinstance(node, dict):
            errors.append(f"Node {node_id!r} must be an object.")
            continue
        class_type = node.get("class_type")
        if not isinstance(class_type, str) or not class_type:
            errors.append(f"Node {node_id!r} is missing string class_type.")
        inputs = node.get("inputs")
        if inputs is None:
            errors.append(f"Node {node_id!r} is missing inputs object.")
        elif not isinstance(inputs, dict):
            errors.append(f"Node {node_id!r} inputs must be an object.")
    return errors


def normalize_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if not normalized.startswith(("http://", "https://")):
        raise SystemExit("--server must start with http:// or https://")
    return normalized


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> Any:
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
        raise ComfyApiError(f"{method} {url} failed with HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise ComfyApiError(f"{method} {url} failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise ComfyApiError(f"{method} {url} timed out") from exc

    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ComfyApiError(f"{method} {url} returned non-JSON response") from exc


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
    response = request_json("POST", f"{server}/prompt", payload, timeout=timeout)
    if not isinstance(response, dict) or "prompt_id" not in response:
        raise ComfyApiError(f"Unexpected /prompt response: {response!r}")
    return response


def get_history(server: str, prompt_id: str, timeout: float) -> dict[str, Any]:
    response = request_json("GET", f"{server}/history/{urllib.parse.quote(prompt_id)}", timeout=timeout)
    if not isinstance(response, dict):
        raise ComfyApiError(f"Unexpected /history response: {response!r}")
    return response


def wait_for_history(
    server: str,
    prompt_id: str,
    timeout_seconds: float,
    poll_interval: float,
    request_timeout: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        history = get_history(server, prompt_id, request_timeout)
        if prompt_id in history:
            return history
        time.sleep(poll_interval)
    raise ComfyApiError(f"Timed out waiting for history for prompt_id {prompt_id}")


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


def safe_download_name(item: dict[str, str], index: int) -> str:
    filename = Path(item["filename"]).name or f"output-{index}"
    node_id = item.get("node_id", "node").replace("/", "_")
    return f"{index:03d}-{node_id}-{filename}"


def download_outputs(
    server: str,
    history: dict[str, Any],
    prompt_id: str,
    download_dir: Path,
    timeout: float,
) -> list[Path]:
    entry = history.get(prompt_id)
    if not isinstance(entry, dict):
        raise ComfyApiError(f"No history entry for prompt_id {prompt_id}")

    download_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for index, item in enumerate(iter_output_files(entry), start=1):
        query = urllib.parse.urlencode(
            {
                "filename": item["filename"],
                "subfolder": item["subfolder"],
                "type": item["type"],
            }
        )
        url = f"{server}/view?{query}"
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise ComfyApiError(f"GET {url} failed with HTTP {exc.code}: {details}") from exc
        except urllib.error.URLError as exc:
            raise ComfyApiError(f"GET {url} failed: {exc.reason}") from exc

        output_path = download_dir / safe_download_name(item, index)
        output_path.write_bytes(data)
        saved.append(output_path)
    return saved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Queue a ComfyUI API workflow JSON and optionally collect output files.",
    )
    parser.add_argument("workflow", type=Path, help="Path to API-format workflow JSON.")
    parser.add_argument(
        "--server",
        default="http://127.0.0.1:8188",
        help="ComfyUI base URL. Default: %(default)s",
    )
    parser.add_argument(
        "--client-id",
        default=None,
        help="Client id to send with /prompt. Default: generated UUID.",
    )
    parser.add_argument(
        "--prompt-id",
        default=None,
        help="Optional canonical lowercase hyphenated UUID prompt id. Omit to let server generate it.",
    )
    parser.add_argument(
        "--api-key-env",
        default=None,
        help="Environment variable containing Comfy API key for API nodes; sent as extra_data.api_key_comfy_org.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate JSON and print summary without queueing.")
    parser.add_argument("--wait", action="store_true", help="Poll /history until the prompt appears.")
    parser.add_argument("--timeout", type=float, default=300.0, help="Overall wait timeout in seconds. Default: %(default)s")
    parser.add_argument("--request-timeout", type=float, default=30.0, help="Per-request timeout in seconds. Default: %(default)s")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="History polling interval in seconds. Default: %(default)s")
    parser.add_argument("--download-dir", type=Path, default=None, help="Directory for downloaded output files; implies --wait.")
    parser.add_argument("--print-history", action="store_true", help="Print final history JSON to stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = normalize_base_url(args.server)
    workflow = load_json(args.workflow)
    errors = validate_api_prompt(workflow)
    if errors:
        for error in errors:
            print(f"validation error: {error}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(json.dumps({"ok": True, "nodes": len(workflow)}, indent=2))
        return 0

    client_id = args.client_id or str(uuid.uuid4())
    api_key = None
    if args.api_key_env:
        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            print(f"Environment variable {args.api_key_env!r} is not set or empty.", file=sys.stderr)
            return 2

    try:
        queued = queue_prompt(server, workflow, client_id, args.prompt_id, api_key, args.request_timeout)
        prompt_id = str(queued["prompt_id"])
        result: dict[str, Any] = {"queued": queued, "client_id": client_id}

        should_wait = args.wait or args.download_dir is not None or args.print_history
        history: dict[str, Any] | None = None
        if should_wait:
            history = wait_for_history(
                server,
                prompt_id,
                args.timeout,
                args.poll_interval,
                args.request_timeout,
            )
            result["history_found"] = True

        if args.download_dir is not None:
            assert history is not None
            saved = download_outputs(server, history, prompt_id, args.download_dir, args.request_timeout)
            result["downloaded"] = [str(path) for path in saved]

        if args.print_history and history is not None:
            result["history"] = history

        print(json.dumps(result, indent=2))
        return 0
    except ComfyApiError as exc:
        print(f"ComfyUI API error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
