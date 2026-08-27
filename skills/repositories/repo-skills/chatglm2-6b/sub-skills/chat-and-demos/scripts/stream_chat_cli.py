#!/usr/bin/env python3
"""Self-contained ChatGLM2-6B streaming CLI adapted from the repository demo.

This script loads model weights only when executed with --model. Use --help as
a safe parser check. The model path may be a complete local directory or a Hub
identifier that the runtime is allowed to download.
"""
from __future__ import annotations

import argparse
import os
import platform
import signal
from typing import Any


def auto_configure_device_map(num_gpus: int) -> dict[str, int]:
    if num_gpus < 1:
        raise ValueError("num_gpus must be positive")
    if num_gpus == 1:
        return {}
    num_trans_layers = 28
    per_gpu_layers = 30 / num_gpus
    device_map: dict[str, int] = {
        "transformer.embedding.word_embeddings": 0,
        "transformer.encoder.final_layernorm": 0,
        "transformer.output_layer": 0,
        "transformer.rotary_pos_emb": 0,
        "lm_head": 0,
    }
    used = 2
    gpu_target = 0
    for layer in range(num_trans_layers):
        if used >= per_gpu_layers:
            gpu_target += 1
            used = 0
        if gpu_target >= num_gpus:
            raise ValueError("device map exceeds requested GPU count")
        device_map[f"transformer.encoder.layers.{layer}"] = gpu_target
        used += 1
    return device_map


def load_model(args: argparse.Namespace) -> tuple[Any, Any]:
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True, revision=args.revision)
    model = AutoModel.from_pretrained(args.model, trust_remote_code=True, revision=args.revision)
    if args.quantization_bit is not None:
        if not hasattr(model, "quantize"):
            raise RuntimeError("loaded model implementation does not expose quantize(bits)")
        model = model.quantize(args.quantization_bit)
    if args.num_gpus and args.num_gpus > 1:
        from accelerate import dispatch_model
        model = model.half()
        model = dispatch_model(model, device_map=auto_configure_device_map(args.num_gpus))
    elif args.device == "cuda":
        model = model.cuda()
    elif args.device == "cpu":
        model = model.float()
    elif args.device == "mps":
        model = model.to("mps")
    else:
        try:
            import torch
            if torch.cuda.is_available():
                model = model.cuda()
            else:
                model = model.float()
        except Exception:
            model = model.float()
    return tokenizer, model.eval()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Local model directory or Hub id such as THUDM/chatglm2-6b")
    parser.add_argument("--revision", default=None)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda", "mps"), default="auto")
    parser.add_argument("--quantization-bit", type=int, choices=(4, 8), default=None)
    parser.add_argument("--num-gpus", type=int, default=1, help="Use accelerate dispatch for values greater than one")
    parser.add_argument("--max-length", type=int, default=8192)
    parser.add_argument("--top-p", type=float, default=0.8)
    parser.add_argument("--temperature", type=float, default=0.95)
    args = parser.parse_args()

    tokenizer, model = load_model(args)
    clear_command = "cls" if platform.system() == "Windows" else "clear"
    stop_stream = {"value": False}

    def signal_handler(_signal: int, _frame: object) -> None:
        stop_stream["value"] = True

    signal.signal(signal.SIGINT, signal_handler)
    history: list[list[str]] = []
    past_key_values = None
    print("ChatGLM2-6B CLI: enter text, clear to reset history, stop to exit")
    while True:
        query = input("\nUser: ")
        if query.strip() == "stop":
            break
        if query.strip() == "clear":
            history, past_key_values = [], None
            os.system(clear_command)
            print("ChatGLM2-6B CLI: enter text, clear to reset history, stop to exit")
            continue
        print("\nChatGLM2-6B: ", end="", flush=True)
        current_length = 0
        for response, history, past_key_values in model.stream_chat(
            tokenizer,
            query,
            history=history,
            past_key_values=past_key_values,
            return_past_key_values=True,
            max_length=args.max_length,
            top_p=args.top_p,
            temperature=args.temperature,
        ):
            if stop_stream["value"]:
                stop_stream["value"] = False
                break
            print(response[current_length:], end="", flush=True)
            current_length = len(response)
        print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
