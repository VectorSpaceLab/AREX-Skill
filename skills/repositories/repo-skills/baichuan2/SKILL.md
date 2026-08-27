---
name: baichuan2
description: "Route Baichuan2 chat inference, deployment/quantization, and
  fine-tuning workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Baichuan2

Use this repo skill when a task is about Baichuan2 model selection, chat/base inference, local chat demos, OpenAI-compatible serving, quantized deployment, CPU deployment, checkpoint conversion, or supervised fine-tuning.

Baichuan2 is a model-family repository rather than an importable Python package. The operating guidance is therefore organized around public workflows and bundled helpers, not a package module tree.

## Start here

1. If the task may depend on repo freshness, read [`references/repo-provenance.md`](references/repo-provenance.md).
2. If the user has not chosen a checkpoint, read [`references/model-overview.md`](references/model-overview.md).
3. Prepare the smallest environment for the requested workflow using [`references/installation.md`](references/installation.md).
4. Run a no-weight dependency check before loading 7B/13B weights:

```bash
python scripts/check_baichuan2_env.py --workflow inference
python scripts/check_baichuan2_env.py --workflow all --require-cuda
```

Use `--workflow inference`, `deployment`, `fine-tuning`, or `all` to match the route. These checks do not download model weights.

## Route by user request

| User request signals | Read | Why |
| --- | --- | --- |
| `model.chat`, Python inference, Base-model generation, terminal demo, Streamlit web UI, OpenAI-compatible `/v1/chat/completions` | [`sub-skills/inference/SKILL.md`](sub-skills/inference/SKILL.md) | Owns Baichuan2 Chat/Base inference, CLI/web demos, and the Flask chat-completions helper. |
| 4-bit/8-bit quantization, BitsAndBytes, CPU-only loading, `load_in_8bit`, `quantize(4)`, `lm_head.weight`, Baichuan1 optimization migration | [`sub-skills/deployment/SKILL.md`](sub-skills/deployment/SKILL.md) | Owns memory-reduction, CPU deployment, and checkpoint-conversion workflows. |
| supervised fine-tuning, DeepSpeed, LoRA, `fine-tune.py`, hostfile, `W_pack`, `ds_config`, training data schema | [`sub-skills/fine-tuning/SKILL.md`](sub-skills/fine-tuning/SKILL.md) | Owns SFT data validation, ZeRO-3 launch planning, LoRA, and post-training loading. |
| installation/import/backend failure before a route is clear | [`references/troubleshooting.md`](references/troubleshooting.md) | Covers shared CUDA, dependency, model-access, and optional-extra problems. |
| license, commercial-use constraints, or citation | [`references/license-and-citation.md`](references/license-and-citation.md) | Distills the repo's license/citation section. |

## Core operating facts

- Released model ids include `baichuan-inc/Baichuan2-7B-Base`, `baichuan-inc/Baichuan2-7B-Chat`, `baichuan-inc/Baichuan2-13B-Base`, `baichuan-inc/Baichuan2-13B-Chat`, and published 4-bit Chat variants.
- Chat checkpoints expose `model.chat(tokenizer, messages)` through Hugging Face `trust_remote_code=True`. Base checkpoints use `model.generate(...)` instead.
- The repository demos are GPU-oriented by default. CPU loading is a separate float32 deployment branch and is expected to be slow.
- Quantization and training are CUDA-sensitive. Do not use a CPU import check as proof that those workflows work.
- The bundled scripts intentionally include `--help`, `--dry-run`, or validation modes so future agents can inspect plans without downloading large weights.

## Do not do this

- Do not tell the user to open or run original checkout scripts; use the bundled helpers and references in this skill.
- Do not force Base checkpoints through Chat-only CLI/web/API wrappers.
- Do not add `device_map="auto"` to online quantization; the deployment sub-skill explains why.
- Do not launch DeepSpeed training until the data validator and dry-run plan pass.
- Do not import this skill into live repo-skill storage unless a later verification/import workflow is explicitly approved. This construction run was requested as **not import**.
