---
name: "model-serving"
description: "Plan DeepAnalyze model download, vLLM serving, Docker GPU launch,
  quantization, and tokenizer extension."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# model-serving

Use this sub-skill for deployment planning around DeepAnalyze-8B and its model-adjacent setup.

## Use this when
- Choosing a public model source for a local checkpoint.
- Picking a vLLM launch recipe from GPU memory and desired context length.
- Deciding whether to enable FP8 KV cache.
- Planning Docker GPU startup for model serving.
- Planning quantization or tokenizer tag extension before training.
- Using a remote API-key based model service instead of local serving.

## Do not use this when
- The task is about API calls, files, or client code after the server exists → use `api-and-clients`.
- The task is about WebUI provider selection or frontend setup → use `interactive-frontends`.
- The task is about SFT, RL, or benchmark runs → use `training-and-evaluation`.

## Operating flow
1. Read `references/vllm-and-docker.md` for the deployment matrix and command shape.
2. Use `scripts/vllm_command_builder.py` to print a dry-run launch command from the GPU-memory target.
3. Use `references/model-customization.md` and `scripts/quantization_command_builder.py` for copy-safe quantization planning.
4. Use `scripts/token_tag_plan.py` before any training run that starts from DeepSeek-R1-0528-Qwen3-8B and needs the DeepAnalyze tag set.
5. Use `references/cloud-api-usage.md` for remote API-key access hygiene.
6. Use `references/troubleshooting.md` for Windows, VRAM, missing path, FP8, bitsandbytes, and font issues.

## Safety rules
- Default to dry-run command output; do not mutate a checkpoint unless the caller explicitly asks for that action.
- Never embed API keys in code, prompts, or image builds.
- Treat source scripts as evidence for planning, not as something to run automatically in this runtime skill.
- Keep any command templates self-contained and avoid linking out to source-repo documentation.
