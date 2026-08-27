#!/usr/bin/env python3
"""Janus-family multimodal-understanding helper.

Safe default: prints a dry-run plan and does not download model weights unless
--run-model is provided.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence


@dataclass
class Plan:
    family: str
    model_id: str
    image_count: int
    placeholder_count: int
    roles: tuple[str, str]
    run_model: bool
    device: str
    dtype: str


def _family_roles(family: str) -> tuple[str, str]:
    if family == "janus-pro":
        return ("<|User|>", "<|Assistant|>")
    return ("User", "Assistant")


def _build_prompt(question: str, family: str) -> tuple[str, list[dict[str, str]]]:
    user_role, assistant_role = _family_roles(family)
    conversation = [
        {"role": user_role, "content": f"<image_placeholder>\n{question}"},
        {"role": assistant_role, "content": ""},
    ]
    return conversation[0]["content"], conversation


def _read_image_args(images: Sequence[str]) -> list[str]:
    return list(images)


def _dry_run(plan: Plan, question: str, images: list[str]) -> int:
    print("Janus multimodal-understanding dry run")
    print(json.dumps(
        {
            "family": plan.family,
            "model_id": plan.model_id,
            "image_count": plan.image_count,
            "placeholder_count": plan.placeholder_count,
            "roles": list(plan.roles),
            "device": plan.device,
            "dtype": plan.dtype,
            "run_model": plan.run_model,
            "question": question,
            "images": images,
        },
        indent=2,
        sort_keys=True,
    ))
    print()
    print("Next step:")
    if plan.run_model:
        print("- The helper is ready to import torch/transformers and run the model.")
    else:
        print("- Re-run with --run-model only after you have the required model access and backend.")
    return 0


def _lazy_run(plan: Plan, question: str, images: list[str], max_new_tokens: int, temperature: float, top_p: float, show_prompt: bool) -> int:
    import torch
    from transformers import AutoModelForCausalLM

    if plan.family == "janusflow":
        from janus.janusflow.models import MultiModalityCausalLM, VLChatProcessor
    else:
        from janus.models import MultiModalityCausalLM, VLChatProcessor
    from janus.utils.io import load_pil_images

    if plan.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = plan.device

    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but torch.cuda.is_available() is false.")

    dtype_map = {
        "auto": torch.bfloat16 if device == "cuda" else torch.float32,
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }
    dtype = dtype_map[plan.dtype]

    user_role, assistant_role = plan.roles
    conversation = [
        {"role": user_role, "content": f"<image_placeholder>\n{question}", "images": images},
        {"role": assistant_role, "content": ""},
    ]
    pil_images = load_pil_images(conversation)
    vl_chat_processor = VLChatProcessor.from_pretrained(plan.model_id)
    tokenizer = vl_chat_processor.tokenizer

    if plan.family == "janusflow":
        vl_gpt = MultiModalityCausalLM.from_pretrained(plan.model_id, trust_remote_code=True)
    else:
        vl_gpt = AutoModelForCausalLM.from_pretrained(plan.model_id, trust_remote_code=True)

    vl_gpt = vl_gpt.to(dtype=dtype)
    if device == "cuda":
        vl_gpt = vl_gpt.cuda().eval()
    else:
        vl_gpt = vl_gpt.to(device).eval()

    prepare_inputs = vl_chat_processor(conversations=conversation, images=pil_images, force_batchify=True).to(device, dtype=dtype)
    if show_prompt:
        print("Formatted prompt:\n")
        print(prepare_inputs["sft_format"][0])
        print()

    inputs_embeds = vl_gpt.prepare_inputs_embeds(**prepare_inputs)
    outputs = vl_gpt.language_model.generate(
        inputs_embeds=inputs_embeds,
        attention_mask=prepare_inputs.attention_mask,
        pad_token_id=tokenizer.eos_token_id,
        bos_token_id=tokenizer.bos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        max_new_tokens=max_new_tokens,
        do_sample=temperature > 0,
        temperature=temperature,
        top_p=top_p,
        use_cache=True,
    )

    answer = tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)
    print(answer)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate or run Janus-family multimodal understanding.")
    parser.add_argument("--family", choices=["janus", "janus-pro", "janusflow"], default="janus", help="Model family to target.")
    parser.add_argument("--model-id", default="deepseek-ai/Janus-1.3B", help="Hugging Face model id for the chosen family.")
    parser.add_argument("--image", action="append", default=[], help="Image path or data URI. Repeat for multiple images.")
    parser.add_argument("--question", required=True, help="Question to ask about the image(s).")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto", help="Execution device for the real model run.")
    parser.add_argument("--dtype", choices=["auto", "bfloat16", "float16", "float32"], default="auto", help="Model dtype for the real model run.")
    parser.add_argument("--max-new-tokens", type=int, default=512, help="Maximum new tokens for generation.")
    parser.add_argument("--temperature", type=float, default=0.1, help="Sampling temperature; values above zero enable sampling.")
    parser.add_argument("--top-p", type=float, default=0.95, help="Top-p nucleus sampling value.")
    parser.add_argument("--run-model", action="store_true", help="Import the runtime dependencies and run the model.")
    parser.add_argument("--show-prompt", action="store_true", help="Print the formatted prompt before generation.")
    parser.add_argument("--json", action="store_true", help="Print the dry-run plan as JSON only.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.image and args.run_model:
        parser.error("--run-model requires at least one --image")

    roles = _family_roles(args.family)
    prompt, _conversation = _build_prompt(args.question, args.family)
    plan = Plan(
        family=args.family,
        model_id=args.model_id,
        image_count=len(args.image),
        placeholder_count=prompt.count("<image_placeholder>"),
        roles=roles,
        run_model=args.run_model,
        device=args.device,
        dtype=args.dtype,
    )

    if not args.run_model:
        if args.json:
            print(json.dumps(plan.__dict__, indent=2, sort_keys=True))
        else:
            _dry_run(plan, args.question, _read_image_args(args.image))
        return 0

    return _lazy_run(
        plan=plan,
        question=args.question,
        images=_read_image_args(args.image),
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        show_prompt=args.show_prompt,
    )


if __name__ == "__main__":
    raise SystemExit(main())
