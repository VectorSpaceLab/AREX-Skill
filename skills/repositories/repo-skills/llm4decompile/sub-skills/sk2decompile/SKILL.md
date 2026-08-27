---
name: sk2decompile
description: "Run the SK²Decompile two-phase skeleton/skin pipeline, RL helpers,
  and BringUpBench evaluation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# SK²Decompile

Use this sub-skill when the user wants the repo's two-phase binary-decompilation workflow: structure recovery, identifier naming, RL reward helpers, two-stage inference, or BringUpBench evaluation.

## Covers

- pseudo-code normalization and obfuscation helpers
- header/type inference for structure-recovery training data
- function-map generation across source, pseudo-code, and assembly
- two-stage skeleton/skin inference
- GRPO / RL helper scripts and reward modules
- BringUpBench evaluation and report generation

## Excludes

- direct LLM4Decompile training and inference → use `training` or `evaluation`
- Ghidra-only refinement flow → use `ghidra-refine`
- plain benchmark scoring without the two-stage pipeline → use `evaluation`

## Start Here

1. Read [`references/workflows.md`](references/workflows.md) for the stage map.
2. Read [`references/data-formats.md`](references/data-formats.md) before changing JSONL/Parquet layouts.
3. Read [`references/reward-functions.md`](references/reward-functions.md) if the user asks about RL rewards.
4. Read [`references/bringupbench.md`](references/bringupbench.md) when the task touches the benchmark pipeline.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) if normalization, reward services, or benchmark checkout paths fail.

## Common routes

### Preprocessing / normalization

Use this route when the user wants to normalize pseudo-code, build function maps, or infer headers for RL data.

Good entry points:

- `scripts/normalize_pseudo.py`
- `scripts/infer_type.py`
- `scripts/build_func_maps.py`
- `scripts/disasm_all_objdump.sh`

### Two-stage inference

Use this route when the user wants to run the structure-recovery model and then the identifier-naming model.

Good entry points:

- `scripts/sk2decompile_inf.py`

### RL reward helpers

Use this route when the user wants to inspect, adapt, or debug the reward modules used by VERL / GRPO.

Good entry points:

- `scripts/reward_functions/exe_type.py`
- `scripts/reward_functions/sim_exe.py`
- `scripts/reward_functions/embedding_gte.py`
- `scripts/reward_functions/embedding_qwen3.py`
- `scripts/run_struct_rl.sh`
- `scripts/run_ident_rl.sh`

### BringUpBench evaluation

Use this route when the user wants to rebuild a benchmark workspace and score replacement / compile / execution rates.

Good entry points:

- `scripts/eval_infer_out.py`

## Environment signals

- `clang-format` is required for normalization.
- `vllm` / `torch` CUDA is required for the stage models.
- Psychec is optional but needed for header inference.
- BringUpBench uses its own checkout; set `BENCH_REPO_ROOT` before evaluation.

## When to read the bundled references

- Use the workflow reference for stage ordering and script ownership.
- Use the data-format reference to validate the JSONL/Parquet schemas.
- Use the reward reference to distinguish structure-recovery and identifier-naming signals.
- Use the BringUpBench reference to understand the benchmark-side file layout and environment variables.
