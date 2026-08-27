---
name: internlm-xcomposer
description: "Guides InternLM-XComposer multimodal inference, composition,
  fine-tuning, reward-model, OmniLive, evaluation, and related-project
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# InternLM-XComposer

Use this repo skill when a user asks about the InternLM-XComposer family of model workflows: legacy 1.0/2.0 chat and evaluation, current 2.5 chat/composition and LMDeploy 4-bit paths, supervised fine-tuning, reward-model training and scoring, OmniLive audio/video/memory services, or related benchmark/project workflows.

This repository is a model/workflow collection rather than a single importable root package. Install only the dependencies needed for the selected route, then follow the nearest sub-skill plus its bundled references/scripts. Several repaired routes also include source-derived runnable bundles under `sub-skills/*/entrypoints/`; use those for approved execution instead of depending on the original checkout.

## Route map

- `model-inference` — Transformers chat/composition, multi-GPU dispatch, 4-bit/LMDeploy, Gradio, and legacy inference compatibility.
- `finetuning` — supervised fine-tuning, LoRA, adapter merge, and data-manifest validation.
- `reward-model` — reward scoring/comparison/ranking, preference data, and reward training/evaluation.
- `omnilive` — audio, video-memory, SRS/FastAPI/Gradio deployment planning, and OmniLive benchmarks.
- `evaluation-and-projects` — benchmark planning plus ShareGPT4V and DualFocus package/evaluation routing.

## Install guidance

There is no single root editable install. Use the workflow-specific dependencies for the sub-skill you are following:

- Base XComposer 2.5 inference: `torch`, `transformers`, `timm`, `sentencepiece`, `gradio`, `markdown2`, `xlsxwriter`, `einops`.
- Multi-GPU dispatch: add `accelerate`.
- 4-bit / LMDeploy: add `lmdeploy` and a CUDA-compatible wheel.
- Fine-tuning: add `deepspeed` and `peft`; some setups also need `flash-attn`.
- Reward-model training/evaluation: add `peft`, `deepspeed`, `pandas`, `pyarrow`, and the benchmark-specific data tools if you are actually running the benchmark.
- OmniLive audio/video: add `swift`, `decord`, `fastapi`, `gradio`, and the model/runtime pieces named in the OmniLive references.
- Related project packages: install from their own `pyproject.toml` directories when you choose the `evaluation-and-projects` route.

A safe generic check after installing a chosen workflow is:

```bash
python scripts/check_environment.py --modules torch,transformers
```

If you are using `projects/ShareGPT4V` or `projects/DualFocus`, read their sub-skill references for the package-specific install commands before creating or mutating an environment.

## What to read first

- Read `references/overview.md` for the model-family and route summary.
- Read `references/installation.md` for workflow-specific dependency guidance.
- Read `references/troubleshooting.md` when imports, CUDA, `trust_remote_code`, or data/layout issues appear.
- Read `references/repo-provenance.md` before deciding whether this skill matches the current checkout or before refreshing it.

## Minimal usage pattern

1. Choose the sub-skill that matches the user request.
2. Install the dependencies that sub-skill needs.
3. Run the bundled helper scripts from that sub-skill when available.
4. If the task has explicit execution approval, prefer bundled `entrypoints/` wrappers over source checkout scripts for finetuning, reward training, Gradio, OmniLive merge, and OmniLive services.
5. Use the sub-skill references for command shapes, data formats, and troubleshooting.

## Notes

- Future agents should not depend on the original source checkout still existing.
- Runtime links should stay inside this skill tree.
- Heavy model downloads, benchmark runs, and long training jobs remain user-executed actions outside the static skill guidance.
