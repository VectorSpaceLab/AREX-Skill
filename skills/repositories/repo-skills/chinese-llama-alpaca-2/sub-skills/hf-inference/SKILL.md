---
name: hf-inference
description: "Routes Chinese-LLaMA-Alpaca-2 local generation, chat, and
  speculative-sampling workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# hf-inference

Use this sub-skill for direct Transformers-based inference, interactive chat, speculative sampling, and prompt-template handling.

## Use it when

- the user mentions `inference_hf.py`, `gradio_demo.py`, `speculative_sample.py`, or the attention patch helpers
- the task is about `--interactive`, `--with_prompt`, `--negative_prompt`, `--guidance_scale`, or `--speculative_sampling`
- the task needs CPU-only inference, 4-bit/8-bit loading, NTK scaling, or FlashAttention acceleration
- the user wants a chat UI rather than an HTTP server

## Workflow

1. Read `references/workflows.md` for the supported CLI flag combinations.
2. Check `assets/prompts/` and `assets/tokenizer/` if the task is about prompt wrapping or tokenizer compatibility.
3. Use `scripts/inference/inference_hf.py` for single-turn or file-based generation.
4. Use `scripts/inference/gradio_demo.py` for multi-turn chat or a browser UI.
5. Read `references/troubleshooting.md` if a run fails on tokenizer paths, draft models, optional acceleration helpers, or CPU/GPU constraints.

## Bundled runtime files

- `scripts/inference/inference_hf.py`
- `scripts/inference/gradio_demo.py`
- `scripts/inference/speculative_sample.py`
- `scripts/inference/flash_attn_patch_for_inference.py`
- `scripts/attn_and_long_ctx_patches.py`
- root asset `../../assets/prompts/alpaca-2.txt`
- root asset `../../assets/prompts/alpaca-2-long.txt`
- root asset `../../assets/tokenizer/`

## What to read first

- `references/workflows.md` for the supported CLI modes and prompt behavior
- `references/troubleshooting.md` for optional acceleration and model-loading failures
- `../../references/prompt-and-tokenizer.md` when the task is specifically about prompt text or tokenizer files

## Routing notes

- Use this sub-skill for local generation and chat UX.
- Use the API-serving sub-skill when the task becomes an HTTP server instead of a direct generation CLI.
- The optional vLLM code path inside the inference CLI is still an inference concern, but the dedicated server sub-skill is usually the better choice when the user wants deployment rather than local generation.
