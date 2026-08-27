---
name: moss
description: "Routes OpenMOSS/MOSS workflows for local LLM inference, model
  runtime checks, API or UI serving, and SFT data/fine-tuning preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MOSS repo skill

Use this skill for OpenMOSS/MOSS tasks involving the MOSS conversational language
model release: model/runtime readiness, local chat inference, FastAPI/Gradio or
Streamlit serving, and supervised fine-tuning data preparation. The generated
helpers are self-contained and dry-run by default; heavyweight checkpoint
loading, service launch, or training must be an explicit task decision.

## When to read

- The task names MOSS, OpenMOSS, `moss-moon-003`, MOSS tokenizer/model classes,
  INT4/INT8 MOSS checkpoints, MOSS prompt markers, or MOSS plugin transcripts.
- You need to choose a checkpoint precision or GPU plan for MOSS inference.
- You need to validate MOSS environment imports or CUDA availability without
  downloading model weights.
- You need a safe FastAPI request payload, serving plan, or UI deployment recipe.
- You need to validate MOSS SFT JSON/JSONL conversations or plan a DeepSpeed SFT
  launch.

## First decisions

1. **Workflow type** — route to a sub-skill below. Do not collapse serving,
   inference, and training data into one generic recipe.
2. **Checkpoint/runtime cost** — distinguish dry-run planning from real model
   execution. Full MOSS generation can download large Hugging Face checkpoints
   and allocate tens of GB of GPU memory.
3. **Precision and device** — FP16 supports model parallelism; INT4/INT8 are
   documented as single-GPU only.
4. **Data/license constraints** — code, model weights, and data have separate
   licenses. Check constraints before redistribution, external serving, or
   commercial data use.

## Sub-skill routes

| Task | Read |
| --- | --- |
| Import/check `MossConfig`, `MossTokenizer`, `MossForCausalLM`; inspect model defaults; reason about quantization, CUDA, Triton, checkpoint families, memory. | [sub-skills/model-runtime/SKILL.md](sub-skills/model-runtime/SKILL.md) |
| Build MOSS prompts, plan chat generation, validate model/GPU choices, use a dry-run-first generation template, or reason about optional Jittor generation. | [sub-skills/inference/SKILL.md](sub-skills/inference/SKILL.md) |
| Build API request payloads, plan FastAPI/Gradio/Streamlit service launch, handle `uid` history and UI parameters, debug service startup. | [sub-skills/serving/SKILL.md](sub-skills/serving/SKILL.md) |
| Validate MOSS SFT records, plugin/no-plugin transcripts, no-loss spans, Accelerate/DeepSpeed config, and fine-tuning command plans. | [sub-skills/fine-tuning-data/SKILL.md](sub-skills/fine-tuning-data/SKILL.md) |

## Shared references

- [references/repo-provenance.md](references/repo-provenance.md) — source commit
  and evidence baseline; read before deciding whether this skill is stale.
- [references/install-and-dependencies.md](references/install-and-dependencies.md)
  — Python/dependency, CUDA, optional UI/training/Jittor guidance.
- [references/model-overview.md](references/model-overview.md) — checkpoint
  catalog, memory table, backend and license constraints.
- [references/prompt-format.md](references/prompt-format.md) — canonical MOSS
  meta instruction, turn markers, plugin sections, and tool APIs.
- [references/api-reference.md](references/api-reference.md) — verified public
  class/function signatures and runtime facts.
- [references/cli-reference.md](references/cli-reference.md) — bundled helper
  commands and safe-versus-heavy execution notes.
- [references/serving-and-ui.md](references/serving-and-ui.md) — API/UI request,
  response, and state behavior.
- [references/fine-tuning-data.md](references/fine-tuning-data.md) — SFT data
  schema and training-plan summary.
- [references/troubleshooting.md](references/troubleshooting.md) — cross-cutting
  install, checkpoint, CUDA, service, and data failures.

## Shared safe helper

Run [scripts/check_moss_env.py](scripts/check_moss_env.py) to check imports and
optional CUDA availability without loading MOSS checkpoints:

```bash
python path/to/moss/scripts/check_moss_env.py --repo-root /path/to/MOSS --json
python path/to/moss/scripts/check_moss_env.py --repo-root /path/to/MOSS --require-cuda --json
```

The `--repo-root` argument is supplied by the user for their own checkout. Do not
hard-code the checkout that was used to create this skill.

## Non-negotiable operating constraints

- Do not claim full MOSS inference, serving, or fine-tuning works unless that
  heavyweight path was actually run in the target environment.
- Do not use a CPU import check as proof of CUDA generation, quantized Triton
  kernels, or multi-GPU training.
- Do not recommend model parallelism for quantized INT4/INT8 MOSS checkpoints.
- Do not tell a future agent to rely on original repository scripts; use the
  bundled helpers and references in this generated skill tree.
- Keep model downloads, public network exposure, training writes, and license
  implications explicit before executing.
