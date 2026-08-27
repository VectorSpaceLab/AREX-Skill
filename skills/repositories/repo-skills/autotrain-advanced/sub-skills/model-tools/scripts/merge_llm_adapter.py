#!/usr/bin/env python3
"""Standalone AutoTrain LLM adapter merge helper.

Source-derived from `src/autotrain/tools/merge_adapter.py` with a small CLI wrapper.
Requires AutoTrain Advanced, torch, transformers, and peft in the active env.
"""

from __future__ import annotations

import argparse

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from autotrain import logger
from autotrain.trainers.common import ALLOW_REMOTE_CODE


def merge_llm_adapter(base_model_path, adapter_path, token, output_folder=None, pad_to_multiple_of=None, push_to_hub=False):
    if output_folder is None and push_to_hub is False:
        raise ValueError("You must specify either --output-folder or --push-to-hub")

    logger.info("Loading adapter...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        trust_remote_code=ALLOW_REMOTE_CODE,
        token=token,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        adapter_path,
        trust_remote_code=ALLOW_REMOTE_CODE,
        token=token,
    )
    if pad_to_multiple_of:
        base_model.resize_token_embeddings(len(tokenizer), pad_to_multiple_of=pad_to_multiple_of)
    else:
        base_model.resize_token_embeddings(len(tokenizer))

    model = PeftModel.from_pretrained(
        base_model,
        adapter_path,
        token=token,
    )
    model = model.merge_and_unload()

    if output_folder is not None:
        logger.info("Saving target model...")
        model.save_pretrained(output_folder)
        tokenizer.save_pretrained(output_folder)
        logger.info(f"Model saved to {output_folder}")

    if push_to_hub:
        logger.info("Pushing model to Hugging Face Hub...")
        model.push_to_hub(adapter_path)
        tokenizer.push_to_hub(adapter_path)
        logger.info(f"Model pushed to Hugging Face Hub as {adapter_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-model-path", required=True)
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--token")
    parser.add_argument("--pad-to-multiple-of", type=int)
    parser.add_argument("--output-folder")
    parser.add_argument("--push-to-hub", action="store_true")
    args = parser.parse_args()
    merge_llm_adapter(
        base_model_path=args.base_model_path,
        adapter_path=args.adapter_path,
        token=args.token,
        output_folder=args.output_folder,
        pad_to_multiple_of=args.pad_to_multiple_of,
        push_to_hub=args.push_to_hub,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
