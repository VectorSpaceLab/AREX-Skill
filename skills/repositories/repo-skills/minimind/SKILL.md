---
name: minimind
description: "Routes MiniMind LLM architecture, tokenizer, training, inference,
  serving, model conversion, RLHF, RLAIF, and Agentic RL workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MiniMind Repo Skill

Use this skill for MiniMind tasks: training a tiny language model from scratch, validating MiniMind JSONL data, using the MiniMind tokenizer/chat template, running inference, serving an OpenAI-compatible local API, converting artifacts for third-party engines, or planning DPO/PPO/GRPO/CISPO/Agentic RL post-training.

MiniMind is an educational and practical PyTorch LLM codebase for small Dense and MoE decoder-only models aligned with Qwen3/Qwen3-MoE conventions. It includes custom tokenizer assets, pretrain/SFT/LoRA/RL training entrypoints, tool-call and thinking chat-template support, OpenAI-compatible serving helpers, and conversion workflows.

## Before you choose a route

1. Identify whether the user is working with **data**, **raw PyTorch weights**, **Transformers-format model directories**, **training scripts**, **post-training objectives**, or **serving/API clients**.
2. Check whether real model weights, datasets, reward-model checkpoints, or external serving engines already exist locally. This skill does not assume downloads are available.
3. Treat CUDA as the practical backend for real training and meaningful generation. CPU is useful for imports, validators, parser checks, and tiny random-tensor smokes.
4. Use bundled validators and smoke helpers before long training, server, conversion, or RL runs.

## Sub-skill routes

- [training-basics](sub-skills/training-basics/SKILL.md): use for tokenizer compatibility, pretrain JSONL, SFT/LoRA conversation JSONL, `MiniMindConfig`, core pretraining, full SFT, LoRA training, checkpoint resume, DDP, output weight naming, and tiny model smokes.
- [inference-serving](sub-skills/inference-serving/SKILL.md): use for local generation, raw `.pth` versus Transformers artifact decisions, LoRA inference/merge/export, OpenAI-compatible `/v1/chat/completions`, Streamlit-style UI behavior, tool-call parsing, thinking output, model conversion, and vLLM/llama.cpp/Ollama-style serving.
- [rlhf-agentic](sub-skills/rlhf-agentic/SKILL.md): use for white-box distillation, DPO, PPO, GRPO/CISPO, Agentic RL, RLAIF/Agentic JSONL schemas, reward models, rollout engines, SGLang planning, tool-use rewards, and post-training weight handoff.

## Shared references and helper

- Read [references/package-overview.md](references/package-overview.md) for the repository capability map, artifact naming, dependencies, and evidence-backed workflow summary.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/backend/data/artifact triage before drilling into a sub-skill's troubleshooting page.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is stale for a checkout.
- Run [scripts/check_minimind_environment.py](scripts/check_minimind_environment.py) to inspect core dependency availability, CUDA, Qwen3 class support, and optional MiniMind source-module imports without loading large weights.

## Minimal public setup checks

For a general MiniMind Python environment, install dependencies from the repository's requirement list and a backend-appropriate PyTorch build. The requirement list intentionally leaves `torch` commented because the right wheel depends on CPU/CUDA/ROCm and host drivers. The OpenAI-compatible server additionally needs `fastapi` and `uvicorn`.

After installation, run a lightweight dependency/backend check:

```bash
python scripts/check_minimind_environment.py --check-qwen3 --check-cuda
```

If you are working inside a local MiniMind checkout or an unpacked source tree and want module import checks, pass that tree explicitly:

```bash
python scripts/check_minimind_environment.py --module-root MINIMIND_SOURCE_TREE --check-modules
```

Do not treat this import check as proof that a long training job, model download, reward-model load, or third-party serving engine will work. Route to the relevant sub-skill for the workflow-specific validation.

## Common route decisions

| User goal | Route | First safe action |
| --- | --- | --- |
| Validate `pretrain_t2t_mini.jsonl`, `sft_t2t_mini.jsonl`, or custom LoRA data | `training-basics` | Run the bundled JSONL validator for the expected schema. |
| Start or resume pretraining/SFT/LoRA | `training-basics` | Validate data, run a tiny smoke, confirm input/output weight prefixes and backend. |
| Chat with a trained MiniMind model | `inference-serving` | Classify the artifact as raw `.pth` or Transformers format. |
| Serve MiniMind behind an OpenAI-compatible endpoint | `inference-serving` | Prefer a Transformers directory, check API dependencies, then probe one request. |
| Debug `<tool_call>` or `<think>` parsing | `inference-serving` | Run the bundled tool-call smoke helper on representative text. |
| Convert raw weights for vLLM, llama.cpp, or Ollama | `inference-serving` | Validate artifacts and plan raw-to-Transformers or Qwen3-compatible export first. |
| Run DPO, PPO, GRPO/CISPO, or Agentic RL | `rlhf-agentic` | Validate post-training JSONL schema and external reward/teacher/checkpoint prerequisites. |
| Use optional SGLang rollout for RL | `rlhf-agentic` | Confirm the local SGLang service, logprob support, update endpoint, and dedicated shared checkpoint path; otherwise use torch rollout. |

## Backend and dependency notes

- CUDA is a required practical backend for the selected training/inference capability surface; tiny CPU checks only validate plumbing.
- The native evidence supports dense and MoE MiniMind configs; checkpoint names add `_moe` for MoE variants.
- MiniMind tokenizer behavior depends on `tokenizer_config.json` with chat-template support for roles, `<think>`, `<tool_call>`, and `<tool_response>`.
- FastAPI/Uvicorn are serving dependencies; Streamlit is a UI dependency; SGLang/vLLM/llama.cpp/Ollama are optional external engines and are not part of the minimum environment.

## Freshness check

Before applying this skill to a changed MiniMind checkout, read [references/repo-provenance.md](references/repo-provenance.md). If the commit, dirty state, tokenizer/model files, training scripts, or public workflow docs differ materially from the recorded snapshot, refresh this repo skill instead of assuming the old guidance is current.
