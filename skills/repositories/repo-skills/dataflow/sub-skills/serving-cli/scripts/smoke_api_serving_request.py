#!/usr/bin/env python3
"""Smoke-test APILLMServing_request against a tiny local OpenAI-style server.

The script is offline-safe:
- it only binds to localhost
- it does not use credentials
- it starts a tiny HTTP server with chat and embeddings endpoints
- it adds minimal import shims for base CLI dependencies if needed
"""
from __future__ import annotations

import argparse
import contextlib
import http.server
import importlib.util
import json
import os
import socketserver
import sys
import tempfile
import threading
import urllib.parse
from pathlib import Path


def _find_repo_root() -> Path | None:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "dataflow" / "__init__.py").is_file() and (parent / "pyproject.toml").is_file():
            return parent
    return None


def _write_shims() -> Path:
    shim_dir = Path(tempfile.mkdtemp(prefix="dataflow-api-smoke-shims-"))
    (shim_dir / "colorlog.py").write_text(
        "import logging\n"
        "class ColoredFormatter(logging.Formatter):\n"
        "    def __init__(self, fmt=None, datefmt=None, log_colors=None, secondary_log_colors=None, style='%', **kwargs):\n"
        "        super().__init__(fmt=fmt, datefmt=datefmt, style=style)\n"
        "    def format(self, record):\n"
        "        for key in ('asctime_log_color', 'levelname_log_color', 'name_log_color', 'funcName_log_color', 'lineno_log_color', 'message_log_color', 'reset'):\n"
        "            if not hasattr(record, key):\n"
        "                setattr(record, key, '')\n"
        "        return super().format(record)\n",
        encoding="utf-8",
    )
    (shim_dir / "colorama.py").write_text(
        "class _Ansi:\n"
        "    def __getattr__(self, name):\n"
        "        return ''\n"
        "Fore = _Ansi()\n"
        "Style = _Ansi()\n"
        "def init(*args, **kwargs):\n"
        "    return None\n",
        encoding="utf-8",
    )
    (shim_dir / "appdirs.py").write_text(
        "from pathlib import Path\n"
        "def user_data_dir(appname=None, appauthor=None, roaming=False):\n"
        "    return str(Path.home() / '.local' / 'share' / (appname or 'app'))\n",
        encoding="utf-8",
    )
    return shim_dir


shim_dir = _write_shims()
repo_root = _find_repo_root()
pythonpath_parts = [str(shim_dir)]
if repo_root is not None:
    pythonpath_parts.append(str(repo_root))
if os.environ.get("PYTHONPATH"):
    pythonpath_parts.append(os.environ["PYTHONPATH"])
os.environ["PYTHONPATH"] = os.pathsep.join(p for p in pythonpath_parts if p)
sys.path.insert(0, str(shim_dir))
if repo_root is not None:
    sys.path.insert(0, str(repo_root))


def _load_api_llm_serving_request():
    candidates: list[Path] = []
    package_spec = importlib.util.find_spec("dataflow")
    if package_spec and package_spec.submodule_search_locations:
        for base in package_spec.submodule_search_locations:
            candidates.append(Path(base) / "serving" / "api_llm_serving_request.py")
    if repo_root is not None:
        candidates.insert(0, repo_root / "dataflow" / "serving" / "api_llm_serving_request.py")

    import dataflow  # noqa: F401
    import types

    for module_path in candidates:
        if module_path.is_file():
            serving_pkg = types.ModuleType("dataflow.serving")
            serving_pkg.__path__ = [str(module_path.parent)]
            sys.modules.setdefault("dataflow.serving", serving_pkg)

            spec = importlib.util.spec_from_file_location("dataflow.serving.api_llm_serving_request", module_path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module.APILLMServing_request

    raise FileNotFoundError("Could not locate api_llm_serving_request.py")


APILLMServing_request = _load_api_llm_serving_request()


class TinyOpenAIHandler(http.server.BaseHTTPRequestHandler):
    server_version = "TinyOpenAI/0.1"

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _query(self) -> dict[str, str]:
        parsed = urllib.parse.urlparse(self.path)
        return {k: v[-1] for k, v in urllib.parse.parse_qs(parsed.query).items()}

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/health"):
            body = json.dumps({"ok": True}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        q = self._query()
        _ = self._json_body()

        if parsed.path == "/v1/chat/completions":
            body_text = q.get("body", "hello")
            think_text = q.get("think", "reason")

            # Keepalive-like leading whitespace is harmless for JSON parsing.
            response = {
                "id": "tiny-chatcmpl-001",
                "object": "chat.completion",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": body_text,
                            "reasoning_content": think_text,
                        },
                    }
                ],
            }
            raw = ("\n\n" + json.dumps(response, ensure_ascii=False)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        if parsed.path == "/v1/embeddings":
            dim = int(q.get("dim", "8"))
            response = {
                "object": "list",
                "data": [
                    {
                        "object": "embedding",
                        "index": 0,
                        "embedding": [0.01] * dim,
                    }
                ],
            }
            raw = json.dumps(response, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        self.send_error(404)


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def _start_server() -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), TinyOpenAIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, thread, f"http://{host}:{port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test APILLMServing_request with a local server.")
    parser.add_argument("--chat-body", default="hello", help="Response body for the chat endpoint.")
    parser.add_argument("--think", default="reason", help="Reasoning content for the chat endpoint.")
    parser.add_argument("--embedding-dim", type=int, default=8, help="Embedding dimension for the embeddings endpoint.")
    ns = parser.parse_args()

    server, thread, base_url = _start_server()
    print(f"Started tiny server at {base_url}")

    old_df_api_key = os.environ.get("DF_API_KEY")
    os.environ["DF_API_KEY"] = "dummy-key"

    try:
        chat = APILLMServing_request(
            api_url=f"{base_url}/v1/chat/completions?body={urllib.parse.quote(ns.chat_body)}&think={urllib.parse.quote(ns.think)}",
            key_name_of_api_key="DF_API_KEY",
            model_name="tiny-model",
            max_workers=2,
            max_retries=1,
            connect_timeout=1.0,
            read_timeout=3.0,
        )
        chat_result = chat.generate_from_input(["hello world"], system_prompt="You are helpful")
        assert chat_result and "<think>" in chat_result[0] and "<answer>" in chat_result[0]
        conversation_result = chat.generate_from_conversations(
            [[
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Who are you?"},
            ]]
        )
        assert conversation_result and "<answer>" in conversation_result[0]
        chat.cleanup()

        embed = APILLMServing_request(
            api_url=f"{base_url}/v1/embeddings?dim={ns.embedding_dim}",
            key_name_of_api_key="DF_API_KEY",
            model_name="tiny-embed-model",
            max_workers=2,
            max_retries=1,
            connect_timeout=1.0,
            read_timeout=3.0,
        )
        embeddings = embed.generate_embedding_from_input(["embed me"])
        assert embeddings and len(embeddings[0]) == ns.embedding_dim
        embed.cleanup()

        print("Chat response:")
        print(chat_result[0])
        print("Conversation response:")
        print(conversation_result[0])
        print("Embedding length:", len(embeddings[0]))
        print("Smoke test passed.")
        return 0
    finally:
        if old_df_api_key is None:
            with contextlib.suppress(KeyError):
                del os.environ["DF_API_KEY"]
        else:
            os.environ["DF_API_KEY"] = old_df_api_key
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


if __name__ == "__main__":
    raise SystemExit(main())
