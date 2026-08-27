#!/usr/bin/env python3
"""Streamlit Baichuan2 Chat demo.

Run with Streamlit for the web UI, or use `--help` / `--dry-run` with
plain Python to inspect configuration without importing Streamlit/Transformers
or loading model weights.

Example:
  streamlit run scripts/chat_web_demo.py --server.address 0.0.0.0 --server.port 8501 -- --model baichuan-inc/Baichuan2-13B-Chat
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any

DEFAULT_MODEL = "baichuan-inc/Baichuan2-13B-Chat"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a Streamlit Baichuan2 Chat web demo. Use Chat checkpoints, not Base checkpoints.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", default=os.environ.get("BAICHUAN2_MODEL", DEFAULT_MODEL), help="Hugging Face model id or local Chat-model directory.")
    parser.add_argument("--dtype", choices=("auto", "float16", "bfloat16", "float32"), default=os.environ.get("BAICHUAN2_DTYPE", "float16"), help="Model weight dtype. 'auto' omits torch_dtype.")
    parser.add_argument("--device-map", default=os.environ.get("BAICHUAN2_DEVICE_MAP", "auto"), help="Transformers device_map value; use 'none' to omit.")
    parser.add_argument("--no-trust-remote-code", action="store_false", dest="trust_remote_code", default=True, help="Disable trust_remote_code. Baichuan2 HF models normally require it.")
    stream_group = parser.add_mutually_exclusive_group()
    stream_group.add_argument("--stream", dest="stream", action="store_true", default=True, help="Stream assistant updates into the page.")
    stream_group.add_argument("--no-stream", dest="stream", action="store_false", help="Generate each assistant answer non-streaming.")
    parser.add_argument("--max-new-tokens", type=int, help="Optional override for model.generation_config.max_new_tokens.")
    parser.add_argument("--page-title", default="Baichuan 2", help="Streamlit page title.")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved launch configuration and exit before importing web/model dependencies.")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        # Streamlit can inject or forward extra arguments in some launch modes.
        # Keep the app tolerant, but expose the ignored values in dry-run/sidebar.
        args.ignored_args = unknown
    else:
        args.ignored_args = []
    return args


def dry_run(args: argparse.Namespace) -> None:
    config = {
        "model": args.model,
        "dtype": args.dtype,
        "device_map": None if args.device_map == "none" else args.device_map,
        "trust_remote_code": args.trust_remote_code,
        "stream": args.stream,
        "max_new_tokens": args.max_new_tokens,
        "page_title": args.page_title,
        "ignored_args": args.ignored_args,
        "launch_example": "streamlit run scripts/chat_web_demo.py --server.address 0.0.0.0 --server.port 8501 -- --model " + args.model,
    }
    print(json.dumps(config, ensure_ascii=False, indent=2))
    if "Base" in os.path.basename(str(args.model)):
        print("WARNING: the Streamlit helper expects a Baichuan2 Chat checkpoint, not a Base checkpoint.")


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


def maybe_empty_mps_cache() -> None:
    try:
        import torch

        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            torch.mps.empty_cache()
    except Exception:
        pass


def run_streamlit_app(args: argparse.Namespace) -> None:
    import streamlit as st
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from transformers.generation.utils import GenerationConfig

    st.set_page_config(page_title=args.page_title)
    st.title(args.page_title)

    if "Base" in os.path.basename(str(args.model)):
        st.warning("This web helper expects a Baichuan2 Chat checkpoint. Use the Base generation recipe for Base checkpoints.")

    if args.ignored_args:
        st.sidebar.warning(f"Ignored script arguments: {args.ignored_args}")

    st.sidebar.markdown("### Model")
    st.sidebar.write(args.model)
    st.sidebar.write(f"dtype: `{args.dtype}`")
    st.sidebar.write(f"device_map: `{None if args.device_map == 'none' else args.device_map}`")
    st.sidebar.write(f"streaming: `{args.stream}`")
    if st.sidebar.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

    @st.cache_resource(show_spinner="Loading Baichuan2 model...")
    def init_model(
        model_id: str,
        dtype_name: str,
        device_map: str,
        trust_remote_code: bool,
        max_new_tokens: int | None,
    ):
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            use_fast=False,
            trust_remote_code=trust_remote_code,
        )
        model_kwargs: dict[str, Any] = {"trust_remote_code": trust_remote_code}
        if device_map != "none":
            model_kwargs["device_map"] = device_map
        dtype = dtype_from_name(dtype_name)
        if dtype is not None:
            model_kwargs["torch_dtype"] = dtype
        model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
        try:
            model.generation_config = GenerationConfig.from_pretrained(model_id)
        except Exception as exc:  # pragma: no cover - depends on model artifacts
            st.warning(f"Could not load GenerationConfig from {model_id}: {exc}")
        if max_new_tokens is not None:
            model.generation_config.max_new_tokens = max_new_tokens
        model.eval()
        if not hasattr(model, "chat"):
            raise RuntimeError("Loaded model does not expose model.chat(...); use a Baichuan2 Chat checkpoint.")
        return model, tokenizer

    try:
        model, tokenizer = init_model(
            args.model,
            args.dtype,
            args.device_map,
            args.trust_remote_code,
            args.max_new_tokens,
        )
    except Exception as exc:  # pragma: no cover - depends on runtime setup
        st.error(f"Failed to load model: {exc}")
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.chat_message("assistant", avatar="🤖"):
        st.markdown("您好，我是百川大模型，很高兴为您服务🥰")

    for message in st.session_state.messages:
        avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    prompt = st.chat_input("Shift + Enter for newline, Enter to send")
    if prompt:
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        print(f"[user] {prompt}", flush=True)

        response = ""
        with st.chat_message("assistant", avatar="🤖"):
            placeholder = st.empty()
            with torch.inference_mode():
                if args.stream:
                    for response in model.chat(tokenizer, st.session_state.messages, stream=True):
                        placeholder.markdown(response)
                        maybe_empty_mps_cache()
                else:
                    response = model.chat(tokenizer, st.session_state.messages)
                    placeholder.markdown(response)
                    maybe_empty_mps_cache()

        if response:
            st.session_state.messages.append({"role": "assistant", "content": response})
            print(json.dumps(st.session_state.messages, ensure_ascii=False), flush=True)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.dry_run:
        dry_run(args)
        return 0
    run_streamlit_app(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
