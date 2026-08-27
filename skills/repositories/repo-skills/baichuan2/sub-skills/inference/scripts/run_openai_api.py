#!/usr/bin/env python3
"""Run a small OpenAI-compatible Baichuan2 Chat completions server.

The server intentionally supports non-streaming `/v1/chat/completions` only,
matching the behavior of the Baichuan2 demo API. Use `--dry-run` or `--help`
to inspect configuration without importing Flask/Transformers or loading model
weights.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from typing import Any

DEFAULT_MODEL = "baichuan-inc/Baichuan2-13B-Chat"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Serve Baichuan2 Chat through a non-streaming OpenAI-style chat-completions API.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", default=os.environ.get("BAICHUAN2_MODEL", DEFAULT_MODEL), help="Hugging Face model id or local Chat-model directory.")
    parser.add_argument("--host", default=os.environ.get("BAICHUAN2_API_HOST", "0.0.0.0"), help="Flask bind address.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("BAICHUAN2_API_PORT", "8000")), help="Flask bind port.")
    parser.add_argument("--dtype", choices=("auto", "float16", "bfloat16", "float32"), default=os.environ.get("BAICHUAN2_DTYPE", "float16"), help="Model weight dtype. 'auto' omits torch_dtype.")
    parser.add_argument("--device-map", default=os.environ.get("BAICHUAN2_DEVICE_MAP", "auto"), help="Transformers device_map value; use 'none' to omit.")
    parser.add_argument("--no-trust-remote-code", action="store_false", dest="trust_remote_code", default=True, help="Disable trust_remote_code. Baichuan2 HF models normally require it.")
    parser.add_argument("--threaded", action="store_true", help="Allow Flask threaded request handling. Default is single-threaded for GPU safety.")
    parser.add_argument("--debug", action="store_true", help="Run Flask in debug mode.")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved launch configuration and exit before importing server/model dependencies.")
    return parser


def dtype_from_name(name: str):
    if name == "auto":
        return None
    import torch

    mapping = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }
    return mapping[name]


def dry_run(args: argparse.Namespace) -> None:
    config = {
        "model": args.model,
        "host": args.host,
        "port": args.port,
        "dtype": args.dtype,
        "device_map": None if args.device_map == "none" else args.device_map,
        "trust_remote_code": args.trust_remote_code,
        "endpoint": f"http://{args.host}:{args.port}/v1/chat/completions",
        "streaming_supported": False,
    }
    print(json.dumps(config, ensure_ascii=False, indent=2))
    if "Base" in os.path.basename(str(args.model)):
        print("WARNING: the API helper expects a Baichuan2 Chat checkpoint, not a Base checkpoint.")


def load_model_and_tokenizer(args: argparse.Namespace):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from transformers.generation.utils import GenerationConfig

    print(f"Loading tokenizer: {args.model}", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        use_fast=False,
        trust_remote_code=args.trust_remote_code,
    )

    model_kwargs: dict[str, Any] = {"trust_remote_code": args.trust_remote_code}
    if args.device_map != "none":
        model_kwargs["device_map"] = args.device_map
    dtype = dtype_from_name(args.dtype)
    if dtype is not None:
        model_kwargs["torch_dtype"] = dtype

    print(f"Loading model: {args.model}", flush=True)
    model = AutoModelForCausalLM.from_pretrained(args.model, **model_kwargs)
    try:
        model.generation_config = GenerationConfig.from_pretrained(args.model)
    except Exception as exc:  # pragma: no cover - depends on model artifacts
        print(f"WARNING: could not load GenerationConfig from {args.model}: {exc}", flush=True)
    model.eval()

    if not hasattr(model, "chat"):
        raise RuntimeError("Loaded model does not expose model.chat(...); use a Baichuan2 Chat checkpoint.")

    if torch.cuda.is_available():
        print(f"CUDA devices visible: {torch.cuda.device_count()}", flush=True)
    return model, tokenizer


def normalize_messages(raw_messages: Any) -> list[dict[str, str]]:
    if not isinstance(raw_messages, list) or not raw_messages:
        raise ValueError("messages must be a non-empty list of {'role', 'content'} objects")

    messages: list[dict[str, str]] = []
    for index, item in enumerate(raw_messages):
        if not isinstance(item, dict):
            raise ValueError(f"messages[{index}] must be an object")
        role = item.get("role")
        content = item.get("content")
        if not isinstance(role, str) or not role:
            raise ValueError(f"messages[{index}].role must be a non-empty string")
        if not isinstance(content, str):
            raise ValueError(f"messages[{index}].content must be a string")
        messages.append({"role": role, "content": content})
    return messages


def count_tokens(tokenizer: Any, text: str) -> int:
    try:
        return len(tokenizer.encode(text))
    except Exception:
        return len(text)


def create_app(args: argparse.Namespace, model: Any, tokenizer: Any):
    from flask import Flask, jsonify, request

    app = Flask(__name__)

    def error_response(message: str, status: int, code: str = "bad_request"):
        return jsonify({"error": {"message": message, "type": "invalid_request_error", "code": code}}), status

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "model": args.model, "streaming": False})

    @app.post("/v1/chat/completions")
    def chat_completion():
        data = request.get_json(silent=True)
        if data is None:
            return error_response("Request body must be JSON.", 400, "invalid_json")

        if data.get("stream", False):
            return error_response(
                "Streaming is not supported by this Baichuan2 API helper; send stream=false.",
                400,
                "streaming_not_supported",
            )

        try:
            messages = normalize_messages(data.get("messages"))
        except ValueError as exc:
            return error_response(str(exc), 400, "invalid_messages")

        try:
            import torch

            with torch.inference_mode():
                response_text = model.chat(tokenizer, messages)
        except Exception as exc:  # pragma: no cover - model/runtime dependent
            return jsonify({"error": {"message": str(exc), "type": "server_error", "code": "generation_failed"}}), 500

        prompt_tokens = sum(count_tokens(tokenizer, item["content"]) for item in messages)
        completion_tokens = count_tokens(tokenizer, response_text)
        response = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": args.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": response_text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
        return jsonify(response)

    return app


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.dry_run:
        dry_run(args)
        return 0

    if "Base" in os.path.basename(str(args.model)):
        print("WARNING: this API helper expects a Baichuan2 Chat checkpoint, not a Base checkpoint.", flush=True)

    model, tokenizer = load_model_and_tokenizer(args)
    app = create_app(args, model, tokenizer)
    print(f"Serving non-streaming chat completions at http://{args.host}:{args.port}/v1/chat/completions", flush=True)
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=args.threaded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
