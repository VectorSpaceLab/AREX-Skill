---
name: llm4decompile
description: "Route requests for LLM4Decompile training, direct decompilation,
  Ghidra refinement, and SK²Decompile workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# LLM4Decompile

LLM4Decompile is a decompilation repo with four major user-facing workflow families:
training, direct inference/evaluation, Ghidra-assisted refinement, and the SK²Decompile two-phase pipeline.
Use this root skill as the router, then open the sub-skill that matches the task shape.

## Quick route map

- **Fine-tune or continue pretraining models** → [`sub-skills/training/SKILL.md`](sub-skills/training/SKILL.md)
- **Run assembly-to-C inference or benchmark scoring** → [`sub-skills/evaluation/SKILL.md`](sub-skills/evaluation/SKILL.md)
- **Use Ghidra to extract pseudo-code and refine it with a model** → [`sub-skills/ghidra-refine/SKILL.md`](sub-skills/ghidra-refine/SKILL.md)
- **Run the SK²Decompile skeleton/skin pipeline, RL helpers, or BringUpBench evaluation** → [`sub-skills/sk2decompile/SKILL.md`](sub-skills/sk2decompile/SKILL.md)

## Common signals

Use the workflow that matches the user's nouns and commands:

- `train`, `fine-tune`, `pretrain`, `DeepSpeed`, `ColossalAI`, `LLaMA-Factory`
- `vLLM`, `text-generation-inference`, `single GPU`, `HumanEval-Decompile`, `Decompile-Bench`, `ExeBench`
- `Ghidra`, `analyzeHeadless`, `pseudo-code`, `V2`, `refine`
- `SK²Decompile`, `skeleton`, `skin`, `GRPO`, `reward function`, `BringUpBench`

## Shared repository facts

- The repo is source-only; it does not declare a Python package in `pyproject.toml` or `setup.py`.
- GPU/CUDA is required for the model-training and model-inference paths.
- Java 17 and `clang-format` are required for the Ghidra and normalization workflows.
- GCC/binutils are required for dataset compilation and benchmark execution.
- Psychec/stack appears only in the SK²Decompile header-inference path.

Before editing or extending the skill tree, read:

- [`references/model-overview.md`](references/model-overview.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)
- [`references/repo-provenance.md`](references/repo-provenance.md)
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json)
- [`scripts/check-runtime.sh`](scripts/check-runtime.sh)

## How to use this skill

1. Identify the workflow family.
2. Open the matching sub-skill.
3. Use the bundled references for command templates, data schemas, and troubleshooting.
4. Prefer the bundled scripts over source-checkout paths when giving future instructions.

## What not to do

- Do not route training questions into the benchmark or Ghidra routes.
- Do not route benchmark questions into the training route.
- Do not route SK²Decompile questions into the direct-evaluation route just because both use CUDA.
- Do not assume the old legacy benchmark examples are the primary path; treat them as historical context only.

## Shared helper

Run [`scripts/check-runtime.sh`](scripts/check-runtime.sh) when you need a quick environment sanity check for the common Python, CUDA, compiler, and Java prerequisites.
