# Training and Evaluation Troubleshooting

## Purpose

Read this when a train/eval run fails after the config and model family already look correct.

## Broken console script or wrapper import

### Symptom
- `ModuleNotFoundError: main_train`
- `cvnets-train` or `cvnets-eval` starts, then fails before argument parsing completes.

### Cause
- The installed console script cannot resolve the top-level module in the current environment.

### Recovery
- Use the bundled wrapper in this sub-skill with `--repo-root <repo-root>`.
- If you only need to inspect the parser, use `scripts/inspect_config.py` instead of launching a run.

## Distributed setup problems

### Symptom
- Rank, world-size, or backend warnings.
- Multi-GPU launches crash during spawn or device setup.

### Cause
- The DDP arguments do not match the visible GPUs or the requested backend.

### Recovery
- Match `CUDA_VISIBLE_DEVICES`, `--ddp.rank`, and `--ddp.world-size`.
- If you do not need distributed training, keep the visible GPU count at one or zero.
- Recheck the config's dataset-worker count if the run starves on input.

## Checkpoint and finetuning problems

### Symptom
- Resume fails, or finetuning loads a checkpoint but the head shape is wrong.
- `common.resume` or `common.finetune` points at a file that cannot be used for the current run.

### Cause
- The checkpoint was trained for a different class count, model family, or task head.

### Recovery
- Reconfirm the model family in `references/model-overview.md`.
- Use `common.resume` only for the same run shape.
- Use `common.finetune` for a fresh run and adjust the head or class count if needed.

## Data and class-count problems

### Symptom
- Dataset root errors, missing annotations, or class-count mismatches in detection/segmentation.

### Cause
- `dataset.root_*` or `model.<category>.n-classes` is wrong for the selected task.

### Recovery
- Fix the config with `scripts/inspect_config.py`.
- For detection and segmentation, verify the class count before rerunning evaluation.
- For evaluation-only runs, confirm that the right loader mode is being used.

## Precision and device problems

### Symptom
- Mixed-precision or CUDA assertions on a CPU-only run.
- The model is selected correctly but the run still fails in device setup.

### Cause
- A GPU-only flag or a CUDA-specific assumption leaked into a CPU smoke run.

### Recovery
- Disable mixed precision on CPU.
- Reduce the GPU count to zero or one for smoke testing.
- Verify that the model and dataset can both run in the chosen backend before scaling up.

## When to stop and switch

- If the problem is the wrong config key, switch to `data-and-config`.
- If the problem is model-family choice or registry naming, switch to `models-and-architectures`.
- If the problem is export or profiling, switch to `conversion-and-profiling`.
