---
name: prompt-and-image-conditioning
description: "Route HunyuanImage-3.0 system prompts, recaption and think modes,
  DeepSeek rewrite, text rendering, image size, and multi-image conditioning
  decisions."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Prompt and Image Conditioning

Use this sub-skill when a task is about how to phrase prompts or how to choose `use_system_prompt`, `bot_task`, `--rewrite`, `image`, `image_size`, or `infer_align_image_size` for HunyuanImage-3.0 generation.

Do not use this sub-skill for raw model architecture, tokenizer template internals, checkpoint loading internals, full local command walkthroughs, Gradio launch, or vLLM deployment. For those, route to sibling skills:

- CLI command construction and demo variants: [local inference CLI](../local-inference-cli/SKILL.md).
- Public API objects, tokenizer/template internals, and image processor internals: [core APIs and architecture](../core-apis-and-architecture/SKILL.md).

## Operating route

1. Read [prompt modes](references/prompt-modes.md) to choose the prompt path:
   - manual prompt writing,
   - model self-rewrite with `recaption` or `think_recaption`,
   - external DeepSeek PE rewrite,
   - direct multi-image conditioning.
2. Read [troubleshooting](references/troubleshooting.md) before diagnosing failures, especially for credentials, network, dynamic mode, image lists, text rendering, or the known `args.sys_deepseek_prompt` rewrite typo.
3. Optionally run [prompt-mode validator](scripts/validate_prompt_modes.py) to check a proposed mode combination without loading model weights or calling any network service.

## Fast recommendations

- For HunyuanImage-3.0-Instruct or Instruct-Distil image editing, multi-image fusion, or sparse prompts: prefer `use_system_prompt="en_unified"` with `bot_task="think_recaption"`. Pass conditional images as an ordered list in the API or comma-separated paths in the CLI.
- For direct text-to-image with an already detailed prompt: use `bot_task="image"`; use `image_size="auto"` when the model should infer a ratio, or a fixed `HxW` / `W:H` value when composition must be constrained.
- For the base pretrain checkpoint: do not assume local model self-rewrite. Write a rich manual prompt, or use the DeepSeek PE rewrite path only when Tencent credentials and network access are intentionally available.
- For UI, poster, logo, or text rendering: every visible text string must be explicit and enclosed in double quotes; preserve the language and spelling of user-specified text.
- Avoid `use_system_prompt="dynamic"` with the local CLI's `bot_task="think_recaption"`: the source resolver maps dynamic mode for `think`, `recaption`, and `image`, but not for `think_recaption`.

## Safety constraints

- This sub-skill does not call DeepSeek, Tencent Cloud, model checkpoints, or repo launch scripts.
- Treat `PE/deepseek.py` as reference-only because it is credential and network bound.
- Treat `PE/system_prompt.py` as distilled guidance, not as a runnable dependency for the generated skill.
- Keep future guidance self-contained; do not require the original repository checkout to remain available.
