---
name: unsloth
description: "Use Unsloth Core, CLI, Studio, and export workflows for fast LLM
  finetuning, local inference, Studio serving, and checkpoint conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Unsloth

Use this repo skill when a user asks about Unsloth, Unsloth Core, Unsloth Studio, the `unsloth` CLI, fast LoRA/QLoRA/full finetuning, GGUF or merged checkpoint export, local Studio/API serving, or connecting coding agents to an Unsloth Studio server.

## Route First

- Read `sub-skills/core-training/SKILL.md` for code-first Python workflows with `FastLanguageModel`, `FastModel`, `FastVisionModel`, LoRA/full finetuning, chat templates, raw-text/data checks, trainer setup, and backend/import troubleshooting.
- Read `sub-skills/cli-workflows/SKILL.md` for `unsloth train`, `inference`, `chat`, `export`, `list-checkpoints`, `studio`, `run`, `connect`, YAML/JSON config dry-runs, pass-through flags, and CLI parser troubleshooting.
- Read `sub-skills/model-export/SKILL.md` for adapter, merged, GGUF, Ollama, and Hub export planning, tokenizer/output preflight, `unsloth_save_model`, `save_to_gguf`, and export failures.
- Read `sub-skills/studio-runtime/SKILL.md` for Unsloth Studio install/launch/update, secure tunnel vs raw host binding, backend APIs, providers, RAG/data recipes, tool policy, GGUF/llama.cpp runtime, and coding-agent connection.

## Shared References

- Read `references/install-and-backends.md` before advising installation, optional extras, hardware backends, Core-vs-Studio choices, or safe import checks.
- Read `references/troubleshooting.md` for cross-cutting install/import, optional dependency, CUDA/MLX/ROCm, network/cache, token, and routing failures.
- Read `references/repo-provenance.md` when deciding whether this skill is stale relative to the source repository.
- `references/repo-routing-metadata.json` is structured metadata for DisCo import routing; future agents normally do not need to read it manually.

## Shared Script

- Run `scripts/check_unsloth_environment.py --help` to inspect installed package metadata, CLI availability, backend packages, and optional CUDA state without loading a model, downloading weights, starting Studio, or training.

## Start With The User's Interface

- If the user gives Python code, mentions `FastLanguageModel`, `get_peft_model`, `SFTTrainer`, `standardize_sharegpt`, or dataset formats, route to `core-training`.
- If the user gives shell commands, YAML/JSON configs, `unsloth train --dry-run`, `unsloth run`, `unsloth connect`, or parser errors, route to `cli-workflows`.
- If the user asks to save, merge, convert, quantize, upload, create GGUF, create an Ollama model, or list checkpoints, route to `model-export`.
- If the user mentions the web UI, local API server, browser launch, Cloudflare tunnel, API key, providers, RAG, tool execution, llama.cpp, GGUF serving, or agent connection to Studio, route to `studio-runtime`.

## Safe Defaults

- Prefer planning and preflight checks before model downloads, long training, export conversion, Studio setup, or networked provider calls.
- Import Unsloth before `transformers`, `trl`, or `peft` in Python training scripts so its patches apply early.
- Use `unsloth train --dry-run` for CLI training config validation before any real training run.
- Prefer `unsloth studio --secure` for remote access; treat `-H 0.0.0.0` as a raw network exposure that requires explicit risk acceptance.
- Keep tokens out of reusable files and logs; pass Hugging Face, W&B, Studio API, and provider credentials through environment variables or secure stores.
- Do not assume every optional acceleration package is installed. Check `torch`, `unsloth_zoo`, `bitsandbytes`, `xformers`, `flash-attn`, `triton`, `llama.cpp`, and Studio dependencies against the chosen workflow.

## What This Skill Does Not Cover

- It does not reproduce Unsloth benchmarks, run long finetuning jobs, download gated models, push to the Hub, start Studio servers, or mutate user installs without explicit user approval.
- It does not treat source repository tests, notebooks, examples, or install scripts as runtime dependencies; relevant behavior is distilled into bundled references and safe helper scripts.
- It does not replace official Unsloth docs for model catalogs or notebook links; use public docs for live model availability and this skill for repo-specific API/CLI/runtime behavior.
