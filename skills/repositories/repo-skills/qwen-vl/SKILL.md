---
name: qwen-vl
description: "Route Qwen-VL multimodal inference, serving, finetuning, and
  official evaluation workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Qwen-VL

This generated repo skill is the router for Qwen-VL-family workflows. Start here when you are not yet sure whether the request is about direct inference, serving, finetuning, or evaluation. The detailed workflow notes live in the sub-skills and bundled references.

## Read first

- [Repository provenance](references/repo-provenance.md) to see the source snapshot, dirty-state note, and evidence paths used to build this skill.
- [Model and workflow overview](references/model-and-workflow-overview.md) for the model-family map and the fastest route to the right sub-skill.
- [Installation](references/installation.md) for the runtime package groups and a safe smoke check command.
- [Troubleshooting](references/troubleshooting.md) for cross-cutting install, dependency, and backend issues.
- [Runtime smoke helper](scripts/runtime_smoke.py) when you want a quick import or CUDA probe before launching a larger workflow.

## Route by intent

- Use [sub-skills/inference/SKILL.md](sub-skills/inference/SKILL.md) for direct chat, grounding, box rendering, generation, and quantization-aware loading.
- Use [sub-skills/serving/SKILL.md](sub-skills/serving/SKILL.md) for the Gradio demo or the OpenAI-compatible FastAPI service.
- Use [sub-skills/finetuning/SKILL.md](sub-skills/finetuning/SKILL.md) for full finetuning, LoRA, Q-LoRA, and conversation-data validation.
- Use [sub-skills/evaluation/SKILL.md](sub-skills/evaluation/SKILL.md) for captioning, VQA, grounding, ScienceQA, MMBench, SEED-Bench, MME reference notes, and TouchStone reference notes.

## What this skill covers

- Qwen-VL, Qwen-VL-Chat, and Qwen-VL-Chat-Int4 checkpoint selection.
- Multimodal prompts with one or more images and optional grounding markup.
- Local service launch planning without auto-starting listeners.
- Adapter training and checkpoint/adapter preparation.
- Official benchmark conversion, inference, scoring, and submission formatting.

## Operating notes

1. Use `trust_remote_code=True` unless you have an audited local copy of the custom model code.
2. Use `Qwen/Qwen-VL-Chat` for assistant-style chat and `Qwen/Qwen-VL` for base-model generation.
3. Use the bundled sub-skill scripts and references rather than depending on the original repository checkout.
4. Keep service launch, training, and benchmark execution separate unless the user explicitly asks for a multi-step workflow.
5. If a request mentions `box`, `grounding`, `ref`, or `quad`, start with inference; if it mentions `port`, `share`, or `OpenAI-compatible`, start with serving; if it mentions `LoRA`, `Q-LoRA`, or `DeepSpeed`, start with finetuning; if it mentions dataset names or benchmark outputs, start with evaluation.

## Quick start

- For a quick environment sanity check, run `python scripts/runtime_smoke.py --check-cuda`.
- For a quick command plan, open the sub-skill that matches the user request and then read the bundled reference linked there.
- For a small source-free orientation, use [references/model-and-workflow-overview.md](references/model-and-workflow-overview.md) before opening the deeper workflow docs.

## Not included here

- Long API tables, benchmark file layouts, and command catalogs live in the sub-skill references.
- Review artifacts, usability test cases, and verification notes live under `skills/tests/qwen-vl/`, not in this runtime skill.
