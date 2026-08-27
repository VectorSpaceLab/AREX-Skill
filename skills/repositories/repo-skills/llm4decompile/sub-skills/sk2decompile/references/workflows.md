# SK²Decompile Workflows

This sub-skill covers the full SK²Decompile pipeline: preprocessing, supervised fine-tuning, RL reward helpers, two-stage inference, and BringUpBench evaluation.

## Route Summary

Use this route when the user wants to:

- normalize pseudo-code into the skeleton representation,
- build function maps that join source, pseudo-code, and assembly,
- prepare or inspect RL reward data,
- run the two-phase inference pipeline,
- evaluate the results on BringUpBench.

## Main workflow stages

### 1. Preprocess pseudo-code and source code

Use the normalization helpers to convert pseudo-code into a clang-formatted, placeholder-preserving form.

Key scripts:

- `scripts/normalize_pseudo.py`
- `scripts/infer_type.py`

### 2. Build function maps

Create a JSONL record that joins source, pseudo-code, normalized pseudo-code, and assembly for each function.

Key scripts:

- `scripts/build_func_maps.py`
- `scripts/disasm_all_objdump.sh` (or equivalent helper)

### 3. Train the two phases

- **Stage 1 / skeleton**: supervised fine-tuning or RL for structure recovery.
- **Stage 2 / skin**: supervised fine-tuning or RL for identifier naming.

Key scripts:

- `scripts/run_struct_rl.sh`
- `scripts/run_ident_rl.sh`
- `scripts/train_pseudo2norm.yaml` / `scripts/train_norm2code.yaml` equivalents when needed

### 4. Run two-stage inference

The inference helper first predicts normalized structure, then feeds that result into the recovery model.

Key script:

- `scripts/sk2decompile_inf.py`

### 5. Evaluate on BringUpBench

Use the generated function maps or inference outputs to rebuild benchmark workspaces and measure replacement, compile, and execution rates.

Key script:

- `scripts/eval_infer_out.py`

## Decision points

- Use the preprocessing route when the user is preparing training or benchmark inputs.
- Use the RL route when the user explicitly mentions GRPO, reward functions, or the paper's post-training stage.
- Use the inference route when the user wants to recover a function end-to-end from the skeleton/skin pair.
- Use the BringUpBench route when the user wants per-function replacement and build/test scores.

## Read Next

- [`data-formats.md`](data-formats.md)
- [`reward-functions.md`](reward-functions.md)
- [`bringupbench.md`](bringupbench.md)
- [`troubleshooting.md`](troubleshooting.md)
- [`../../../references/model-overview.md`](../../../references/model-overview.md)
