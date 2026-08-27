#!/usr/bin/env python3
"""Run an OmniLive audio understanding prompt against a local model root.

This is a source-derived runnable entrypoint. It imports Swift and torch only
when executed and expects an `audio/` model component under --model-root unless
--audio-model-path is given.
"""
from __future__ import annotations

import argparse
import os


def main() -> int:
    parser = argparse.ArgumentParser(description="OmniLive audio ASR/classification entrypoint")
    parser.add_argument("--model-root", default=os.environ.get("IXC_OMNILIVE_MODEL_ROOT", "internlm-xcomposer2d5-ol-7b"))
    parser.add_argument("--audio-model-path", default="", help="Override the audio component path. Defaults to <model-root>/audio.")
    parser.add_argument("--audio", action="append", required=True, help="Audio file path. Repeat for multiple files.")
    parser.add_argument("--task", choices=["asr", "classify"], default="asr")
    parser.add_argument("--device-map", default="cuda:0")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()

    import torch
    from swift.llm import get_model_tokenizer, get_template, ModelType, get_default_template_type, inference
    from swift.utils import seed_everything

    model_type = ModelType.qwen2_audio_7b_instruct
    model_id_or_path = args.audio_model_path or os.path.join(args.model_root, "audio")
    template_type = get_default_template_type(model_type)
    model, tokenizer = get_model_tokenizer(
        model_type,
        torch.float16,
        model_id_or_path=model_id_or_path,
        model_kwargs={"device_map": args.device_map},
    )
    model.generation_config.max_new_tokens = args.max_new_tokens
    template = get_template(template_type, tokenizer)
    seed_everything(42)

    query = "<audio>Classify the audio." if args.task == "classify" else "<audio>Detect the language and recognize the speech."
    for audio_path in args.audio:
        response, _ = inference(model, template, query, audios=audio_path)
        print(f"audio: {audio_path}")
        print(f"query: {query}")
        print(f"response: {response}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
