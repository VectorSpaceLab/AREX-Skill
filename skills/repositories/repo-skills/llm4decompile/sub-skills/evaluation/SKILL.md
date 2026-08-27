---
name: evaluation
description: "Run direct decompilation inference and benchmark scoring for
  LLM4Decompile outputs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Evaluation

Use this sub-skill when the user wants to generate C from assembly or pseudo-code, run benchmark scoring, or compare model outputs against the repo's direct-evaluation datasets.

## Covers

- vLLM-based direct inference and scoring
- text-generation-inference / server-backed inference paths
- benchmark metrics such as executable rate, compile rate, and edit similarity
- direct benchmark families such as HumanEval-Decompile, MBPP, and Decompile-Bench
- legacy single-GPU evaluation only as a reference path

## Excludes

- training or dataset preparation → use `training`
- Ghidra pseudo-code extraction or refinement → use `ghidra-refine`
- SK²Decompile preprocessing, RL, and BringUpBench evaluation → use `sk2decompile`

## Start Here

1. Read [`references/evaluation-workflows.md`](references/evaluation-workflows.md) for the route map.
2. Read [`references/data-formats.md`](references/data-formats.md) before editing dataset or output paths.
3. Read [`references/benchmark-catalog.md`](references/benchmark-catalog.md) to match the benchmark family.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) if the model, server, or metrics fail.

## Common routes

### Direct vLLM evaluation

Use this route when the user wants the repo's recommended GPU inference path or a quick benchmark run.

Good entry points:

- `scripts/run_vllm_eval.py`
- `scripts/run_exe_rate.py`

### Server-backed evaluation

Use this route when the user prefers a text-generation server or needs the repo's TGI-like pattern.

Good entry points:

- `scripts/run_tgi_eval.py`
- `scripts/text_generation.py`

### Metrics only

Use this route when predictions already exist and the user only wants compile/run or edit-similarity scoring.

Good entry points:

- `scripts/calc_execute_rate.py`
- `scripts/calc_edit_similarity.py`

## Prompt and output signals

- The direct prompt shape is `# This is the assembly code:` followed by the candidate body and `# What is the source code?`.
- The v2/Ghidra prompt shape belongs to `ghidra-refine`, not this sub-skill.
- Output directories are usually grouped by optimization level, so the file layout matters as much as the content.

## When to read the bundled references

- Use the benchmark catalog to identify which dataset the user actually named.
- Use the data-format reference to validate JSON fields and output layout.
- Use the troubleshooting reference when the model path, GPU memory, or compiler tools are the problem.
