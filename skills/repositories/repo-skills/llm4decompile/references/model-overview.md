# Model Overview

This repository centers on several related model families. Future agents should match the model family to the workflow before choosing a script or benchmark.

## Direct Decompilation Family

These models generate C directly from assembly-style prompts.

| Model path | Typical use | Notes |
| --- | --- | --- |
| `LLM4Binary/llm4decompile-1.3b-v1.5` | small direct decompilation baseline | V1.5 prompt format uses `# This is the assembly code:` |
| `LLM4Binary/llm4decompile-6.7b-v1.5` | default V1.5 direct model in examples | GPU inference and evaluation scripts usually reference this family |
| `LLM4Binary/llm4decompile-1.3b-v2` | Ghidra-refinement family baseline | Uses pseudo-code input rather than raw assembly |
| `LLM4Binary/llm4decompile-6.7b-v2` | recommended V2 refinement model | Refines Ghidra pseudo-code into cleaner C |
| `LLM4Binary/llm4decompile-9b-v2` | larger V2 refinement model | Appears in repo results tables |
| `LLM4Binary/llm4decompile-22b-v2` | largest documented V2 model | Used for best reported refinement results |

## SK²Decompile Family

These models operate in a two-stage pipeline.

| Model path | Stage | Notes |
| --- | --- | --- |
| `LLM4Binary/sk2decompile-struct-6.7b` | structure recovery | Predicts normalized/obfuscated intermediate representations |
| `LLM4Binary/sk2decompile-ident-6.7` | identifier naming | Recovers human-readable identifiers from the normalized IR |

## Training Base Models

The training scripts use base checkpoints from external hubs.

| Model path | Use |
| --- | --- |
| `deepseek-ai/deepseek-coder-1.3b-base` | default base model in `train/finetune.py` |
| `deepseek-ai/deepseek-coder-6.7b-base` | ColossalAI training example |
| `01-ai/Yi-Coder-9B` | referenced in the repo changelog for a later fine-tuned variant |

## Prompt Format Signals

- Direct decompilation uses `# This is the assembly code:` followed by a prompt ending with `# What is the source code?`.
- The V2 Ghidra refinement examples use the same top-level prompt but feed normalized pseudo-code instead of raw assembly.
- SK²Decompile stage 1 uses `# This is the assembly code:` or `# This is the normalized code:` depending on the stage and data source.
- SK²Decompile stage 2 usually consumes the normalized output of stage 1 and then recovers names/structure.

## Model-Selection Guidance

- Choose a V1.5 model when the input is raw assembly and the workflow is direct decompilation.
- Choose a V2 model when the input comes from Ghidra pseudo-code.
- Choose the SK²Decompile pair when the workflow is explicitly two-stage or mentions skeleton/skin, GRPO, or BringUpBench.
- Use the smallest model that can truthfully support the requested workflow; the repo examples often use 1.3B or 6.7B checkpoints for reproducibility.
