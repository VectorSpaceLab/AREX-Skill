---
name: hunyuan-image-3-0
description: "Route HunyuanImage-3.0 local generation, prompt conditioning,
  package APIs, Gradio UI, and vLLM serving workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# HunyuanImage-3.0 Repo Skill

Use this skill for Tencent HunyuanImage-3.0 package and checkpoint workflows:
local text-to-image generation, instruction/image-to-image editing, prompt
conditioning, package APIs, Gradio UI diagnostics, and vLLM service payloads.

## Start here

- Read [install and environment](references/install-and-environment.md) before
  building a Python runtime or debugging imports.
- Read [hardware and models](references/hardware-and-models.md) before planning
  full image generation, GPU memory, CUDA, FlashInfer, or checkpoint selection.
- Read [troubleshooting](references/troubleshooting.md) for known snapshot
  failures: package metadata omissions, broken console script, stale Gradio
  imports, DeepSeek rewrite, CUDA/VRAM, and vLLM branch drift.
- Read [repo provenance](references/repo-provenance.md) when you need the
  source commit, package version, or freshness baseline for this snapshot.
- Run `scripts/check_hunyuan_image_environment.py` for a safe import/CUDA smoke
  that does not load checkpoints, call Tencent Cloud, open ports, or generate
  images.

## Route map

| If the user asks about... | Read |
|---|---|
| Public Python APIs, model/config/tokenizer/image-processor objects, scheduler/cache internals, lazy imports | [core APIs and architecture](sub-skills/core-apis-and-architecture/SKILL.md) |
| Local generation commands, checkpoint recipes, T2I/TI2I, instruct/distil runs, Taylor Cache, deterministic flags | [local inference CLI](sub-skills/local-inference-cli/SKILL.md) |
| System-prompt modes, `think_recaption`, `recaption`, multi-image conditioning, DeepSeek rewrite, text rendering | [prompt and image conditioning](sub-skills/prompt-and-image-conditioning/SKILL.md) |
| Gradio app launch, UI arguments, chat history, image uploads, or current app import breakage | [Gradio app and prompt UI](sub-skills/gradio-app-and-prompt-ui/SKILL.md) |
| vLLM server command, custom branch, OpenAI-style payloads, model alias, client/server diagnostics | [vLLM serving](sub-skills/vllm-serving/SKILL.md) |

## Fast decisions

- For repeatable local generation, use the skill-owned runner and dry-run
  helpers under `sub-skills/local-inference-cli/scripts/` before starting a GPU
  run.
- For HunyuanImage-3.0-Instruct or Instruct-Distil editing, prefer
  `bot_task="think_recaption"`, `use_system_prompt="en_unified"`, ordered
  image inputs, and `image_size="auto"` unless a fixed size is required.
- For base text-to-image, use rich manual prompts or an explicitly authorized
  DeepSeek rewrite branch; do not assume the base checkpoint self-rewrites.
- For actual generation, CUDA is required. CPU import checks are useful for API
  inspection but do not validate generation.
- For vLLM, a normal package install is not enough; the workflow needs the
  custom HunyuanImage-3.0 vLLM branch or the matching Docker path.
- For the Gradio UI in this snapshot, run the bundled diagnostics first; the
  source app launcher has stale imports and may need a patch or CLI fallback.

## Known snapshot constraints

- Distribution metadata is `hunyuan-image-3` version `3.0.0`, Python `>=3.12`.
- The generated environment smoke passed with PyTorch `2.8.0+cu128`, but full
  80B checkpoint generation was not run because it needs external weights and
  large multi-GPU memory.
- The package metadata can omit top-level helper modules in non-compat installs;
  always verify `hunyuan_image_3`, `utils`, `PE`, and `vllm_infer` importability
  when those workflows matter.
- The declared `hunyuan-image` console entry point calls `main()` incorrectly;
  use the bundled runner/dry-run helper or a patched source CLI instead.

## Non-goals

- This skill does not cover LoRA training, general Stable Diffusion tooling,
  unrelated Hunyuan models, or generic vLLM deployment not involving
  HunyuanImage-3.0 task support.
- This skill does not download model weights, call Tencent Cloud, build Docker
  images, start long-running services, or run full image generation by default.
