# MOSS model overview

## Purpose

Read this when choosing a MOSS checkpoint, estimating hardware needs, or
explaining what the OpenMOSS/MOSS release contains. Use the sub-skill references
for executable prompt, serving, and fine-tuning details.

## Public model families

| Model id | Role | Operational notes |
| --- | --- | --- |
| `OpenMOSS-Team/moss-moon-003-base` | Base language model | Foundation checkpoint for downstream SFT. |
| `OpenMOSS-Team/moss-moon-003-sft` | Chat SFT model | Main local chat/inference checkpoint; can use FP16 model parallelism. |
| `OpenMOSS-Team/moss-moon-003-sft-plugin` | Plugin-augmented SFT model | Trained with tool-use transcripts for search, calculator, equation solver, and text-to-image commands. |
| `OpenMOSS-Team/moss-moon-003-sft-int4` | 4-bit quantized chat model | Lower memory; single-GPU only in documented demos. |
| `OpenMOSS-Team/moss-moon-003-sft-int8` | 8-bit quantized chat model | Lower memory than FP16; single-GPU only in documented demos. |
| `OpenMOSS-Team/moss-moon-003-sft-plugin-int4` / `*-int8` | Quantized plugin variants | Use only when plugin-trained behavior and single-GPU quantized runtime are in scope. |

The README also names preference-model/final-model checkpoints planned for
release. Do not claim those are available unless the target environment confirms
their current status.

## Memory table

For batch size 1, the public documentation estimates:

| Precision | Load model | Complete one-turn dialogue | Reach max 2048 context |
| --- | ---: | ---: | ---: |
| FP16 | 31 GB | 42 GB | 81 GB |
| INT8 | 16 GB | 24 GB | 46 GB |
| INT4 | 7.8 GB | 12 GB | 26 GB |

Use these as planning estimates, not guarantees. Real usage varies with prompt
length, history length, generation length, CUDA allocator state, and service
worker count.

## Backend and checkpoint rules

- FP16 `moss-moon-003-sft` is the route for multi-GPU model parallelism.
- INT4/INT8 checkpoints are documented as not supporting model parallelism.
- Quantized inference uses GPTQ/Triton-style kernels and is Linux/WSL-oriented.
- Full generation or serving requires checkpoint files and substantial GPU
  memory; safe helpers in this skill dry-run by default.
- Plugin transcripts format tool commands but do not provide live tool services.

## Data and licensing summary

MOSS separates code, model, and data licenses. The repo includes an Apache-2.0
code license, a separate model license, a separate data license, and user
agreement PDFs in source evidence. Before redistributing weights, serving a
public endpoint, or reusing SFT data commercially, check the exact license terms
for the artifact being used.

## Related routes

- Runtime classes and quantization internals:
  [../sub-skills/model-runtime/SKILL.md](../sub-skills/model-runtime/SKILL.md)
- Chat and command planning:
  [../sub-skills/inference/SKILL.md](../sub-skills/inference/SKILL.md)
- API/UI deployment:
  [../sub-skills/serving/SKILL.md](../sub-skills/serving/SKILL.md)
- SFT data and training:
  [../sub-skills/fine-tuning-data/SKILL.md](../sub-skills/fine-tuning-data/SKILL.md)
